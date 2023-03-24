import json
from base64 import b64decode

import pytest
from fastapi.testclient import TestClient
from prepline_test_project.api.app import app
from requests_toolbelt.multipart import decoder

from test_unstructured_api_tools.api.functions_and_variables import (
    FILE_DOCX,
    FILE_IMAGE,
    FILE_TXT_1,
    FILE_TXT_2,
    convert_files_for_api,
    convert_text_files_for_api,
    P_INPUT_1_EMPTY,
    P_INPUT_1_SINGLE,
    P_INPUT_1_MULTI,
    P_INPUT_2_SINGLE,
    P_INPUT_2_MULTI,
    P_INPUT_2_EMPTY,
    JSON,
    MIXED,
    RESPONSE_SCHEMA_ISD,
    RESPONSE_SCHEMA_LABELSTUDIO,
    FILENAME_FORMATS,
    generate_header_kwargs,
)

# accepts: files, text files
PROCESS_FILE_TEXT_1_ROUTE = [
    "/test-project/v1.2.3/process-text-file-1",
    "/test-project/v1/process-text-file-1",
]

# accepts: files, text files, response_type, input2
PROCESS_FILE_TEXT_2_ROUTE = [
    "/test-project/v1.2.3/process-text-file-2",
    "/test-project/v1/process-text-file-2",
]

# accepts: files, text files, response_type, response_schema
PROCESS_FILE_TEXT_3_ROUTE = [
    "/test-project/v1.2.3/process-text-file-3",
    "/test-project/v1/process-text-file-3",
]

# accepts: files, text files, response_type, response_schema, input1, input2
PROCESS_FILE_TEXT_4_ROUTE = [
    "/test-project/v1.2.3/process-text-file-4",
    "/test-project/v1/process-text-file-4",
]

client = TestClient(app)


def _assert_response_for_process_file_text_1(test_files, test_files_text, response):
    def _json_for_one_file(test_file=None, test_text_file=None):
        text = None
        file_read = None
        filename = test_file
        file_content_type = None

        if test_text_file:
            with open(test_text_file, "r") as file:
                text = file.read()
        if test_file:
            with open(test_file, "rb") as file:
                file_read = file.read()
                file_content_type = FILENAME_FORMATS[test_file]

        return {
            "silly_result": " : ".join(
                [
                    str(len(text if text else "")),
                    str(text),
                    str(len(file_read) if file_read else None),
                    str(filename),
                    str(file_content_type),
                ]
            )
        }

    test_files_arr = []
    test_text_files_arr = []
    if len(test_files) > 0:
        test_files_arr = [_json_for_one_file(test_file=test_file) for test_file in test_files]
    if len(test_files_text) > 0:
        test_text_files_arr = [
            _json_for_one_file(test_text_file=test_file) for test_file in test_files_text
        ]
    assert response.json() == test_text_files_arr + test_files_arr


def _assert_response_for_process_file_text_2(
    test_files, test_files_text, response_type, m_input2, response
):
    def _json_for_one_file(test_file=None, test_text_file=None):
        text = None
        file_read = None
        filename = test_file
        file_content_type = None

        if test_text_file:
            with open(test_text_file, "r") as file:
                text = file.read()
        if test_file:
            with open(test_file, "rb") as file:
                file_read = file.read()
                file_content_type = FILENAME_FORMATS[test_file]

        return {
            "silly_result": " : ".join(
                [
                    str(len(text if text else "")),
                    str(text),
                    str(len(file_read) if file_read else None),
                    str(filename),
                    str(file_content_type),
                    str(response_type),
                    str(m_input2.get("input2", None)),
                ]
            )
        }

    test_files_arr = []
    test_text_files_arr = []
    if len(test_files) > 0:
        test_files_arr = [_json_for_one_file(test_file=test_file) for test_file in test_files]
    if len(test_files_text) > 0:
        test_text_files_arr = [
            _json_for_one_file(test_text_file=test_file) for test_file in test_files_text
        ]
    if response_type == JSON:
        assert response.json() == test_text_files_arr + test_files_arr
    elif response_type == MIXED:
        response_array = []
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            response_array.append(json.loads(b64decode(part.content)))
        assert response_array == test_text_files_arr + test_files_arr


