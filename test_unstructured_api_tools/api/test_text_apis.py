import json
from base64 import b64decode

import pytest
from fastapi.testclient import TestClient
from prepline_test_project.api.app import app
from requests_toolbelt.multipart import decoder

from test_unstructured_api_tools.api.functions_and_variables import (
    FILE_TXT_1,
    FILE_TXT_2,
    convert_text_files_for_api,
    FILENAME_LENGTHS,
    P_INPUT_1_SINGLE,
    P_INPUT_1_MULTI,
    P_INPUT_1_EMPTY,
    P_INPUT_2_SINGLE,
    P_INPUT_2_MULTI,
    P_INPUT_2_EMPTY,
    JSON,
    MIXED,
    TEXT_CSV,
    RESPONSE_SCHEMA_ISD,
    RESPONSE_SCHEMA_LABELSTUDIO,
    generate_header_kwargs,
    GZIP_FILE_TXT_1,
    GZIP_FILE_TXT_2,
    FILE_MARKDOWN,
    FILENAME_FORMATS,
)

# accepts: text files
PROCESS_TEXT_1_ROUTE = ["/test-project/v1.2.3/process-text-1", "/test-project/v1/process-text-1"]

# accepts: text files, input1, input2
PROCESS_TEXT_2_ROUTE = ["/test-project/v1.2.3/process-text-2", "/test-project/v1/process-text-2"]

# accepts: text files, response_type
PROCESS_TEXT_3_ROUTE = ["/test-project/v1.2.3/process-text-3", "/test-project/v1/process-text-3"]

# accepts: text files, response_type, response_schema
PROCESS_TEXT_4_ROUTE = ["/test-project/v1.2.3/process-text-4", "/test-project/v1/process-text-4"]

client = TestClient(app)


def _assert_response_for_process_text_1(test_files, response, response_type, gz_content_type):
    def _json_for_one_file(test_file):
        if test_file.endswith(".gz"):
            test_file = test_file[:-3]
        with open(test_file, "r") as file:
            return {
                "silly_result": " : ".join([str(FILENAME_LENGTHS[test_file]), str(file.read())])
            }

    if response_type in [JSON, TEXT_CSV]:
        if len(test_files) == 1:
            assert response.json() == _json_for_one_file(test_files[0])
        else:
            assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]
    elif response_type == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


def _assert_response_for_process_text_2(test_files, response, m_input1, m_input2, response_type):
    def _json_for_one_file(test_file):
        if test_file.endswith(".gz"):
            test_file = test_file[:-3]
        with open(test_file, "r") as file:
            return {
                "silly_result": " : ".join(
                    [
                        str(FILENAME_LENGTHS[test_file]),
                        str(file.read()),
                        str(m_input1.get("input1", None)),
                        str(m_input2.get("input2", None)),
                    ]
                )
            }

    if response_type in [JSON, TEXT_CSV]:
        if len(test_files) == 1:
            assert response.json() == _json_for_one_file(test_files[0])
        else:
            assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]
    elif response_type == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


def _assert_response_for_process_text_3(test_files, response, response_type=TEXT_CSV):
    def _json_for_one_file(test_file):
        if test_file.endswith(".gz"):
            test_file = test_file[:-3]
        with open(test_file, "r") as file:
            return {
                "silly_result": " : ".join(
                    [str(FILENAME_LENGTHS[test_file]), str(file.read()), str(response_type)]
                )
            }

    if response_type in [JSON, TEXT_CSV]:
        if len(test_files) == 1:
            assert response.json() == _json_for_one_file(test_files[0])
        else:
            assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]
    elif response_type == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


