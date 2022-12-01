import tarfile
import tempfile
from typing import List
import zipfile

from fastapi import UploadFile


def expand_tarred_upload(upload_file: UploadFile) -> List[UploadFile]:
    files: List[UploadFile] = list()

    tar = upload_file.file
    with tar.open(tar.name, "r:*") as _tar:
        for member in _tar.getmembers():
            f = _tar.extractfile(member)
            files.append(UploadFile(filename=f.name, file=f))

    return files


def expand_zipped_upload(upload_file: UploadFile) -> List[UploadFile]:
    files: List[UploadFile] = list()

    zipped_file = upload_file.file
    for filename in zipped_file.namelist():
        f = zipped_file.open(filename)
        files.append(UploadFile(filename=f.name, file=f))

    return files


def is_tarfile(file: tempfile.SpooledTemporaryFile) -> bool:
    """Deteremines if the SpooledTemporaryFile is a tar file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(file.read())
        _is_tarfile = tarfile.is_tarfile(tmp_file.name)

    file.seek(0)
    return _is_tarfile


def is_zipfile(file: tempfile.SpooledTemporaryFile) -> bool:
    """Deteremines if the SpooledTemporaryFile is a zip file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(file.read())
        _is_zipfile = zipfile.is_zipfile(tmp_file.name)

    file.seek(0)
    return _is_zipfile


def open_tar(file: tempfile.SpooledTemporaryFile):
    return tarfile.open(fileobj=files[0].file, mode="r:gz")
