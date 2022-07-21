"""Tools for converting pipeline notebooks to Python scripts/REST APIs"""
from copy import deepcopy
import imp
import inspect
import os
from pathlib import Path
import re
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from nbconvert import ScriptExporter
import nbformat

from unstructured_api_tools.pipelines.api_conventions import get_pipeline_path
import unstructured_api_tools.pipelines.lint as lint

INPUT_LINES_RE = re.compile(r"\n\n# In\[.+\]:")
PIPELINE_API_RE = re.compile(r"\n\n# pipeline-api")
HEADERS_RE = re.compile(r"#(!/usr/bin/env python| coding: utf-8)")

PIPELINE_FILENAME_RE = re.compile("pipeline-.*\\.ipynb")

PATH = Path(__file__).resolve().parent
TEMPLATE_PATH = os.path.join(PATH, "templates")


def generate_pipeline_api(
    filename: str,
    pipeline_family: Optional[str] = None,
    semver: Optional[str] = None,
    config_filename: Optional[str] = None,
    flake8_opts: List[str] = lint.FLAKE8_DEFAULT_OPTS,
) -> str:
    """Given the filename for a pipeline notebooks, generates the a FastAPI
    application with the appropriate REST routes."""
    notebook = read_notebook(filename)
    script = notebook_to_script(notebook)
    pipeline_path = get_pipeline_path(
        filename=get_script_filename(filename),
        pipeline_family=pipeline_family,
        semver=semver,
        config_filename=config_filename,
    )
    multi_string_param_names = _infer_params_from_pipeline_api(script)

    environment = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
    template = environment.get_template("pipeline_api.txt")
    content = template.render(
        pipeline_path=pipeline_path,
        script=script,
        multi_string_param_names=multi_string_param_names,
    )
    content = lint.format_black(content)
    lint.check_flake8(content, opts=flake8_opts)
    lint.check_mypy(content)
    return content


def _infer_params_from_pipeline_api(script: str) -> List[str]:
    """A helper function to prepare jinja interpolation.
    Returns a list of string (multi-value) parameters to expose in the FastAPI route.
    """
    infer_module = imp.new_module("infer_module")
    exec(script, infer_module.__dict__)
    params = inspect.signature(infer_module.pipeline_api).parameters

    multi_string_param_names = []

    if len(params) < 1:
        raise ValueError("pipeline_api must have at least one parameter named text")

    if "text" not in params or params["text"].default is not inspect._empty:
        # NOTE(crag) coming soon: first argument may instead represent binary content
        # (which would imply updating pipeline_api.txt for either)
        raise ValueError("First parameter must be named text and not have a default value")

    first_param = True
    for param in params:
        if first_param:
            if param != "text":
                raise ValueError("First parameter must be named text")
            first_param = False
        elif param.startswith("m_"):
            # NOTE(crag) string parameter that may have multiple values
            if params[param].default is inspect._empty or params[param].default != []:
                raise ValueError(f"Default argument for {param} must be empty list")
            else:
                # NOTE(crag): "m_" is stripped from the FastAPI API params.
                # E.g., the pipeline param m_my_param implies a FastAPI param of my_param
                multi_string_param_names.append(param[2:])
        else:
            raise ValueError(
                f"Unsupported parameter name {param}, must either be text or begin with m_"
            )

    return multi_string_param_names


def notebook_file_to_script(
    input_filename: str,
    output_directory: str,
    pipeline_family: Optional[str] = None,
    semver: Optional[str] = None,
    config_filename: Optional[str] = None,
    flake8_opts: List[str] = lint.FLAKE8_DEFAULT_OPTS,
):
    """Converts a notebook file to a Python script and saves it to a Python script with
    the appropriate filename. Given an input file that looks like pipeline-<pipeline>.ipynb,
    the output file is <pipeline>.py"""
    script = generate_pipeline_api(
        input_filename,
        pipeline_family=pipeline_family,
        semver=semver,
        config_filename=config_filename,
        flake8_opts=flake8_opts,
    )
    script_filename = os.path.join(output_directory, get_script_filename(input_filename))
    with open(script_filename, "w") as f:
        f.write(script)


def read_notebook(filename: str) -> nbformat.NotebookNode:
    """Reads in a Jupyter notebook as a Python dictionary."""
    with open(filename, "r") as f:
        notebook = nbformat.read(f, as_version=4)
    return notebook


def get_pipeline_api_cells(notebook: nbformat.NotebookNode) -> nbformat.NotebookNode:
    """Filters a notebook down to only include code cells that start with # pipeline-api,
    per the convention outlined in the architecture docs.
    ref: https://github.com/Unstructured-IO/docs-and-arch/
        blob/main/Pipelines-and-APIs.md#github-repository-conventions-for-pipeline-families"""
    api_notebook = deepcopy(notebook)
    del api_notebook["cells"]

    api_cells: List[dict] = list()
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue

        if cell["source"].strip().startswith("# pipeline-api"):
            api_cell = deepcopy(cell)
            api_cell["outputs"] = list()
            api_cells.append(api_cell)

    api_notebook["cells"] = api_cells
    return api_notebook


def notebook_to_script(notebook: nbformat.NotebookNode) -> str:
    """Converts a notebook to a Python script, looking for cells that beging with # pipeline-api"""
    script_exporter = ScriptExporter()
    api_notebook = get_pipeline_api_cells(notebook)
    body, _ = script_exporter.from_notebook_node(api_notebook)
    return _cleanup_script(body)


def _cleanup_script(script: str) -> str:
    """Cleans unnecessary lines from the script file, including:
    - Input lines, which look like "# In[4]: "
    - The preamble that specifies the python environment and utf-8 encoding"""
    script = INPUT_LINES_RE.sub("", script)
    script = PIPELINE_API_RE.sub("", script)
    script = HEADERS_RE.sub("", script)
    return script.strip()


def get_script_filename(notebook_filename: str) -> str:
    """Converts the pipeline-notebook filename to a Python module filename in accordance
    with the conventions in the architecture and docs repo. Any dashes are converted
    to underscores.
    ref: https://github.com/Unstructured-AI/docs-and-arch
        /blob/main/Pipelines-and-APIs.md#github-repository-conventions-for-pipeline-families"""
    return f"{get_api_name(notebook_filename)}.py"


def get_api_name(notebook_filename: str) -> str:
    """Converts the pipeline-notebook filename to an api-name. Dashes are converted to
    underscores, the extension is dropped and 'pipeline-' is dropped as a prefix."""
    notebook_filename = os.path.basename(notebook_filename)
    _validate_notebook_filename(notebook_filename)
    return notebook_filename[9:-6].replace("-", "_")


def _validate_notebook_filename(notebook_filename: str):
    """Raises an error if the notebook filename is not valid."""
    if PIPELINE_FILENAME_RE.match(notebook_filename) is None:
        raise ValueError(
            f"Notebook filename is invalid: {notebook_filename} . "
            "Must follow the format: pipeline-<api-name>.ipynb ."
        )
