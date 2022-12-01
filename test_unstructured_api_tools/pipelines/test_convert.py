import json
import os
import pytest
import re

from nbformat import NotebookNode

import unstructured_api_tools.pipelines.convert as convert


@pytest.fixture
def sample_notebook():
    return NotebookNode(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "id": "768fa8c6",
                    "metadata": {},
                    "outputs": [],
                    "source": "# pipeline-api\nimport random",  # noqa: E501
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "id": "64f6386b",
                    "metadata": {},
                    "outputs": [],
                    "source": "def function_not_to_include():\n    pass",
                },
                {
                    "cell_type": "markdown",
                    "id": "45988caf",
                    "metadata": {},
                    "source": "# pipeline-api",
                },
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "id": "c8e0cad6",
                    "metadata": {},
                    "outputs": [],
                    "source": "# pipeline-api\ndef pipeline_api(text: str):\n    sec_document = 'not a real document'\n    risk_narrative = sec_document[0:5]\n    return risk_narrative",  # noqa: E501
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3 (ipykernel)",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {
                    "codemirror_mode": {"name": "ipython", "version": 3},
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.8.13",
                },
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )


def test_generate_pipeline_api(sample_notebook, tmpdir):
    filename = os.path.join(tmpdir.dirname, "pipeline-test-notebook.ipynb")
    with open(filename, "w") as f:
        json.dump(sample_notebook, f, indent=4)

    # NOTE(robinson) - Just a smoke test for now
    convert.generate_pipeline_api(filename, pipeline_family="sec_filings", semver="2.0.1")


def test_read_notebook(sample_notebook, tmpdir):
    filename = os.path.join(tmpdir.dirname, "pipeline-test-notebook.ipynb")
    with open(filename, "w") as f:
        json.dump(sample_notebook, f, indent=4)

    notebook = convert.read_notebook(filename)
    assert notebook == sample_notebook


def test_get_api_cells(sample_notebook):
    api_notebook = convert.get_pipeline_api_cells(sample_notebook)
    assert api_notebook["cells"] == [
        {
            "cell_type": "code",
            "execution_count": 1,
            "id": "768fa8c6",
            "metadata": {},
            "outputs": [],
            "source": "# pipeline-api\nimport random",  # noqa: E501
        },
        {
            "cell_type": "code",
            "execution_count": 2,
            "id": "c8e0cad6",
            "metadata": {},
            "outputs": [],
            "source": "# pipeline-api\ndef pipeline_api(text: str):\n    sec_document = 'not a real document'\n    risk_narrative = sec_document[0:5]\n    return risk_narrative",  # noqa: E501
        },
    ]


def tests_notebook_to_script(sample_notebook):
    script = convert.notebook_to_script(sample_notebook)
    script_start = "import random\n\n"

    assert script.startswith(script_start)

    script_end = """def pipeline_api(text: str):
    sec_document = 'not a real document'
    risk_narrative = sec_document[0:5]
    return risk_narrative"""
    assert script.endswith(script_end)


@pytest.mark.parametrize(
    "api_definition,error_match",
    [
        ("def pipeline_api(): pass", "pipeline_api must have at least one parameter named text"),
        (
            "def pipeline_api(text=[]): pass",
            "First parameter must be named either text or file and not have a default value",
        ),
        (
            "def pipeline_api(bad_arg,text): pass",
            re.escape("The first parameter(s) must be named either text or file."),
        ),
        ("def pipeline_api(text, m_var): pass", "Default argument for m_var must be empty list"),
        (
            "def pipeline_api(text, response_type, m_var=[], m_var2=[]): pass",
            "Default argument type for response_type must be one of: <class 'str'>",
        ),
        (
            "def pipeline_api(text, response_schema=None, m_var=[], m_var2=[]): pass",
            "Default argument type for response_schema must be one of: <class 'str'>",
        ),
        (
            "def pipeline_api(text, m_var=[], m_var2=[], var3=[]): pass",
            "Unsupported parameter name var3, must either be text, file, response_type,"
            " response_schema, or begin with m_",
        ),
        (
            "def pipeline_api(text, m_var=[], file=None, m_var2=[], var3=[]): pass",
            "The parameters text or file must be specified before any keyword parameters.",
        ),
    ],
)
def test_infer_params_catches_bad_args(api_definition, error_match):
    """Make sure we are catching bad args."""

    with pytest.raises(ValueError, match=error_match):
        convert._infer_params_from_pipeline_api(api_definition)


@pytest.mark.parametrize(
    "api_definition,warning_message,raises_exc",
    [
        ("def pipeline_api(text): pass", None, False),
        (
            "def pipeline_api(text): pass\ndef pipeline_api(text): pass",
            "Function pipeline_api was redefined in the pipeline API definition.",
            False,
        ),
        (
            "def bad_function(text): pass",
            "Function pipeline_api was not defined in the pipeline API definition.",
            True,
        ),
    ],
)
def test_infer_params_logs_warnings(api_definition, warning_message, raises_exc, caplog):
    """Make sure warnings are logged when pipeline_api does not exist or is redefined."""

    if raises_exc:
        with pytest.raises(Exception):
            convert._infer_params_from_pipeline_api(api_definition)
    else:
        convert._infer_params_from_pipeline_api(api_definition)

    if warning_message is None:
        assert len(caplog.records) == 0
    else:
        assert caplog.records[0].msg == warning_message
        assert caplog.records[0].levelname == "WARNING"


