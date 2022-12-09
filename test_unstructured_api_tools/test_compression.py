import os
import tarfile

from fastapi import UploadFile

import unstructured_api_tools.compression as compression


def test_is_tarfile(tmpdir):
    filename = os.path.join(tmpdir, "tmp-file.txt")
    with open(filename, "w") as f:
        f.write("This is a test file.")

    tar_filename = os.path.join(tmpdir, "fake-files.tar.gz")
    with tarfile.open(tar_filename, "w:tar") as tar:
        tar.add(filename)
        tar.add(filename)

    # tar_filename = "/Users/mrobinson/repos/pipeline-oer/sample-docs/oers.tar.gz"
    with open(tar_filename, "rb") as f:
        upload_file = UploadFile(file=f, filename=tar_filename)
        assert compression.is_tarfile(upload_file) is True

