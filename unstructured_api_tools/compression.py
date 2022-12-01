import tarfile
import tempfile
import zipfile


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
