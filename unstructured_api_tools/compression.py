import os
import tarfile
import tempfile
from tempfile import SpooledTemporaryFile
from typing import Callable, List
import zipfile

from fastapi import UploadFile


def is_tarfile(upload_file: UploadFile) -> bool:
    """Determines if the UploadFile is a tar file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(upload_file.file.read())
        _is_tarfile = tarfile.is_tarfile(tmp_file.name)

    upload_file.file.seek(0)
    return _is_tarfile


def _process_file(filename: str, pipeline_api: Callable, accepts: str = "file"):
    if accepts == "file":
        with open(filename, "rb") as f:
            response = pipeline_api(f, filename=filename)
    elif accepts == "text":
        with open(filename, "r") as f:
            text = f.read()
            response = pipeline_api(text)
    else:
        raise ValueError(f"{accepts} is an invalid value for accepts." "Choose 'file' or 'text'.")
    return response


def process_tarred_files(file: UploadFile, pipeline_api: Callable, accepts: str = "file"):
    response = []
    tar = tarfile.open(fileobj=file.file, mode="r:gz")
    with tempfile.TemporaryDirectory() as tmpdir:
        tar.extractall(tmpdir)

        for _file in os.listdir(tmpdir):
            filename = os.path.join(tmpdir, _file)
            _response = _process_file(filename, pipeline_api, accepts)

        response.append(_response)

    return response


def process_zipped_files(
    file: UploadFile, pipeline_api: Callable, accepts: str = "file"
) -> List[UploadFile]:
    """If an UploadFile object is a zipfile, this function will unpack the files
    within the zip as a list of UploadFiles."""
    response = []
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(file.file.read())
        zf = zipfile.ZipFile(tmp_file.name, "r")

    with tempfile.TemporaryDirectory() as tmpdir:
        zf.extractall(tmpdir)
        for _file in os.listdir(tmpdir):
            filename = os.path.join(tmpdir, _file)
            _response = _process_file(filename, pipeline_api, accepts)

        response.append(_response)
    return response


def is_zipfile(upload_file: UploadFile) -> bool:
    """Deteremines if the UploadFile is a zip file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(upload_file.file.read())
        _is_zipfile = zipfile.is_zipfile(tmp_file.name)

    upload_file.file.seek(0)
    return _is_zipfile