def _assert_response_for_process_file_text_3(
    test_files, test_files_text, response_type, response_schema, response
):
    def _json_for_one_file(test_file=None, test_text_file=None):
        text = None
        file_read = None
        filename = test_file
        file_content_type = None

        if test_text_file:
            with open(test_text_file, "r") as file:
                text = file.read()
        if test_file:
            with open(test_file, "rb") as file:
                file_read = file.read()
                file_content_type = FILENAME_FORMATS[test_file]

        return {
            "silly_result": " : ".join(
                [
                    str(len(text if text else "")),
                    str(text),
                    str(len(file_read) if file_read else None),
                    str(filename),
                    str(file_content_type),
                    str(response_type),
                    str(response_schema["output_schema"]),
                ]
            )
        }

    test_files_arr = []
    test_text_files_arr = []
    if len(test_files) > 0:
        test_files_arr = [_json_for_one_file(test_file=test_file) for test_file in test_files]
    if len(test_files_text) > 0:
        test_text_files_arr = [
            _json_for_one_file(test_text_file=test_file) for test_file in test_files_text
        ]
    if response_type == JSON:
        assert response.json() == test_text_files_arr + test_files_arr
    elif response_type == MIXED:
        response_array = []
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            response_array.append(json.loads(b64decode(part.content)))
        assert response_array == test_text_files_arr + test_files_arr


def _assert_response_for_process_file_text_4(
    test_files, test_files_text, response_type, response_schema, m_input1, m_input2, response
):
    def _json_for_one_file(test_file=None, test_text_file=None):
        text = None
        file_read = None
        filename = test_file
        file_content_type = None

        if test_text_file:
            with open(test_text_file, "r") as file:
                text = file.read()
        if test_file:
            with open(test_file, "rb") as file:
                file_read = file.read()
                file_content_type = FILENAME_FORMATS[test_file]

        return {
            "silly_result": " : ".join(
                [
                    str(len(text if text else "")),
                    str(text),
                    str(len(file_read) if file_read else None),
                    str(filename),
                    str(file_content_type),
                    str(response_type),
                    str(response_schema["output_schema"]),
                    str(m_input1.get("input1", None)),
                    str(m_input2.get("input2", None)),
                ]
            )
        }

    test_files_arr = []
    test_text_files_arr = []
    if len(test_files) > 0:
        test_files_arr = [_json_for_one_file(test_file=test_file) for test_file in test_files]
    if len(test_files_text) > 0:
        test_text_files_arr = [
            _json_for_one_file(test_text_file=test_file) for test_file in test_files_text
        ]
    if response_type == JSON:
        assert response.json() == test_text_files_arr + test_files_arr
    elif response_type == MIXED:
        response_array = []
        data = decoder.MultipartDecoder.from_response(response)
        for i, part in enumerate(data.parts):
            response_array.append(json.loads(b64decode(part.content)))
        assert response_array == test_text_files_arr + test_files_arr


