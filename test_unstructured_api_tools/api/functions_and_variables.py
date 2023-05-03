FILE_DOCX = "test_unstructured_api_tools/api/fixtures/fake.docx"
FILE_IMAGE = "test_unstructured_api_tools/api/fixtures/example.jpg"
FILE_TXT_1 = "test_unstructured_api_tools/api/fixtures/text_file.txt"
FILE_TXT_2 = "test_unstructured_api_tools/api/fixtures/text_file_2.txt"
FILE_MARKDOWN = "test_unstructured_api_tools/api/fixtures/markdown.md"
FILE_MSG = "test_unstructured_api_tools/api/fixtures/fake-email.msg"
FILE_JSON = "test_unstructured_api_tools/api/fixtures/spring-weather.html.json"    

GZIP_FILE_DOCX = "test_unstructured_api_tools/api/fixtures/fake.docx.gz"
GZIP_FILE_IMAGE = "test_unstructured_api_tools/api/fixtures/example.jpg.gz"
GZIP_FILE_TXT_1 = "test_unstructured_api_tools/api/fixtures/text_file.txt.gz"
GZIP_FILE_TXT_2 = "test_unstructured_api_tools/api/fixtures/text_file_2.txt.gz"

FILENAME_LENGTHS = {
    FILE_DOCX: 36602,
    GZIP_FILE_DOCX: 36602,
    FILE_IMAGE: 32764,
    GZIP_FILE_IMAGE: 32764,
    FILE_TXT_1: 26,
    GZIP_FILE_TXT_1: 26,
    FILE_TXT_2: 30,
    GZIP_FILE_TXT_2: 30,
    FILE_MARKDOWN: 91,
    FILE_MSG: 11776,
    FILE_JSON: 13151,
    
}
FILENAME_FORMATS = {
    FILE_DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    FILE_IMAGE: "image/jpeg",
    FILE_TXT_1: "text/plain",
    FILE_TXT_2: "text/plain",
    GZIP_FILE_DOCX: "application/gzip",
    GZIP_FILE_IMAGE: "application/gzip",
    GZIP_FILE_TXT_1: "application/gzip",
    GZIP_FILE_TXT_2: "application/gzip",
    FILE_MARKDOWN: "text/markdown",
    FILE_MSG: "message/rfc822",
    FILE_JSON: "application/json",
    "octet_stream": "application/octet-stream",
}

P_INPUT_1_SINGLE = {"input1": ["hi"]}
P_INPUT_1_MULTI = {"input1": ["hi", "water is better than ice"]}
P_INPUT_1_EMPTY = {"input1": []}
P_INPUT_2_SINGLE = {"input2": ["hello"]}
P_INPUT_2_MULTI = {"input2": ["hello", "earth is better than mars"]}
P_INPUT_2_EMPTY = {"input2": []}
P_INPUT_1_AND_2_MULTI = {"input2": ["hello", "earth is better than mars"], "input1": ["hi"]}

JSON = "application/json"
MIXED = "multipart/mixed"
TEXT_CSV = "text/csv"

RESPONSE_SCHEMA_ISD = {"output_schema": "isd"}
RESPONSE_SCHEMA_LABELSTUDIO = {"output_schema": "labelstudio"}


def convert_files_for_api(files, use_octet_stream_type=False):
    return [
        (
            "files",
            (
                test_file,
                open(test_file, "rb"),
                FILENAME_FORMATS["octet_stream" if use_octet_stream_type else test_file],
            ),
        )
        for test_file in files
    ]


def convert_text_files_for_api(files, use_octet_stream_type=False):
    return [
        (
            "text_files",
            (
                test_file,
                open(test_file, "rb"),
                FILENAME_FORMATS["octet_stream" if use_octet_stream_type else test_file],
            ),
        )
        for test_file in files
    ]


def generate_header_kwargs(value=None):
    return (
        {
            "headers": {
                "Accept": value,
            }
        }
        if value
        else {}
    )
