import json
import os
import pytest

from click.testing import CliRunner
from nbformat import NotebookNode

import unstructured_api_tools.cli as cli


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


def test_convert_pipeline_notebooks(sample_notebook, tmpdir):
    for i in range(5):
        filename = os.path.join(tmpdir.dirname, f"pipeline-this-is-a-test-{i}.ipynb")
        with open(filename, "w") as f:
            json.dump(sample_notebook, f, indent=4)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "convert-pipeline-notebooks",
            "--input-directory",
            tmpdir.dirname,
            "--output-directory",
            tmpdir.dirname,
            "--pipeline-family",
            "fake-family-name",
            "--semver",
            "2.1.1",
        ],
    )
    assert result.exit_code == 0

    files = os.listdir(tmpdir.dirname)
    for i in range(5):
        assert f"this_is_a_test_{i}.py" in files


def test_convert_pipeline_notebooks_passing_flake8_ignore(sample_notebook, tmpdir):
    for i in range(5):
        filename = os.path.join(tmpdir.dirname, f"pipeline-this-is-a-test-{i}.ipynb")
        with open(filename, "w") as f:
            json.dump(sample_notebook, f, indent=4)

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "convert-pipeline-notebooks",
            "--input-directory",
            tmpdir.dirname,
            "--output-directory",
            tmpdir.dirname,
            "--pipeline-family",
            "fake-family-name",
            "--semver",
            "2.1.1",
            "--flake8-ignore",
            "E402, F401",
        ],
    )
    assert result.exit_code == 0

    files = os.listdir(tmpdir.dirname)
    for i in range(5):
        assert f"this_is_a_test_{i}.py" in files
