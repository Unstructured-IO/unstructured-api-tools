import json
from base64 import b64decode
import os

import pytest
from fastapi.testclient import TestClient
from prepline_test_project.api.app import app
from requests_toolbelt.multipart import decoder

from functions_and_variables import (
    FILENAME_LENGTHS,
    FILENAME_FORMATS,
    JSON,
    MIXED,
    FILE_DOCX,
    FILE_IMAGE,
    RESPONSE_SCHEMA_ISD,
    RESPONSE_SCHEMA_LABELSTUDIO,
    P_INPUT_1_SINGLE,
    P_INPUT_2_EMPTY,
    P_INPUT_2_MULTI,
    P_INPUT_1_AND_2_MULTI,
    P_INPUT_1_EMPTY,
    P_INPUT_1_MULTI,
    P_INPUT_2_SINGLE,
    TEXT_CSV,
    convert_files_for_api,
    generate_header_kwargs,
)

# accepts: files, input2
PROCESS_FILE_1_ROUTE = "/test-project/v1.2.3/process-file-1"

# Pull this over here for test_supported_mimetypes
PROCESS_FILE_TEXT_1_ROUTE = "/test-project/v1.2.3/process-text-file-1"

# accepts: files
PROCESS_FILE_2_ROUTE = "/test-project/v1.2.3/process-file-2"

# accepts: files, response_type, response_schema
PROCESS_FILE_3_ROUTE = "/test-project/v1.2.3/process-file-3"

# accepts: files, response_type, response_schema, input1
PROCESS_FILE_4_ROUTE = "/test-project/v1.2.3/process-file-4"

# accepts: files, response_type, response_schema, input1, input2
PROCESS_FILE_5_ROUTE = "/test-project/v1.2.3/process-file-5"

client = TestClient(app)


def _assert_response_for_process_file_1(test_files, test_params, test_type_header, response):
    """assert json response payload matches expected response."""
    api_param_value = []
    if test_params is not None and "input2" in test_params:
        api_param_value = test_params["input2"]

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


def _assert_response_for_process_file_2(test_files, response):
    def _json_for_one_file(test_file):
        return {"silly_result": " : ".join([str(FILENAME_LENGTHS[test_file])])}

    if len(test_files) == 1:
        assert response.json() == _json_for_one_file(test_files[0])
    else:
        assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]


def _asert_response_for_process_file_3(
    test_files, response, response_schema, response_type=TEXT_CSV
):
    def _json_for_one_file(test_file):
        return {
            "silly_result": " : ".join(
                [
                    str(FILENAME_LENGTHS[test_file]),
                    str(response_type),
                    str(response_schema["output_schema"]),
                ]
            )
        }

    if response_type in [JSON, TEXT_CSV]:
        if len(test_files) == 1:
            assert response.json() == _json_for_one_file(test_files[0])
        else:
            assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]
    elif response_schema == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


def _assert_response_for_process_file_4(
    test_files, response, response_schema, response_type, m_input1
):
    def _json_for_one_file(test_file):
        return {
            "silly_result": " : ".join(
                [
                    str(FILENAME_LENGTHS[test_file]),
                    str(FILENAME_FORMATS[test_file]),
                    str(response_type),
                    str(response_schema["output_schema"]),
                    str(m_input1["input1"]),
                ]
            )
        }

    if len(test_files) == 1:
        assert response.json() == _json_for_one_file(test_files[0])
    else:
        assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]


def _assert_response_for_process_file_5(
    test_files, response, response_schema, response_type, m_input1, m_input2
):
    def _json_for_one_file(test_file):
        return {
            "silly_result": " : ".join(
                [
                    str(FILENAME_LENGTHS[test_file]),
                    str(FILENAME_FORMATS[test_file]),
                    str(response_type),
                    str(response_schema["output_schema"]),
                    str(m_input1["input1"]),
                    str(m_input2["input2"]),
                ]
            )
        }

    if len(test_files) == 1:
        assert response.json() == _json_for_one_file(test_files[0])
    else:
        assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]


