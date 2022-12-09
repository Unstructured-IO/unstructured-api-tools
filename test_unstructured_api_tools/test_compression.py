import os
import pathlib
import pytest
import tarfile

from fastapi import UploadFile

import unstructured_api_tools.compression as compression


DIRECTORY = pathlib.Path(__file__).parent.resolve()


def test_is_tarfile(tmpdir):
    filename = os.path.join(tmpdir, "tmp-file.txt")
    with open(filename, "w") as f:
        f.write("This is a test file.")

    tar_filename = os.path.join(tmpdir, "fake-files.tar.gz")
    with tarfile.open(tar_filename, "w:tar") as tar:
        tar.add(filename)

    with open(tar_filename, "rb") as f:
        upload_file = UploadFile(file=f, filename=tar_filename)
        assert compression.is_tarfile(upload_file) is True


def test_is_zipfile():
    zip_filename = os.path.join(DIRECTORY, "test-zip.zip")
    with open(zip_filename, "rb") as f:
        upload_file = UploadFile(file=f, filename=zip_filename)
        assert compression.is_zipfile(upload_file) is True


def pipeline_api(f, filename=None):
    return {}


def test_process_file(tmpdir):
    filename = os.path.join(tmpdir, "tmp-file.txt")
    with open(filename, "w") as f:
        f.write("This is a test file.")

    assert compression._process_file(filename, pipeline_api, "file") == {}
    assert compression._process_file(filename, pipeline_api, "text") == {}
    with pytest.raises(ValueError):
        compression._process_file(filename, pipeline_api, "bad_type")
