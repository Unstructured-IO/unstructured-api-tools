#####################################################################
# THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS.
# DO NOT MODIFY DIRECTLY
#####################################################################

import os
import mimetypes
from typing import List, Union
from fastapi import (
    status,
    FastAPI,
    File,
    Form,
    Request,
    UploadFile,
    APIRouter,
    HTTPException,
)
from fastapi.responses import PlainTextResponse
import json
from fastapi.responses import StreamingResponse
from starlette.types import Send
from base64 import b64encode
from typing import Optional, Mapping, Iterator, Tuple
import secrets


app = FastAPI()
router = APIRouter()

DEFAULT_MIMETYPES = "application/epub+zip,\
application/json,\
application/msword,\
application/pdf,\
application/vnd.ms-powerpoint,\
application/vnd.openxmlformats-officedocument.presentationml.presentation,\
application/vnd.openxmlformats-officedocument.wordprocessingml.document,\
image/jpeg,\
image/png,\
message/rfc822,\
text/html,\
text/markdown,\
text/plain,"


def is_expected_response_type(media_type, response_type):
    if media_type == "application/json" and response_type not in [dict, list]:
        return True
    elif media_type == "text/csv" and response_type != str:
        return True
    else:
        return False


# pipeline-api
def pipeline_api(
    text,
    file=None,
    filename=None,
    file_content_type=None,
    response_type="application/json",
    m_input2=[],
):
    return {
        "silly_result": " : ".join(
            [
                str(len(text if text else "")),
                str(text),
                str(len(file.read()) if file else None),
                str(filename),
                str(file_content_type),
                str(response_type),
                str(m_input2),
            ]
        )
    }


def get_validated_mimetype(file):
    """
    Return a file's mimetype, either via the file.content_type
    or the mimetypes lib if that's too generic. If this is not
    one of our allowed mimetypes, raise a HTTP 400 error.
    """
    allowed_mimetypes_str = os.environ.get(
        "UNSTRUCTURED_ALLOWED_MIMETYPES", DEFAULT_MIMETYPES
    )
    allowed_mimetypes = allowed_mimetypes_str.split(",")

    content_type = file.content_type
    if content_type == "application/octet-stream":
        content_type = mimetypes.guess_type(str(file.filename))[0]

        # Markdown mimetype is too new for the library - just hardcode that one in for now
        if not content_type and ".md" in file.filename:
            content_type = "text/markdown"

    if content_type not in allowed_mimetypes:
        raise HTTPException(
            status_code=400, detail=f"File type not supported: {file.filename}"
        )

    return content_type


class MultipartMixedResponse(StreamingResponse):
    CRLF = b"\r\n"

    def __init__(self, *args, content_type: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_type = content_type

    def init_headers(self, headers: Optional[Mapping[str, str]] = None) -> None:
        super().init_headers(headers)
        self.boundary_value = secrets.token_hex(16)
        content_type = f'multipart/mixed; boundary="{self.boundary_value}"'
        self.raw_headers.append((b"content-type", content_type.encode("latin-1")))

    @property
    def boundary(self):
        return b"--" + self.boundary_value.encode()

    def _build_part_headers(self, headers: dict) -> bytes:
        header_bytes = b""
        for header, value in headers.items():
            header_bytes += f"{header}: {value}".encode() + self.CRLF
        return header_bytes

    def build_part(self, chunk: bytes) -> bytes:
        part = self.boundary + self.CRLF
        part_headers = {
            "Content-Length": len(chunk),
            "Content-Transfer-Encoding": "base64",
        }
        if self.content_type is not None:
            part_headers["Content-Type"] = self.content_type
        part += self._build_part_headers(part_headers)
        part += self.CRLF + chunk + self.CRLF
        return part

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )
        async for chunk in self.body_iterator:
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(self.charset)
                chunk = b64encode(chunk)
            await send(
                {
                    "type": "http.response.body",
                    "body": self.build_part(chunk),
                    "more_body": True,
                }
            )

        await send({"type": "http.response.body", "body": b"", "more_body": False})


@router.post("/test-project/v1.2.3/process-text-file-2")
async def pipeline_1(
    request: Request,
    files: Union[List[UploadFile], None] = File(default=None),
    text_files: Union[List[UploadFile], None] = File(default=None),
    output_format: Union[str, None] = Form(default=None),
    input2: List[str] = Form(default=[]),
):
    content_type = request.headers.get("Accept")

    default_response_type = output_format or "application/json"
    if not content_type or content_type == "*/*" or content_type == "multipart/mixed":
        media_type = default_response_type
    else:
        media_type = content_type

    has_text = isinstance(text_files, list) and len(text_files)
    has_files = isinstance(files, list) and len(files)
    if not has_text and not has_files:
        return PlainTextResponse(
            content='One of the request parameters "text_files" or "files" is required.\n',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    files_list: List = files or []
    text_files_list: List = text_files or []

    if len(files_list) + len(text_files_list) > 1:
        if content_type and content_type not in [
            "*/*",
            "multipart/mixed",
            "application/json",
        ]:
            return PlainTextResponse(
                content=(
                    f"Conflict in media type {content_type}"
                    ' with response type "multipart/mixed".\n'
                ),
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )

        def response_generator(is_multipart):
            for text_file in text_files_list:
                text = text_file.file.read().decode("utf-8")

                response = pipeline_api(
                    text=text,
                    file=None,
                    m_input2=input2,
                    response_type=media_type,
                )
                if is_multipart:
                    if type(response) not in [str, bytes]:
                        response = json.dumps(response)
                yield response

            for file in files_list:
                _file = file.file

                file_content_type = get_validated_mimetype(file)

                response = pipeline_api(
                    text=None,
                    file=_file,
                    m_input2=input2,
                    response_type=media_type,
                    filename=file.filename,
                    file_content_type=file_content_type,
                )
                if is_multipart:
                    if type(response) not in [str, bytes]:
                        response = json.dumps(response)
                yield response

        if content_type == "multipart/mixed":
            return MultipartMixedResponse(
                response_generator(is_multipart=True), content_type=media_type
            )
        else:
            return response_generator(is_multipart=False)
    else:
        if has_text:
            text_file = text_files_list[0]
            text = text_file.file.read().decode("utf-8")
            response = pipeline_api(
                text=text,
                file=None,
                m_input2=input2,
                response_type=media_type,
            )
        elif has_files:
            file = files_list[0]
            _file = file.file

            file_content_type = get_validated_mimetype(file)

            response = pipeline_api(
                text=None,
                file=_file,
                m_input2=input2,
                response_type=media_type,
                filename=file.filename,
                file_content_type=file_content_type,
            )

        if is_expected_response_type(media_type, type(response)):
            return PlainTextResponse(
                content=(
                    f"Conflict in media type {media_type}"
                    f" with response type {type(response)}.\n"
                ),
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )
        valid_response_types = ["application/json", "text/csv", "*/*"]
        if media_type in valid_response_types:
            return response
        else:
            return PlainTextResponse(
                content=f"Unsupported media type {media_type}.\n",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )


@app.get("/healthcheck", status_code=status.HTTP_200_OK)
async def healthcheck(request: Request):
    return {"healthcheck": "HEALTHCHECK STATUS: EVERYTHING OK!"}


app.include_router(router)
