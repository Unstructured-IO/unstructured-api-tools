import json
import os
import pytest

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
            "First parameter must be named text and not have a default value",
        ),
        ("def pipeline_api(bad_arg,text): pass", "First parameter must be named text"),
        ("def pipeline_api(text, m_var): pass", "Default argument for m_var must be empty list"),
    ],
)
def test_infer_params_catches_bad_args(api_definition, error_match):
    """Make sure we are catching bad args."""

    with pytest.raises(ValueError, match=error_match):
        convert._infer_params_from_pipeline_api(api_definition)


def test_infer_m_params():
    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[]):
        pass
        """
        )
        == ["var"]
    )
    assert (
        convert._infer_params_from_pipeline_api(
            """def pipeline_api(text, m_var=[], m_var2=[]):
        pass
        """
        )
        == ["var", "var2"]
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


def test_validate_raises_with_bad_filename():
    with pytest.raises(ValueError):
        convert._validate_notebook_filename("crocodile.ipynb")


def test_get_api_name():
    assert convert.get_api_name("pipeline-dummy-api.ipynb") == "dummy_api"
