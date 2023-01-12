import os
from typing import Optional

import click

from unstructured_api_tools.pipelines.convert import convert_notebook_files_to_api
from unstructured_api_tools.pipelines.lint import (
    FLAKE8_DEFAULT_OPTS,
    validate_flake8_ignore,
)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input-directory")
@click.option("--output-directory")
@click.option("--pipeline-family")
@click.option("--semver")
@click.option("--config-filename")
@click.option("--flake8-ignore")
def convert_pipeline_notebooks(
    input_directory: str,
    output_directory: str,
    pipeline_family: Optional[str] = None,
    semver: Optional[str] = None,
    config_filename: Optional[str] = None,
    flake8_ignore: Optional[str] = None,
):
    """Convert a pipeline notebook to a Python script. The conversion script will retain
    any cell that includes # pipeline-api at the top."""
    notebook_filenames = sorted([f for f in os.listdir(input_directory) if f.endswith(".ipynb")])

    if flake8_ignore:
        validate_flake8_ignore(flake8_ignore)
        # NOTE(robinson) - Not making line length configurable because setting it to
        # 100 allows flake8 to be consistent with black
        flake8_opts = ["--max-line-length", "100", "--ignore", flake8_ignore]
    else:
        flake8_opts = FLAKE8_DEFAULT_OPTS

    convert_notebook_files_to_api(
        notebook_filenames,
        input_directory,
        output_directory,
        pipeline_family=pipeline_family,
        semver=semver,
        config_filename=config_filename,
        flake8_opts=flake8_opts,
    )


if __name__ == "__main__":
    cli()  # pragma: nocover