@pytest.mark.parametrize(
    "test_files,test_params,test_type_header,expected_status",
    [
        ([FILE_DOCX], P_INPUT_2_SINGLE, JSON, 200),
        ([FILE_DOCX], P_INPUT_2_MULTI, JSON, 200),
        ([FILE_DOCX], None, JSON, 200),
        ([FILE_DOCX], P_INPUT_1_SINGLE, JSON, 200),
        ([FILE_DOCX], P_INPUT_1_MULTI, JSON, 200),
        ([FILE_DOCX], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_IMAGE], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_DOCX, FILE_IMAGE], P_INPUT_1_AND_2_MULTI, JSON, 200),
        ([FILE_DOCX, FILE_IMAGE], P_INPUT_1_AND_2_MULTI, MIXED, 200),
        # json returned though mixed requested (maybe not a bug for 1 file?)
        pytest.param([FILE_DOCX], P_INPUT_1_MULTI, MIXED, 200, marks=pytest.mark.xfail),
        # json returned though csv requested
        pytest.param([FILE_IMAGE], P_INPUT_1_AND_2_MULTI, TEXT_CSV, 200, marks=pytest.mark.xfail),
    ],
)
def test_process_file_1(test_files, test_params, test_type_header, expected_status):
    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=convert_files_for_api(test_files),
        data=test_params,
        **generate_header_kwargs(test_type_header)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        if test_type_header == MIXED:
            assert response.headers["content-type"].startswith("multipart/mixed; boundary=")
        else:
            assert response.headers["content-type"] == test_type_header
        _assert_response_for_process_file_1(test_files, test_params, test_type_header, response)


@pytest.mark.parametrize(
    "test_files,expected_status", [([FILE_DOCX], 200), ([FILE_DOCX, FILE_IMAGE], 200)]
)
def test_process_file_2(test_files, expected_status):
    response = client.post(PROCESS_FILE_2_ROUTE, files=convert_files_for_api(test_files))
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_file_2(test_files, response)


