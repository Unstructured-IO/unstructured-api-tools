
import os
import tarfile
import tempfile
from tempfile import SpooledTemporaryFile
from typing import Callable, List
import zipfile

from fastapi import UploadFile


def process_tarred_files(file: UploadFile, pipeline_api: Callable, pipeline_kwargs: dict):
    response = []
    tar = tarfile.open(fileobj=file.file, mode="r:gz")
    with tempfile.TemporaryDirectory() as tmpdir:
        tar.extractall(tmpdir)

        for _file in os.listdir(tmpdir):
            filename = os.path.join(tmpdir, _file)
            with open(filename, "rb") as f:
                _response = pipeline_api(f, filename=filename, **pipeline_kwargs)

        response.append(_response)

    return response




def _expand_tarred_upload(upload_file: UploadFile) -> List[UploadFile]:
    """If an UploadFile object is a tarfile, this function will unpack the files
    within the tar as a list of UploadFiles."""
    files: List[UploadFile] = list()

    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(upload_file.file.read())
    tmp_file.close()

    with tarfile.open(fileobj=tmp_file, mode="r:gz") as tar:
        for member in tar.getmembers():

            f = tar.extractfile(member)
            files.append(UploadFile(filename=f.name, file=open(f.name, "r")))

    return files


def tar_to_spooled_temp_files(upload_file: UploadFile) -> List[SpooledTemporaryFile]:
    tar = tarfile.open(fileobj=upload_file.file, mode="r:gz")

    expanded_files = []
    for member in tar.getmembers():
        stf = SpooledTemporaryFile()
        file = tar.extractfile(member)
        file.seek(0)
        stf.write(file.read())
        stf.seek(0)

        upload_file = UploadFile(filename=file.name, file=stf)
        expanded_files.append(upload_file)

    return expanded_files


def expand_tarred_upload(upload_file: UploadFile) -> List[UploadFile]:
    files = list()

    tar = upload_file.file
    with tarfile.open(fileobj=tar, mode="r:*") as _tar:
        for member in _tar.getmembers():
            files.append(_tar.extractfile(member))
            # files.append(UploadFile(filename=f.name, file=f))

    return files


def expand_zipped_upload(upload_file: UploadFile) -> List[UploadFile]:
    """If an UploadFile object is a zipfile, this function will unpack the files
    within the zip as a list of UploadFiles."""
    files: List[UploadFile] = list()

    zipped_file = upload_file.file
    for filename in zipped_file.namelist():
        f = zipped_file.open(filename)
        files.append(UploadFile(filename=f.name, file=f))

    return files


def is_tarfile(upload_file: UploadFile) -> bool:
    """Determines if the UploadFile is a tar file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(upload_file.file.read())
        _is_tarfile = tarfile.is_tarfile(tmp_file.name)

    upload_file.file.seek(0)
    return _is_tarfile


def is_zipfile(upload_file: UploadFile) -> bool:
    """Deteremines if the UploadFile is a zip file or not."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(file.read())
        _is_zipfile = zipfile.is_zipfile(tmp_file.name)

    upload_file.seek(0)
    return _is_zipfile
