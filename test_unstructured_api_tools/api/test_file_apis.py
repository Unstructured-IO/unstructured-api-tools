from base64 import b64decode
import json
import os
import pytest

from requests_toolbelt.multipart import decoder

from fastapi.testclient import TestClient

from prepline_test_project.api.process_file_1 import app

PROCESS_FILE_1_ROUTE = "/test-project/v1.2.3/process-file-1"

FILE_A = "test_unstructured_api_tools/api/fixtures/fake.docx"
FILE_B = "test_unstructured_api_tools/api/fixtures/example.jpg"

FILENAME_LENGTHS = {FILE_A: 36602, FILE_B: 32764}
FILENAME_FORMATS = {
    FILE_A: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    FILE_B: "image/jpeg",
}

P_INPUT_1_SINGLE = {"input_1": ["hi"]}
P_INPUT_1_MULTI = {"input_1": ["hi", "water is better than ice"]}
P_INPUT_2_SINGLE = {"input_2": ["hello"]}
P_INPUT_2_MULTI = {"input_2": ["hello", "earth is better than mars"]}
P_INPUT_1_AND_2_MULTI = {"input_2": ["hello", "earth is better than mars"], "input_1": ["hi"]}

JSON = "application/json"
MIXED = "multipart/mixed"
TEXT_CSV = "text/csv"


def _assert_response_for_process_file_1(test_files, test_params, test_type_header, response):
    """assert json response payload matches expected response."""
    api_param_value = []
    if test_params is not None and "input_2" in test_params:
        api_param_value = test_params["input_2"]

    def _json_for_one_file(test_file):
        return {
            "silly_result": " : ".join(
                [
                    str(FILENAME_LENGTHS[test_file]),
                    test_file,
                    FILENAME_FORMATS[test_file],
                    str(api_param_value),
                ]
            )
        }

    if test_type_header == JSON:
        if len(test_files) == 1:
            assert response.json() == _json_for_one_file(test_files[0])
        else:
            assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]

    elif test_type_header == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


@pytest.mark.parametrize(
    "test_files,test_params,test_type_header,expected_status",
    [
        ([FILE_A], P_INPUT_2_SINGLE, JSON, 200),
        ([FILE_A], P_INPUT_2_MULTI, JSON, 200),
        ([FILE_A], None, JSON, 200),
        ([FILE_A], P_INPUT_1_SINGLE, JSON, 200),
        ([FILE_A], P_INPUT_1_MULTI, JSON, 200),
        ([FILE_A], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_B], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_A, FILE_B], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_A, FILE_B], P_INPUT_1_AND_2_MULTI, MIXED, 200),
        # json returned though mixed requested (maybe not a bug for 1 file?)
        pytest.param([FILE_A], P_INPUT_1_MULTI, MIXED, 200, marks=pytest.mark.xfail),
        # json returned though csv requested
        pytest.param([FILE_B], P_INPUT_1_AND_2_MULTI, TEXT_CSV, 200, marks=pytest.mark.xfail),
    ],
)
def test_process_file_1(test_files, test_params, test_type_header, expected_status):
    # NOTE(robinson) - Reset the rate limit to avoid 429s in tests
    client = TestClient(app)

    _files = [
        ("files", (test_file, open(test_file, "rb"), FILENAME_FORMATS[test_file]))
        for test_file in test_files
    ]

    headers_kwargs = {}
    if test_type_header is not None:
        headers_kwargs = {
            "headers": {
                "Accept": test_type_header,
            }
        }

    response = client.post(PROCESS_FILE_1_ROUTE, files=_files, data=test_params, **headers_kwargs)
    assert response.status_code == expected_status
    if response.status_code == 200:
        if test_type_header == MIXED:
            assert response.headers["content-type"].startswith("multipart/mixed; boundary=")
        else:
            assert response.headers["content-type"] == test_type_header
        _assert_response_for_process_file_1(test_files, test_params, test_type_header, response)


@pytest.mark.parametrize(
    "mimetype,filename,expected_status",
    [
        ("application/epub+zip", "file.epub", 200),
        ("application/json", "file.json", 200),
        ("application/msword", "file.doc", 200),
        ("application/pdf", "file.pdf", 200),
        ("application/vnd.ms-powerpoint", "file.ppt", 200),
        (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "file.pptx",
            200,
        ),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file.docx",
            200,
        ),
        ("application/xml", "file.xml", 400),
        ("application/zip", "file.zip", 400),
        ("image/jpeg", "file.jpeg", 200),
        ("image/png", "file.png", 200),
        ("message/rfc822", "file.eml", 200),
        ("text/html", "file.html", 200),
        ("text/markdown", "file.md", 200),
        ("text/plain", "file.txt", 200),
        ("video/mp4", "file.mp4", 400),
    ],
)
def test_supported_mimetypes(mimetype, filename, expected_status):
    """
    Verify that we return 400 if a filetype is not supported.
    Because we use the mimetype for this, let's just POST different content types
    without caring what the actual file is.
    """
    client = TestClient(app)

    # Keying off of the mimetype just works (there are 4 paths to test)
    # One file
    response = client.post(
        PROCESS_FILE_1_ROUTE, files=[("files", ("example-filename", open(FILE_A, "rb"), mimetype))]
    )
    assert response.status_code == expected_status

    # Multiple files
    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[
            ("files", ("example-filename", open(FILE_A, "rb"), mimetype)),
            ("files", ("example-filename", open(FILE_A, "rb"), mimetype)),
        ],
    )

    # When there are more test fixtures - come back
    # and add single file plus text input, multi file plus text input

    # If the client doesn't set a mimetype, we may just see application/octet-stream
    # Here we fall back to the file extension
    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (filename, open(FILE_A, "rb"), "application/octet-stream"))],
    )
    assert response.status_code == expected_status


def test_reconfigure_supported_mimetypes():
    """
    Verify that we can change the supported mimetype list via env variable
    """
    client = TestClient(app)

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_A, open(FILE_A, "rb"), FILENAME_FORMATS[FILE_A]))],
    )
    assert response.status_code == 200

    os.environ["UNSTRUCTURED_ALLOWED_MIMETYPES"] = "image/jpeg"

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_A, open(FILE_A, "rb"), FILENAME_FORMATS[FILE_A]))],
    )
    assert response.status_code == 400

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_B, open(FILE_B, "rb"), FILENAME_FORMATS[FILE_B]))],
    )
    assert response.status_code == 200
