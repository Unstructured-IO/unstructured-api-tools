import json
from base64 import b64decode

import pytest
from fastapi.testclient import TestClient
from prepline_test_project.api.app import app
from requests_toolbelt.multipart import decoder

from test_unstructured_api_tools.api.functions_and_variables import (
    FILE_C,
    FILE_D,
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
)

PROCESS_TEXT_1_ROUTE = "/test-project/v1.2.3/process-text-1"
PROCESS_TEXT_2_ROUTE = "/test-project/v1.2.3/process-text-2"
PROCESS_TEXT_3_ROUTE = "/test-project/v1.2.3/process-text-3"
PROCESS_TEXT_4_ROUTE = "/test-project/v1.2.3/process-text-4"

client = TestClient(app)


def _assert_response_for_process_text_1(test_files, response):
    def _json_for_one_file(test_file):
        with open(test_file, "r") as file:
            return {
                "silly_result": " : ".join([str(FILENAME_LENGTHS[test_file]), str(file.read())])
            }

    if len(test_files) == 1:
        assert response.json() == _json_for_one_file(test_files[0])
    else:
        assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]


def _assert_response_for_process_text_2(test_files, response, m_input1, m_input2):
    def _json_for_one_file(test_file):
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

    if len(test_files) == 1:
        assert response.json() == _json_for_one_file(test_files[0])
    else:
        assert response.json() == [_json_for_one_file(test_file) for test_file in test_files]


def _assert_response_for_process_text_3(test_files, response, response_type=TEXT_CSV):
    def _json_for_one_file(test_file):
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
    "test_files,expected_status",
    [
        ([FILE_C], 200),
        ([FILE_D], 200),
        ([FILE_C, FILE_D], 200),
    ],
)
def test_process_text_1(test_files, expected_status):
    response = client.post(PROCESS_TEXT_1_ROUTE, files=convert_text_files_for_api(test_files))
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_text_1(test_files, response)


@pytest.mark.parametrize(
    "test_files,m_input1,m_input2,expected_status",
    [
        ([FILE_C], P_INPUT_1_SINGLE, P_INPUT_2_SINGLE, 200),
        ([FILE_C], P_INPUT_1_EMPTY, P_INPUT_2_SINGLE, 200),
        ([FILE_C], P_INPUT_1_EMPTY, P_INPUT_2_MULTI, 200),
        ([FILE_C, FILE_D], P_INPUT_1_EMPTY, P_INPUT_2_EMPTY, 200),
        ([FILE_C, FILE_D], P_INPUT_1_SINGLE, P_INPUT_2_EMPTY, 200),
        ([FILE_C, FILE_D], P_INPUT_1_SINGLE, P_INPUT_2_SINGLE, 200),
        ([FILE_C, FILE_D], P_INPUT_1_MULTI, P_INPUT_2_MULTI, 200),
    ],
)
def test_process_text_2(test_files, m_input1, m_input2, expected_status):
    response = client.post(
        PROCESS_TEXT_2_ROUTE,
        files=convert_text_files_for_api(test_files),
        data={**m_input1, **m_input2},
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_text_2(test_files, response, m_input1, m_input2)


@pytest.mark.parametrize(
    "test_files,response_type,expected_status",
    [
        ([FILE_C], JSON, 200),
        # endpoint doesn't accept mixed media type for one file
        pytest.param([FILE_C], MIXED, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_C], TEXT_CSV, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_C], None, 200, marks=pytest.mark.xfail),
        ([FILE_C, FILE_D], JSON, 200),
        ([FILE_C, FILE_D], MIXED, 200),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_C, FILE_D], TEXT_CSV, 200, marks=pytest.mark.xfail),
        ([FILE_C, FILE_D], None, 200),
        ([FILE_D], JSON, 200),
        # endpoint doesn't accept mixed media type for one file
        pytest.param([FILE_D], MIXED, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        pytest.param([FILE_D], TEXT_CSV, 200, marks=pytest.mark.xfail),
        # endpoint fails because media type text/csv should have response type str
        # because None response type has default text/csv value
        pytest.param([FILE_D], None, 200, marks=pytest.mark.xfail),
    ],
)
def test_process_text_3(test_files, response_type, expected_status):
    response = client.post(
        PROCESS_TEXT_3_ROUTE,
        files=convert_text_files_for_api(test_files),
        data={"output_format": response_type},
        **generate_header_kwargs(response_type)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_text_3(test_files, response, response_type)


@pytest.mark.parametrize(
    "test_files,response_type,response_schema,expected_status",
    [
        ([FILE_C], JSON, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_C], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_C, FILE_D], JSON, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_C, FILE_D], JSON, RESPONSE_SCHEMA_LABELSTUDIO, 200),
        ([FILE_C, FILE_D], MIXED, RESPONSE_SCHEMA_ISD, 200),
        ([FILE_C, FILE_D], MIXED, RESPONSE_SCHEMA_LABELSTUDIO, 200),
    ],
)
def test_process_text_4(test_files, response_type, response_schema, expected_status):
    response = client.post(
        PROCESS_TEXT_4_ROUTE,
        files=convert_text_files_for_api(test_files),
        data={**response_schema, "output_format": response_type},
        **generate_header_kwargs(response_type)
    )
    assert response.status_code == expected_status
    if response.status_code == 200:
        _assert_response_for_process_text_4(test_files, response, response_type, response_schema)