@pytest.mark.parametrize(
    "test_files,test_files_text,expected_status",
    [
        ([FILE_DOCX], [FILE_TXT_1], 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_2], 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1, FILE_TXT_2], 200),
        ([FILE_DOCX], [FILE_TXT_2], 200),
        ([FILE_IMAGE], [FILE_TXT_2], 200),
    ],
)
def test_process_file_text_1(test_files, test_files_text, expected_status):
    for endpoint in PROCESS_FILE_TEXT_1_ROUTE:
        response = client.post(
            endpoint,
            files=convert_files_for_api(test_files) + convert_text_files_for_api(test_files_text),
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_file_text_1(test_files, test_files_text, response)


@pytest.mark.parametrize(
    "test_files,test_files_text,response_type,m_input2,expected_status",
    [
        ([FILE_DOCX], [FILE_TXT_1], JSON, P_INPUT_2_MULTI, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], JSON, P_INPUT_2_MULTI, 200),
        ([FILE_DOCX], [FILE_TXT_1], MIXED, P_INPUT_2_SINGLE, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], MIXED, P_INPUT_2_EMPTY, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1, FILE_TXT_2], JSON, P_INPUT_2_MULTI, 200),
        ([FILE_DOCX], [FILE_TXT_1, FILE_TXT_2], JSON, P_INPUT_2_SINGLE, 200),
        ([FILE_IMAGE], [FILE_TXT_1], JSON, P_INPUT_2_MULTI, 200),
        ([FILE_IMAGE], [FILE_TXT_1], MIXED, P_INPUT_2_EMPTY, 200),
    ],
)
def test_process_file_text_2(test_files, test_files_text, response_type, m_input2, expected_status):
    for endpoint in PROCESS_FILE_TEXT_2_ROUTE:
        response = client.post(
            endpoint,
            files=convert_files_for_api(test_files) + convert_text_files_for_api(test_files_text),
            data={**m_input2, "output_format": response_type},
            **generate_header_kwargs(response_type)
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_file_text_2(
                test_files, test_files_text, response_type, m_input2, response
            )


@pytest.mark.parametrize(
    "test_files,test_files_text,response_type,response_schema,expected_status",
    [
        ([FILE_DOCX], [FILE_TXT_1], JSON, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX], [FILE_TXT_1], MIXED, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], JSON, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], MIXED, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_DOCX], [FILE_TXT_1], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_DOCX], [FILE_TXT_1], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_DOCX, FILE_IMAGE], [FILE_TXT_1, FILE_TXT_2], MIXED, RESPONSE_SCHEMA_ISD, 200),
        (
            [FILE_DOCX, FILE_IMAGE],
            [FILE_TXT_1, FILE_TXT_2],
            MIXED,
            RESPONSE_SCHEMA_LABELSTUDIO,
            200,
        ),
    ],
)
def test_process_file_text_3(
    test_files, test_files_text, response_type, response_schema, expected_status
):
    for endpoint in PROCESS_FILE_TEXT_3_ROUTE:
        response = client.post(
            endpoint,
            files=convert_files_for_api(test_files) + convert_text_files_for_api(test_files_text),
            data={**response_schema, "output_format": response_type},
            **generate_header_kwargs(response_type)
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_file_text_3(
                test_files, test_files_text, response_type, response_schema, response
            )


@pytest.mark.parametrize(
    "test_files,test_files_text,response_type,response_schema,m_input1,m_input2,expected_status",
    [
        (
            [FILE_DOCX],
            [FILE_TXT_1],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_MULTI,
            P_INPUT_2_SINGLE,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            [FILE_TXT_1],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
        ),
        (
            [FILE_DOCX],
            [FILE_TXT_1, FILE_TXT_2],
            JSON,
            RESPONSE_SCHEMA_ISD,
            P_INPUT_1_MULTI,
            P_INPUT_2_MULTI,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            [FILE_TXT_1, FILE_TXT_2],
            JSON,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_MULTI,
            P_INPUT_2_SINGLE,
            200,
        ),
        (
            [FILE_DOCX],
            [FILE_TXT_1],
            MIXED,
            RESPONSE_SCHEMA_ISD,
            P_INPUT_1_MULTI,
            P_INPUT_2_EMPTY,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            [FILE_TXT_1],
            MIXED,
            RESPONSE_SCHEMA_LABELSTUDIO,
            P_INPUT_1_SINGLE,
            P_INPUT_2_SINGLE,
            200,
        ),
        (
            [FILE_DOCX],
            [FILE_TXT_1, FILE_TXT_2],
            MIXED,
            RESPONSE_SCHEMA_ISD,
            P_INPUT_1_EMPTY,
            P_INPUT_2_EMPTY,
            200,
        ),
        (
            [FILE_DOCX, FILE_IMAGE],
            [FILE_TXT_1, FILE_TXT_2],
            MIXED,
            RESPONSE_SCHEMA_ISD,
            P_INPUT_1_MULTI,
            P_INPUT_2_MULTI,
            200,
        ),
    ],
)
def test_process_file_text_4(
    test_files, test_files_text, response_type, response_schema, m_input1, m_input2, expected_status
):
    for endpoint in PROCESS_FILE_TEXT_4_ROUTE:
        response = client.post(
            endpoint,
            files=convert_files_for_api(test_files) + convert_text_files_for_api(test_files_text),
            data={**m_input1, **m_input2, **response_schema, "output_format": response_type},
            **generate_header_kwargs(response_type)
        )
        assert response.status_code == expected_status
        if response.status_code == 200:
            _assert_response_for_process_file_text_4(
                test_files,
                test_files_text,
                response_type,
                response_schema,
                m_input1,
                m_input2,
                response,
            )
