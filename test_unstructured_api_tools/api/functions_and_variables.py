FILE_A = "test_unstructured_api_tools/api/fixtures/fake.docx"
FILE_B = "test_unstructured_api_tools/api/fixtures/example.jpg"
FILE_C = "test_unstructured_api_tools/api/fixtures/text_file.txt"
FILE_D = "test_unstructured_api_tools/api/fixtures/text_file_2.txt"

FILENAME_LENGTHS = {FILE_A: 36602, FILE_B: 32764, FILE_C: 26, FILE_D: 30}
FILENAME_FORMATS = {
    FILE_A: "application/vnd.openxmlformats",
    FILE_B: "image/jpeg",
    FILE_C: "text/plain",
    FILE_D: "text/plain",
}

P_INPUT_1_SINGLE = {"input1": ["hi"]}
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


def convert_files_for_api(files):
    return [
        ("files", (test_file, open(test_file, "rb"), FILENAME_FORMATS[test_file]))
        for test_file in files
    ]


def convert_text_files_for_api(files):
    return [
        ("text_files", (test_file, open(test_file, "rb"), FILENAME_FORMATS[test_file]))
        for test_file in files
    ]


def generate_header_kwargs(value=None):
    return {
        "headers": {
            "Accept": value,
        }
    } if value else {}
