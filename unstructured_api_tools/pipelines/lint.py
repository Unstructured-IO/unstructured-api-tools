"""Tools for linting and autoformatting generated API files."""
import os
import re
from subprocess import PIPE, Popen
import tempfile
from typing import List
from autoflake import (
    check,
    filter_unused_import,
    SAFE_IMPORTS,
    unused_import_module_name,
    filter_useless_pass,
)
import pyflakes.api
import pyflakes.messages
import pyflakes.reporter
import io
import collections

from black import format_str, FileMode
from autoflake import fix_code

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
    return format_str(file_text, mode=FileMode(line_length=100))


def format_autoflake(file_text: str) -> str:
    return fix_code(
        source=file_text,
        remove_unused_variables=True,
        remove_all_unused_imports=True,
        expand_star_imports=True,
    )


"""
Autoflake only takes into account unused imports by checking for pyflakes.messages.UnusedImport
but does not handle duplicate imports which come out as pyflakes.messages.RedefinedWhileUnused
from pyflakes. The following code is an extension of autoflake to take duplicate
imports into account
"""


def duplicate_import_line_numbers(messages):
    """Yield line numbers of unused imports."""
    for message in messages:
        if isinstance(message, pyflakes.messages.RedefinedWhileUnused):
            yield message.lineno


def _remove_duplicate_imports(text: str):
    messages = check(text)
    marked_import_line_numbers = frozenset(
        duplicate_import_line_numbers(messages),
    )
    marked_unused_module = collections.defaultdict(lambda: [])
    for line_number, module_name in unused_import_module_name(messages):
        marked_unused_module[line_number].append(module_name)
    sio = io.StringIO(text)
    previous_line = ""
    result = None
    for line_number, line in enumerate(sio.readlines(), start=1):
        if line_number in marked_import_line_numbers:
            result = filter_unused_import(
                line,
                unused_module=marked_unused_module[line_number],
                remove_all_unused_imports=True,
                imports=SAFE_IMPORTS,
                previous_line=previous_line,
            )
        else:
            result = line
        yield result
        previous_line = line


def remove_duplicate_imports(text: str) -> str:
    return "".join(filter_useless_pass("".join(_remove_duplicate_imports(text))))
