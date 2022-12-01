"""Tools for linting and autoformatting generated API files."""
import os
import re
from subprocess import PIPE, Popen
import tempfile
from typing import List

from black import format_str, FileMode

# NOTE(robinson) - F401 is for unused imports
FLAKE8_DEFAULT_OPTS: List[str] = ["--max-line-length", "100", "--ignore", "F401"]
FLAKE8_PREFIX_RE = re.compile(r".+:\d+:\d+:\s")
FLAKE8_ERROR_CODE_RE = re.compile(r"([A-Z]\d{3},?\s?)+")

MYPY_PREFIX_RE = re.compile(r".+:\d+:\s")


class LintError(RuntimeError):
    pass


def _create_tempfile(file_text: str):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(file_text.encode())
    tmp.close()
    return tmp


def _create_file_for_user_debugging(content: str, filename: str):
    """Creates file in user's current working to facilitate debugging lint errors."""
    with open(filename, "w+") as f:
        f.write(content)


def _run_lint_cmd(cmd: List[str], filename: str, prefix_re: re.Pattern):
    """Runs a subprocess with the specified lint command and raises a LintError
    if the file does not pass."""
    try:
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, _ = process.communicate()
    except Exception as e:
        # NOTE(robinson) - Catching the error ensures we clean up the temp file
        os.unlink(filename)  # NOTE(robinson) - Removes the temporary file
        raise e

    os.unlink(filename)  # NOTE(robinson) - Removes the temporary file
    if process.returncode != 0:
        err = prefix_re.sub("", stdout.decode("utf-8"))
        raise LintError("\n\n" + err)

    return True


def check_flake8(file_text: str, opts: List[str] = FLAKE8_DEFAULT_OPTS) -> bool:
    """Runs flake8 on the text. Raises and exception if the file does
    not pass linting. Uses subprocess because per the Flake8 docs, Flake8
    does not have a public Python API.
    ref: https://flake8.pycqa.org/en/latest/user/python-api.html#public-python-api"""
    tmp = _create_tempfile(file_text)
    cmd = ["flake8", tmp.name] + opts
    try:
        _run_lint_cmd(cmd, tmp.name, MYPY_PREFIX_RE)
    except Exception as e:
        debug_file = "tmp-flake8-check-pipeline-api.py"
        _create_file_for_user_debugging(file_text, debug_file)
        cmd[1] = debug_file
        raise LintError("run the following to debug: \n" f"{' '.join(cmd)}") from e
    return True


def validate_flake8_ignore(flake8_ignore: str) -> bool:
    """Validates the CLI argument for Flake8 errors. For CLI input validation."""
    if FLAKE8_ERROR_CODE_RE.match(flake8_ignore) is None:
        raise ValueError(f"{flake8_ignore} is an invalid argument for the --flake8-ignore flag.")
    return True


def check_mypy(file_text: str):
    """Runs mypy type checking on the file text."""
    tmp = _create_tempfile(file_text)
    cmd = ["mypy", tmp.name, "--ignore-missing-imports", "--implicit-optional"]
    try:
        _run_lint_cmd(cmd, tmp.name, MYPY_PREFIX_RE)
    except Exception as e:
        debug_file = "tmp-myp-check-pipeline-api.py"
        _create_file_for_user_debugging(file_text, debug_file)
        cmd[1] = debug_file
        raise LintError("run the following to debug: \n" f"{' '.join(cmd)}") from e
    return True


def check_black(file_text: str) -> bool:
    """Checks if a file needs to be reformatted with black."""
    passes = format_black(file_text) == file_text
    if not passes:
        raise LintError("File text needs to be reformatted with black.")
    return passes


def format_black(file_text: str) -> str:
    """Auto-formats a file using black."""
    return format_str(file_text, mode=FileMode())
