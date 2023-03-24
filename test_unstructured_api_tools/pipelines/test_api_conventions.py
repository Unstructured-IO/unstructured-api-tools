import os
import pytest
import yaml

import unstructured_api_tools.pipelines.api_conventions as conventions


@pytest.fixture
def sample_config():
    return {"version": "0.2.1", "name": "sec_filings"}


@pytest.mark.parametrize(
    # NOTE(yuming): Test cases ref: https://regex101.com/r/Ly7O1x/3/
    "invalid_semver_string",
    [
        "1",
        "1.2",
        "1.2.3-0123",
        "1.2.3-0123.0123",
        "1.1.2+.123",
        "+invalid",
        "-invalid",
        "-invalid+invalid",
        "-invalid.01",
        "alpha",
        "alpha.beta",
        "alpha.beta.1",
        "alpha.1",
        "alpha+beta",
        "alpha_beta",
        "alpha.",
        "alpha..",
        "beta",
        "1.0.0-alpha_beta",
        "-alpha.",
        "1.0.0-alpha..",
        "1.0.0-alpha..1",
        "1.0.0-alpha...1",
        "1.0.0-alpha....1",
        "1.0.0-alpha.....1",
        "1.0.0-alpha......1",
        "1.0.0-alpha.......1",
        "01.1.1",
        "1.01.1",
        "1.1.01",
        "1.2",
        "1.2.3.DEV",
        "1.2-SNAPSHOT",
        "1.2.31.2.3----RC-SNAPSHOT.12.09.1--..12+788",
        "1.2-RC-SNAPSHOT",
        "-1.0.3-gamma+b7718",
        "+justmeta",
        "9.8.7+meta+meta",
        "9.8.7-whatever+meta+meta",
        "9999999999999.999999999999999999.999999999----RC-SNAPSHOT.12.09.1---------..12",
    ],
)
def test_raise_for_invalid_semver_string(invalid_semver_string):
    with pytest.raises(ValueError):
        conventions.raise_for_invalid_semver_string(invalid_semver_string)


@pytest.mark.parametrize(
    # NOTE(yuming): Test cases ref: https://regex101.com/r/Ly7O1x/3/
    "valid_semver_string",
    [
        "0.0.4",
        "1.2.3",
        "10.20.30",
        "1.1.2-prerelease+meta",
        "1.1.2+meta",
        "1.1.2+meta-valid",
        "1.0.0-alpha",
        "1.0.0-beta",
        "1.0.0-alpha.beta",
        "1.0.0-alpha.beta.1",
        "1.0.0-alpha.1",
        "1.0.0-alpha0.valid",
        "1.0.0-alpha.0valid",
        "1.0.0-alpha-a.b-c-somethinglong+build.1-aef.1-its-okay",
        "1.0.0-rc.1+build.1",
        "2.0.0-rc.1+build.123",
        "1.2.3-beta",
        "10.2.3-DEV-SNAPSHOT",
        "1.2.3-SNAPSHOT-123",
        "1.0.0",
        "2.0.0",
        "1.1.7",
        "2.0.0+build.1848",
        "2.0.1-alpha.1227",
        "1.0.0-alpha+beta",
        "1.2.3----RC-SNAPSHOT.12.9.1--.12+788",
        "1.2.3----R-S.12.9.1--.12+meta",
        "1.2.3----RC-SNAPSHOT.12.9.1--.12",
        "1.0.0+0.build.1-rc.10000aaa-kk-0.1",
        "99999999999999999999999.999999999999999999.99999999999999999",
        "1.0.0-0A.is.legal",
    ],
)
def test_pass_for_valid_semver_string(valid_semver_string):
    try:
        conventions.raise_for_invalid_semver_string(valid_semver_string)
    except ValueError:
        assert False, f"{valid_semver_string} raised an exception."


def test_get_pipeline_path():
    path = conventions.get_pipeline_path(
        filename="risk_narrative.py", pipeline_family="sec_filings", semver="0.2.1"
    )
    assert path == "/sec-filings/v0.2.1/risk-narrative"


def test_get_short_pipeline_path():
    path = conventions.get_pipeline_path(
        filename="risk_narrative.py",
        pipeline_family="sec_filings",
        semver="0.2.1",
        shorter=True,
    )

    assert path == "/sec-filings/v0/risk-narrative"


def test_get_pipeline_path_raises_if_either_not_specified():
    with pytest.raises(ValueError):
        conventions.get_pipeline_path(
            filename="risk_narrative.py", pipeline_family="sec_filings", semver=None
        )

    with pytest.raises(ValueError):
        conventions.get_pipeline_path(
            filename="risk_narrative.py", pipeline_family=None, semver="0.2.1"
        )


def test_get_pipeline_path_reads_from_file(tmpdir, sample_config):
    filename = os.path.join(tmpdir.dirname, "pipeline-family.yaml")
    with open(filename, "w") as f:
        yaml.dump(sample_config, f)

    path = conventions.get_pipeline_path(filename="risk_narrative.py", config_filename=filename)
    assert path == "/sec-filings/v0.2.1/risk-narrative"


def test_pipeline_config_reads_from_file(tmpdir, sample_config):
    filename = os.path.join(tmpdir.dirname, "pipeline-family.yaml")
    with open(filename, "w") as f:
        yaml.dump(sample_config, f)

    config = conventions.PipelineConfig(filename=filename)
    assert config.name == "sec_filings"
    assert config.version == "0.2.1"


def test_pipeline_config_reads_from_env(tmpdir, monkeypatch, sample_config):
    filename = os.path.join(tmpdir.dirname, "pipeline-family.yaml")
    with open(filename, "w") as f:
        yaml.dump(sample_config, f)

    monkeypatch.setenv("PIPELINE_FAMILY_CONFIG", filename)

    config = conventions.PipelineConfig(filename=None)
    assert config.name == "sec_filings"


def test_pipeline_config_raises_with_missing_file(tmpdir, monkeypatch, sample_config):
    # NOTE(robinson) - Will default to looking for ${PWD}/pipeline-family.yaml, which
    # does not exist
    with pytest.raises(FileNotFoundError):
        conventions.PipelineConfig(filename=None)