def test_infer_m_params():
    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[]):
        pass
        """
        )
        == {
            "accepts_text": True,
            "accepts_file": False,
            "multi_string_param_names": ["var"],
            "optional_param_value_map": {},
        }
    )
    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[], m_var2=[]):
        pass
        """
        )
        == {
            "accepts_text": True,
            "accepts_file": False,
            "multi_string_param_names": ["var", "var2"],
            "optional_param_value_map": {},
        }
    )
    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[], m_var2=[], response_type="text/csv"):
        pass
        """
        )
        == {
            "accepts_text": True,
            "accepts_file": False,
            "multi_string_param_names": ["var", "var2"],
            "optional_param_value_map": {"response_type": "text/csv"},
        }
    )

    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[], m_var2=[], response_schema="label_studio"):
        pass
        """
        )
        == {
            "accepts_text": True,
            "accepts_file": False,
            "multi_string_param_names": ["var", "var2"],
            "optional_param_value_map": {"response_schema": "label_studio"},
        }
    )

    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(file, m_var=[], m_var2=[], response_type="text/csv",
                                 file_content_type=None):
        pass
        """
        )
        == {
            "accepts_text": False,
            "accepts_file": True,
            "multi_string_param_names": ["var", "var2"],
            "optional_param_value_map": {"response_type": "text/csv", "file_content_type": None},
        }
    )

    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(file, text, m_var2=[], response_type="application/json",
                                 filename=None):
        pass
        """
        )
        == {
            "accepts_text": True,
            "accepts_file": True,
            "multi_string_param_names": ["var2"],
            "optional_param_value_map": {"response_type": "application/json", "filename": None},
        }
    )


def test_notebook_file_to_script(sample_notebook, tmpdir):
    input_filename = os.path.join(tmpdir.dirname, "pipeline-this-is-a-test.ipynb")
    with open(input_filename, "w") as f:
        json.dump(sample_notebook, f, indent=4)

    convert.notebook_file_to_script(
        input_filename,
        output_directory=tmpdir.dirname,
        pipeline_family="test-family",
        semver="0.2.1",
    )

    output_filename = os.path.join(tmpdir.dirname, "this_is_a_test.py")
    with open(output_filename, "r") as f:
        script = f.read()

    assert "THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS." in script
    assert "fastapi" in script
    assert "slowapi" in script
    assert "pipeline_api" in script


def test_convert_notebook_files_to_api(sample_notebook, tmpdir):
    notebook_filenames = []
    for i in range(5):
        filename = os.path.join(tmpdir.dirname, f"pipeline-test-notebook-{i}.ipynb")
        with open(filename, "w") as f:
            json.dump(sample_notebook, f, indent=4)
        notebook_filenames.append(filename)

    convert.convert_notebook_files_to_api(
        notebook_filenames,
        input_directory=tmpdir.dirname,
        output_directory=tmpdir.dirname,
        pipeline_family="test-family",
        semver="0.2.1",
    )

    for i in range(5):
        output_filename = os.path.join(tmpdir.dirname, f"test_notebook_{i}.py")
        with open(output_filename, "r") as f:
            script = f.read()

        assert "THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS." in script
        assert "fastapi" in script
        assert "slowapi" in script
        assert "pipeline_api" in script

    with open(os.path.join(tmpdir.dirname, "app.py")) as f:
        script = f.read()

    assert "THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS." in script
    assert "fastapi" in script
    assert "slowapi" in script


@pytest.mark.parametrize(
    "bad_filename",
    [("crocodile.ipynb",), ("pipeline-app.ipynb",)],
)
def test_validate_raises_with_bad_filename(bad_filename):
    for bad_filename in bad_filename:
        with pytest.raises(ValueError):
            convert._validate_notebook_filename(bad_filename)


def test_get_api_name():
    assert convert.get_api_name("pipeline-dummy-api.ipynb") == "dummy_api"


def test_organize_imports():
    script = """def hello_word():
    pass

import numpy as np
from unstructured.cleaners.core import clean
from unstructured.cleaners.core import (
    clean_whitespace,
    replace_unicode_quotes,
)

def another_function():
    pass

import unstructured
"""
    reordered_script = convert._organize_imports(script)
    assert (
        reordered_script
        == """import numpy as np
from unstructured.cleaners.core import clean
from unstructured.cleaners.core import (
    clean_whitespace,
    replace_unicode_quotes,
)
import unstructured

def hello_word():
    pass


def another_function():
    pass

"""
    )


def test_get_multiline_import():
    lines = ["from unstructured import (", "func1,", "func2", ")", "", "def hello(): pass"]
    multiline_import, length = convert._get_multiline_import(lines)
    assert length == 4
    assert (
        multiline_import
        == """from unstructured import (
func1,
func2
)"""
    )


def test_get_multiline_import_raises_with_no_import():
    with pytest.raises(ValueError):
        convert._get_multiline_import(["def hello(): pass"])


def test_get_multiline_raises_with_no_parens():
    lines = ["from unstructured import func1", "func1,", "func2", ")", "", "def hello(): pass"]
    with pytest.raises(ValueError):
        convert._get_multiline_import(lines)