@pytest.mark.parametrize(
    "test_files,response_type,response_schema,expected_status",
    [
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_ISD, 200),
        # endpoint doesn't accept mixed media type for one file
        pytest.param([FILE_DOCX], MIXED, RESPONSE_SCHEMA_ISD, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_DOCX], TEXT_CSV, RESPONSE_SCHEMA_ISD, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_DOCX], None, RESPONSE_SCHEMA_ISD, 200, marks=pytest.mark.xfail),
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        # endpoint doesn't accept mixed media type for one file
        pytest.param([FILE_DOCX], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        pytest.param(
            [FILE_DOCX], TEXT_CSV, RESPONSE_SCHEMA_LABELSTUDIO, 200, marks=pytest.mark.xfail
        ),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_DOCX], None, RESPONSE_SCHEMA_LABELSTUDIO, 200, marks=pytest.mark.xfail),
        ([FILE_DOCX, FILE_IMAGE], JSON, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX, FILE_IMAGE], MIXED, RESPONSE_SCHEMA_ISD, 200),
        # endpoint fails because text/csv is not acceptable for multiple files
        pytest.param(
            [FILE_DOCX, FILE_IMAGE], TEXT_CSV, RESPONSE_SCHEMA_ISD, 200, marks=pytest.mark.xfail
        ),
        ([FILE_DOCX, FILE_IMAGE], None, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX, FILE_IMAGE], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_DOCX, FILE_IMAGE], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        # endpoint fails because text/csv is not acceptable for multiple files
        pytest.param(
            [FILE_DOCX, FILE_IMAGE],
            TEXT_CSV,
            RESPONSE_SCHEMA_LABELSTUDIO,
            200,
            marks=pytest.mark.xfail,
        ),
        ([FILE_DOCX, FILE_IMAGE], None, RESPONSE_SCHEMA_LABELSTUDIO, 200),
    ],
)
def test_process_file_3(test_files, response_type, response_schema, expected_status):
    response = client.post(
        PROCESS_FILE_3_ROUTE,
        files=convert_files_for_api(test_files),
        data={**response_schema, "output_format": response_type},
        **generate_header_kwargs(response_type)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _asert_response_for_process_file_3(test_files, response, response_schema, response_type)


@pytest.mark.parametrize(
    "test_files,response_type,response_schema,m_input1,expected_status",
    [
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_ISD, P_INPUT_1_EMPTY, 200),
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_ISD, P_INPUT_1_MULTI, 200),
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_LABELSTUDIO, P_INPUT_1_SINGLE, 200),
        ([FILE_DOCX, FILE_IMAGE], JSON, RESPONSE_SCHEMA_LABELSTUDIO, P_INPUT_1_EMPTY, 200),
        ([FILE_DOCX, FILE_IMAGE], JSON, RESPONSE_SCHEMA_ISD, P_INPUT_1_MULTI, 200),
        ([FILE_DOCX, FILE_IMAGE], JSON, RESPONSE_SCHEMA_ISD, P_INPUT_1_SINGLE, 200),
    ],
)
def test_process_file_4(test_files, response_type, response_schema, m_input1, expected_status):
    response = client.post(
        PROCESS_FILE_4_ROUTE,
        files=convert_files_for_api(test_files),
        data={**response_schema, **m_input1, "output_format": response_type},
        **generate_header_kwargs(response_type)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_file_4(
            test_files, response, response_schema, response_type, m_input1
        )


@pytest.mark.parametrize(
    "test_files,response_type,response_schema,m_input1,m_input2,expected_status",
    [
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_ISD, P_INPUT_1_MULTI, P_INPUT_2_MULTI, 200),
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_LABELSTUDIO, P_INPUT_1_EMPTY, P_INPUT_2_MULTI, 200),
        ([FILE_DOCX], JSON, RESPONSE_SCHEMA_LABELSTUDIO, P_INPUT_1_SINGLE, P_INPUT_2_EMPTY, 200),
        (
            [FILE_DOCX, FILE_IMAGE],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_SINGLE,
            P_INPUT_2_EMPTY,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_MULTI,
            P_INPUT_2_EMPTY,
            200,
        ),
    ],
)
def test_process_file_5(
    test_files, response_type, response_schema, m_input1, m_input2, expected_status
):
    response = client.post(
        PROCESS_FILE_5_ROUTE,
        files=convert_files_for_api(test_files),
        data={**response_schema, **m_input1, **m_input2, "output_format": response_type},
        **generate_header_kwargs(response_type)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_file_5(
            test_files, response, response_schema, response_type, m_input1, m_input2
        )


@pytest.mark.parametrize(
    "mimetype,filename,expected_status",
    [
        ("application/epub+zip", "file.epub", 200),
        ("application/json", "file.json", 200),
        ("application/msword", "file.doc", 200),
        ("application/pdf", "file.pdf", 200),
        ("application/vnd.ms-powerpoint", "file.ppt", 200),
        ("application/vnd.ms-excel", "file.xls", 400),
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
        (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "file.xlsx",
            400,
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
        PROCESS_FILE_1_ROUTE,
        files=[("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype))],
    )
    assert response.status_code == expected_status

    # Multiple files
    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[
            ("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype)),
            ("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype)),
        ],
    )
    assert response.status_code == expected_status

    # One file (in an api that supports text files)
    response = client.post(
        PROCESS_FILE_TEXT_1_ROUTE,
        files=[
            ("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype)),
        ],
    )
    assert response.status_code == expected_status

    # Multiple files (in an api that supports text files)
    response = client.post(
        PROCESS_FILE_TEXT_1_ROUTE,
        files=[
            ("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype)),
            ("files", ("example-filename", open(FILE_DOCX, "rb"), mimetype)),
        ],
    )
    assert response.status_code == expected_status

    # If the client doesn't set a mimetype, we may just see application/octet-stream
    # Here we fall back to the file extension
    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (filename, open(FILE_DOCX, "rb"), "application/octet-stream"))],
    )
    assert response.status_code == expected_status


def test_reconfigure_supported_mimetypes():
    """
    Verify that we can change the supported mimetype list via env variable
    """
    client = TestClient(app)

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_DOCX, open(FILE_DOCX, "rb"), FILENAME_FORMATS[FILE_DOCX]))],
    )
    assert response.status_code == 200

    os.environ["UNSTRUCTURED_ALLOWED_MIMETYPES"] = "image/jpeg"

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_DOCX, open(FILE_DOCX, "rb"), FILENAME_FORMATS[FILE_DOCX]))],
    )
    assert response.status_code == 400

    response = client.post(
        PROCESS_FILE_1_ROUTE,
        files=[("files", (FILE_DOCX, open(FILE_IMAGE, "rb"), FILENAME_FORMATS[FILE_IMAGE]))],
    )
    assert response.status_code == 200

    del os.environ["UNSTRUCTURED_ALLOWED_MIMETYPES"]