def _assert_response_for_process_text_4(test_files, response, response_type, response_schema):
    def _json_for_one_file(test_file):
        if test_file.endswith(".gz"):
            test_file = test_file[:-3]
        with open(test_file, "r") as file:
            return {
                "silly_result": " : ".join(
                    [
                        str(FILENAME_LENGTHS[test_file]),
                        str(file.read()),
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
    elif response_type == MIXED:
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            json_part = json.loads(b64decode(part.content))
            assert json_part == _json_for_one_file(test_files[i])


@pytest.mark.parametrize(
    "test_files,"
    "expected_status,"
    "use_octet_stream_type,"
    "allowed_mimetypes_str,"
    "response_type,"
    "gz_content_type",
    [
        ([FILE_TXT_1], 200, False, None, JSON, None),
        ([FILE_TXT_2], 200, False, None, JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], 200, False, None, JSON, None),
        ([FILE_MARKDOWN], 200, False, None, JSON, None),
        ([FILE_MARKDOWN, FILE_MARKDOWN], 200, True, None, JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], 200, False, FILENAME_FORMATS[FILE_TXT_1], JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], 400, False, FILENAME_FORMATS[FILE_MARKDOWN], JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], 200, False, None, MIXED, None),
        ([FILE_TXT_1, FILE_TXT_2], 406, False, None, TEXT_CSV, None),
        ([], 400, False, None, JSON, None),
        ([GZIP_FILE_TXT_1], 200, False, None, JSON, None),
        ([GZIP_FILE_TXT_1], 200, False, None, JSON, FILENAME_FORMATS[FILE_TXT_1]),
    ],
)
def test_process_text_1(
    test_files,
    expected_status,
    use_octet_stream_type,
    allowed_mimetypes_str,
    response_type,
    gz_content_type,
    monkeypatch,
):
    if allowed_mimetypes_str:
        monkeypatch.setenv("UNSTRUCTURED_ALLOWED_MIMETYPES", allowed_mimetypes_str)
    else:
        monkeypatch.delenv("UNSTRUCTURED_ALLOWED_MIMETYPES", False)
    for endpoint in PROCESS_TEXT_1_ROUTE:
        response = client.post(
            endpoint,
            files=convert_text_files_for_api(test_files, use_octet_stream_type),
            data={"output_format": response_type, "gz_uncompressed_content_type": gz_content_type},
            **generate_header_kwargs(response_type),
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_text_1(
                test_files, response, response_type, gz_content_type
            )


@pytest.mark.parametrize(
    "test_files,"
    "m_input1,"
    "m_input2,"
    "expected_status,"
    "use_octet_stream_type,"
    "allowed_mimetypes_str,"
    "response_type,"
    "gz_content_type",
    [
        ([FILE_TXT_1], P_INPUT_1_SINGLE, P_INPUT_2_SINGLE, 200, False, None, JSON, None),
        ([FILE_TXT_1], P_INPUT_1_EMPTY, P_INPUT_2_SINGLE, 200, False, None, JSON, None),
        ([FILE_TXT_1], P_INPUT_1_EMPTY, P_INPUT_2_MULTI, 200, False, None, JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], P_INPUT_1_EMPTY, P_INPUT_2_EMPTY, 200, False, None, JSON, None),
        ([FILE_TXT_1, FILE_TXT_2], P_INPUT_1_SINGLE, P_INPUT_2_EMPTY, 200, False, None, JSON, None),
        (
            [FILE_TXT_1, FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
            False,
            None,
            JSON,
            None,
        ),
        ([FILE_TXT_1, FILE_TXT_2], P_INPUT_1_MULTI, P_INPUT_2_MULTI, 200, False, None, JSON, None),
        ([GZIP_FILE_TXT_1], P_INPUT_1_SINGLE, P_INPUT_2_SINGLE, 200, False, None, JSON, None),
        ([GZIP_FILE_TXT_1], P_INPUT_1_EMPTY, P_INPUT_2_SINGLE, 200, False, None, JSON, None),
        ([GZIP_FILE_TXT_1], P_INPUT_1_EMPTY, P_INPUT_2_MULTI, 200, False, None, JSON, None),
        (
            [GZIP_FILE_TXT_1, FILE_TXT_2],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
            False,
            None,
            JSON,
            None,
        ),
        (
            [FILE_TXT_1, GZIP_FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_EMPTY,
            200,
            False,
            None,
            JSON,
            None,
        ),
        (
            [GZIP_FILE_TXT_1, GZIP_FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
            False,
            None,
            JSON,
            None,
        ),
        (
            [GZIP_FILE_TXT_1, GZIP_FILE_TXT_2],
            P_INPUT_1_MULTI,
            P_INPUT_2_MULTI,
            200,
            False,
            None,
            JSON,
            None,
        ),
        ([FILE_MARKDOWN], P_INPUT_1_EMPTY, P_INPUT_2_EMPTY, 200, False, None, JSON, None),
        (
            [FILE_MARKDOWN, FILE_TXT_1],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
            True,
            None,
            JSON,
            None,
        ),
        (
            [FILE_MARKDOWN],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
            False,
            FILENAME_FORMATS[FILE_MARKDOWN],
            JSON,
            None,
        ),
        (
            [FILE_MARKDOWN, FILE_TXT_1],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            400,
            False,
            FILENAME_FORMATS[FILE_TXT_1],
            JSON,
            None,
        ),
        (
            [FILE_TXT_1, FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
            False,
            None,
            MIXED,
            None,
        ),
        (
            [GZIP_FILE_TXT_1, FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
            False,
            None,
            MIXED,
            None,
        ),
        (
            [FILE_TXT_1, FILE_TXT_2],
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            406,
            False,
            None,
            TEXT_CSV,
            None,
        ),
        ([], P_INPUT_1_EMPTY, P_INPUT_2_EMPTY, 400, False, None, JSON, None),
        (
            [GZIP_FILE_TXT_1],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
            False,
            None,
            JSON,
            FILENAME_FORMATS[FILE_TXT_1],
        ),
        (
            [GZIP_FILE_TXT_2],
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
            False,
            None,
            JSON,
            FILENAME_FORMATS[FILE_TXT_1],
        ),
    ],
)
def test_process_text_2(
    test_files,
    m_input1,
    m_input2,
    expected_status,
    use_octet_stream_type,
    allowed_mimetypes_str,
    response_type,
    gz_content_type,
    monkeypatch,
):
    if allowed_mimetypes_str:
        monkeypatch.setenv("UNSTRUCTURED_ALLOWED_MIMETYPES", allowed_mimetypes_str)
    else:
        monkeypatch.delenv("UNSTRUCTURED_ALLOWED_MIMETYPES", False)
    for endpoint in PROCESS_TEXT_2_ROUTE:
        response = client.post(
            endpoint,
            files=convert_text_files_for_api(test_files, use_octet_stream_type),
            data={
                **m_input1,
                **m_input2,
                "output_format": response_type,
                "gz_uncompressed_content_type": gz_content_type,
            },
            **generate_header_kwargs(response_type),
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_text_2(
                test_files, response, m_input1, m_input2, response_type
            )


@pytest.mark.parametrize(
    "test_files,"
    "response_type,"
    "expected_status,"
    "use_octet_stream_type,"
    "allowed_mimetypes_str,"
    "gz_content_type",
    [
        ([FILE_TXT_1], JSON, 200, False, None, None),
        ([GZIP_FILE_TXT_1], JSON, 200, False, None, None),
        ([FILE_TXT_1], MIXED, 200, False, None, None),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_TXT_1], TEXT_CSV, 200, False, None, None, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_TXT_1], None, 200, False, None, None, marks=pytest.mark.xfail),
        ([FILE_TXT_1, FILE_TXT_2], JSON, 200, False, None, None),
        ([FILE_TXT_1, FILE_TXT_2], MIXED, 200, False, None, None),
        ([GZIP_FILE_TXT_1, FILE_TXT_2], JSON, 200, False, None, None),
        ([FILE_TXT_1, GZIP_FILE_TXT_2], MIXED, 200, False, None, None),
        ([GZIP_FILE_TXT_1, GZIP_FILE_TXT_2], MIXED, 200, False, None, None),
        # endpoint fails because media type text/csv should have response type str
        pytest.param(
            [FILE_TXT_1, FILE_TXT_2], TEXT_CSV, 200, False, None, None, marks=pytest.mark.xfail
        ),
        pytest.param(
            [GZIP_FILE_TXT_1, FILE_TXT_2], TEXT_CSV, 200, False, None, None, marks=pytest.mark.xfail
        ),
        pytest.param(
            [FILE_TXT_1, GZIP_FILE_TXT_2], TEXT_CSV, 200, False, None, None, marks=pytest.mark.xfail
        ),
        pytest.param(
            [GZIP_FILE_TXT_1, GZIP_FILE_TXT_2],
            TEXT_CSV,
            200,
            False,
            None,
            None,
            marks=pytest.mark.xfail,
        ),
        ([FILE_TXT_1, FILE_TXT_2], None, 406, False, None, None),
        ([FILE_TXT_2], JSON, 200, False, None, None),
        ([GZIP_FILE_TXT_2], JSON, 200, False, None, None),
        ([FILE_TXT_2], MIXED, 200, False, None, None),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_TXT_2], TEXT_CSV, 200, False, None, None, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_TXT_2], None, 200, False, None, None, marks=pytest.mark.xfail),
        ([FILE_TXT_2, FILE_MARKDOWN], None, 406, True, None, None),
        ([FILE_TXT_2, FILE_TXT_1], None, 406, False, FILENAME_FORMATS[FILE_TXT_1], None),
        ([FILE_TXT_2, FILE_MARKDOWN], None, 406, False, FILENAME_FORMATS[FILE_TXT_1], None),
        ([], None, 400, False, None, None),
        ([GZIP_FILE_TXT_1], JSON, 200, False, None, FILENAME_FORMATS[FILE_TXT_1]),
    ],
)
def test_process_text_3(
    test_files,
    response_type,
    expected_status,
    use_octet_stream_type,
    allowed_mimetypes_str,
    gz_content_type,
    monkeypatch,
):
    if allowed_mimetypes_str:
        monkeypatch.setenv("UNSTRUCTURED_ALLOWED_MIMETYPES", allowed_mimetypes_str)
    else:
        monkeypatch.delenv("UNSTRUCTURED_ALLOWED_MIMETYPES", False)
    for endpoint in PROCESS_TEXT_3_ROUTE:
        response = client.post(
            endpoint,
            files=convert_text_files_for_api(test_files, use_octet_stream_type),
            data={"output_format": response_type, "gz_uncompressed_content_type": gz_content_type},
            **generate_header_kwargs(response_type),
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_text_3(test_files, response, response_type)


@pytest.mark.parametrize(
    "test_files,"
    "response_type,"
    "response_schema,"
    "expected_status,"
    "use_octet_stream_type,"
    "allowed_mimetypes_str,"
    "gz_content_type",
    [
        ([FILE_TXT_1], JSON, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([FILE_TXT_1], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200, False, None, None),
        ([FILE_TXT_1, FILE_TXT_2], JSON, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([FILE_TXT_1, FILE_TXT_2], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200, False, None, None),
        ([FILE_TXT_1, FILE_TXT_2], MIXED, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([FILE_TXT_1, FILE_TXT_2], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200, False, None, None),
        ([GZIP_FILE_TXT_1], JSON, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([GZIP_FILE_TXT_1], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200, False, None, None),
        ([GZIP_FILE_TXT_1, FILE_TXT_2], JSON, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([FILE_TXT_1, GZIP_FILE_TXT_2], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200, False, None, None),
        ([GZIP_FILE_TXT_1, GZIP_FILE_TXT_2], MIXED, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        (
            [GZIP_FILE_TXT_1, GZIP_FILE_TXT_2],
            MIXED,
            RESPONSE_SCHEMA_LABELSTUDIO,
            200,
            False,
            None,
            None,
        ),
        ([GZIP_FILE_TXT_1], TEXT_CSV, RESPONSE_SCHEMA_LABELSTUDIO, 406, False, None, None),
        ([FILE_MARKDOWN, FILE_TXT_1], JSON, RESPONSE_SCHEMA_ISD, 200, True, None, None),
        (
            [GZIP_FILE_TXT_1, FILE_TXT_2],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            200,
            False,
            FILENAME_FORMATS[FILE_TXT_1],
            None,
        ),
        (
            [FILE_MARKDOWN, FILE_TXT_2],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            400,
            False,
            FILENAME_FORMATS[FILE_TXT_1],
            None,
        ),
        ([FILE_TXT_1, FILE_TXT_2], TEXT_CSV, RESPONSE_SCHEMA_ISD, 406, False, None, None),
        ([FILE_TXT_1], MIXED, RESPONSE_SCHEMA_ISD, 200, False, None, None),
        ([], JSON, RESPONSE_SCHEMA_ISD, 400, False, None, None),
        (
            [GZIP_FILE_TXT_1],
            JSON,
            RESPONSE_SCHEMA_ISD,
            200,
            False,
            None,
            FILENAME_FORMATS[FILE_TXT_1],
        ),
    ],
)
def test_process_text_4(
    test_files,
    response_type,
    response_schema,
    expected_status,
    use_octet_stream_type,
    allowed_mimetypes_str,
    gz_content_type,
    monkeypatch,
):
    if allowed_mimetypes_str:
        monkeypatch.setenv("UNSTRUCTURED_ALLOWED_MIMETYPES", allowed_mimetypes_str)
    else:
        monkeypatch.delenv("UNSTRUCTURED_ALLOWED_MIMETYPES", False)
    for endpoint in PROCESS_TEXT_4_ROUTE:
        response = client.post(
            endpoint,
            files=convert_text_files_for_api(test_files, use_octet_stream_type),
            data={
                **response_schema,
                "output_format": response_type,
                "gz_uncompressed_content_type": gz_content_type,
            },
            **generate_header_kwargs(response_type),
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_text_4(
                test_files, response, response_type, response_schema
            )
