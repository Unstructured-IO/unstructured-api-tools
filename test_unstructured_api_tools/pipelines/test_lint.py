import os
import pytest
import re
from unittest.mock import patch

import unstructured_api_tools.pipelines.lint as lint


class MockPopen:
    def __init__(self, *args, **kwargs):
        pass

    def communicate(self, *args, **kwargs):
        raise ValueError("Squawk!")


def test_run_lint_cmd_cleans_up_on_exception(monkeypatch):
    monkeypatch.setattr(lint, "Popen", MockPopen)
    with patch.object(os, "unlink", return_value=None) as mock_unlink:
        with pytest.raises(ValueError):
            lint._run_lint_cmd(["fake"], "fake.py", re.compile("[A-Z]"))

    mock_unlink.assert_called_once()


def test_flake8():
    file_text = """# A test file

def hello_world():
    pass
"""
    assert lint.check_flake8(file_text) is True


def test_flake8_passes_with_unsued_import():
    file_text = """# A test file

def hello_world():
    pass


import os
"""
    assert lint.check_flake8(file_text) is True


def test_flake8_raises_with_bad_lint():
    file_text = """# A test file

def hello_world()   :
    pass"""
    with pytest.raises(lint.LintError):
        lint.check_flake8(file_text)


def test_format_black():
    file_text = """# A test file

def hello_world()   :
    pass
"""
    formatted_text = lint.format_black(file_text)

    assert (
        formatted_text
        == """# A test file


def hello_world():
    pass
"""
    )


def test_validate_flake8_ignore():
    lint.validate_flake8_ignore("E405, F401") is True


def test_validate_flake8_ignore_bad_input():
    with pytest.raises(ValueError):
        lint.validate_flake8_ignore("NOT A REAL CODE")


def test_mypy():
    file_text = """# A test file

def hello_world(text: str) -> str:
    return text
"""
    assert lint.check_mypy(file_text) is True


def test_mypy_raises_with_bad_type():
    file_text = """# A test file

def hello_world(text: str) -> str:
    return int(text)
"""
    with pytest.raises(lint.LintError):
        lint.check_mypy(file_text)


def test_check_black():
    file_text = """# A test file


def hello_world():
    pass
"""
    assert lint.check_black(file_text) is True


def test_check_black_raises_with_bad_format():
    file_text = """# A test file


def hello_world()   :
    pass
"""
    with pytest.raises(lint.LintError):
        lint.check_black(file_text)
