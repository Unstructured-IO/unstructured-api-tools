from dataclasses import dataclass
import os
from typing import Optional
import yaml
import re


def get_config(filename: Optional[str] = None):
    if filename is None:
        default = os.path.join(os.getcwd(), "preprocessing-pipeline-family.yaml")
        filename = os.environ.get("PIPELINE_FAMILY_CONFIG", default)

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"A pipeline family config was not found at {filename}."
            "The config class looks for the config in the following "
            "order:\n"
            "    1. The filename parameter\n"
            "    2. The PIPELINE_FAMILY_CONFIG environment variable\n"
            '    3. "${PWD}"/pipeline-family.yaml'
        )

    with open(filename, "r") as f:
        config = yaml.safe_load(f)

    return config


@dataclass
class PipelineConfig:
    name: str
    version: str
    description: str
    long_description: str
    filename: str

    def __init__(self, filename: Optional[str] = None):
        """Parses pipeline family metadata from the pipeline-family.yaml file. If no
        filename is passed, reverts to the PIPELINE_FAMILY_CONFIG environment variable.
        Otherwise, looks for pipeline-family.yaml in the working directory."""
        config = get_config(filename)

        self.name = config["name"]
        self.version = config["version"]
        self.description = config.get("description", "Unstructured Pipeline API")
        self.long_description = config.get("long_description", "")


def raise_for_invalid_semver_string(semver: str):
    """Raise an error if the semver string is invalid."""
    # NOTE(yuming): Suggested regular expression (RegEx) to check a semver string
    # ref: https://semver.org/#is-there-a-suggested-regular-expression
    # -regex-to-check-a-semver-string
    valid_semver_pattern = r"""^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.
                        (?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-]
                        [0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?
                        (?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"""
    valid_semver_re = re.compile(valid_semver_pattern, re.VERBOSE)

    if not re.match(valid_semver_re, semver):
        raise ValueError("Semver string must be a valid string.")


def get_pipeline_path(
    filename: str,
    pipeline_family: Optional[str] = None,
    semver: Optional[str] = None,
    config_filename: Optional[str] = None,
    shorter: Optional[bool] = False,
) -> str:
    """Builds the pipeline path according to the conventions outlined in the architecture docs.
    ref: https://github.com/Unstructured-IO/
    docs-and-arch/blob/main/Pipelines-and-APIs.md#api-specification
    """
    if any([pipeline_family, semver]) and not all([pipeline_family, semver]):
        raise ValueError(
            "If either pipeline_family or semver is specified, the other must be "
            "specified as well."
        )

    if not any([pipeline_family, semver]):
        config = PipelineConfig(filename=config_filename)
        pipeline_family = config.name
        semver = config.version
    else:
        # NOTE(robinson) - Explicit type casting if the variables are passed. Otherwise
        # mypy gets cranky because Optional[str] implies they could be None.
        pipeline_family = str(pipeline_family)
        semver = str(semver)

    raise_for_invalid_semver_string(semver)

    if shorter:
        semver = semver.split(".")[0]

    pipeline_family = pipeline_family.replace("_", "-")

    filepath = filename.split("/")
    # NOTE(robinson) - Converts something like "sec_filings.py" to "sec-filings"
    pipeline_name = filepath[-1].replace("_", "-").replace(".py", "")

    return f"/{pipeline_family}/v{semver}/{pipeline_name}"


def get_api_name_from_config(filename: Optional[str] = None):
    try:
        return get_config(filename).get("name", None)
    except FileNotFoundError:
        return None
