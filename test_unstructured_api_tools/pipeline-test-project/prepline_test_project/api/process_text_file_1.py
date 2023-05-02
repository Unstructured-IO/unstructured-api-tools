#####################################################################
# THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS.
# DO NOT MODIFY DIRECTLY
#####################################################################

import io
import os
import gzip
import mimetypes
from typing import List, Union
from fastapi import status, FastAPI, File, Form, Request, UploadFile, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import json
from fastapi.responses import StreamingResponse
from starlette.datastructures import Headers
from starlette.types import Send
from base64 import b64encode
from typing import Optional, Mapping, Iterator, Tuple
import secrets


app = FastAPI()
router = APIRouter()


# pipeline-api
def pipeline_api(
    text,
    file=None,
    filename=None,
    file_content_type=None,
):
    return {
        "silly_result": " : ".join(
            [
                str(len(text if text else "")),
                str(text),
                str(len(file.read()) if file else None),
                str(filename),
                str(file_content_type),
            ]
        )
    }


def get_validated_mimetype(file):
    """
    Return a file's mimetype, either via the file.content_type or the mimetypes lib if that's too
    generic. If the user has set UNSTRUCTURED_ALLOWED_MIMETYPES, validate against this list and
    return HTTP 400 for an invalid type.
    """
    content_type = file.content_type
    if not content_type or content_type == "application/octet-stream":
        content_type = mimetypes.guess_type(str(file.filename))[0]

        # Markdown mimetype is too new for the library - just hardcode that one in for now
        if not content_type:
            if ".md" in file.filename:
                content_type = "text/markdown"
            if ".json" in file.filename:
                content_type = "application/json"
            if ".msg" in file.filename:
                content_type = "message/rfc82"

    allowed_mimetypes_str = os.environ.get("UNSTRUCTURED_ALLOWED_MIMETYPES")
    if allowed_mimetypes_str is not None:
        allowed_mimetypes = allowed_mimetypes_str.split(",")

        if content_type not in allowed_mimetypes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unable to process {file.filename}: "
                    f"File type {content_type} is not supported."
                ),
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
        part_headers = {"Content-Length": len(chunk), "Content-Transfer-Encoding": "base64"}
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
                {"type": "http.response.body", "body": self.build_part(chunk), "more_body": True}
            )

        await send({"type": "http.response.body", "body": b"", "more_body": False})


def ungz_file(file: UploadFile, gz_uncompressed_content_type=None) -> UploadFile:
    def return_content_type(filename):
        if gz_uncompressed_content_type:
            return gz_uncompressed_content_type
        else:
            return str(mimetypes.guess_type(filename)[0])

    filename = str(file.filename) if file.filename else ""
    if filename.endswith(".gz"):
        filename = filename[:-3]

    gzip_file = gzip.open(file.file).read()
    return UploadFile(
        file=io.BytesIO(gzip_file),
        size=len(gzip_file),
        filename=filename,
        headers=Headers({"content-type": return_content_type(filename)}),
    )


@router.post("/test-project/v1/process-text-file-1")
@router.post("/test-project/v1.2.3/process-text-file-1")
def pipeline_1(
    request: Request,
    gz_uncompressed_content_type: Optional[str] = Form(default=None),
    files: Union[List[UploadFile], None] = File(default=None),
    text_files: Union[List[UploadFile], None] = File(default=None),
):
    if files:
        for file_index in range(len(files)):
            if files[file_index].content_type == "application/gzip":
                files[file_index] = ungz_file(files[file_index], gz_uncompressed_content_type)

    if text_files:
        for file_index in range(len(text_files)):
            if text_files[file_index].content_type == "application/gzip":
                text_files[file_index] = ungz_file(text_files[file_index])

    content_type = request.headers.get("Accept")

    has_text = isinstance(text_files, list) and len(text_files)
    has_files = isinstance(files, list) and len(files)
    if not has_text and not has_files:
        raise HTTPException(
            detail='One of the request parameters "text_files" or "files" is required.\n',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    files_list: List = files or []
    text_files_list: List = text_files or []

    if len(files_list) or len(text_files_list):
        if all(
            [
                content_type,
                content_type
                not in [
                    "*/*",
                    "multipart/mixed",
                    "application/json",
                ],
                len(files_list) + len(text_files_list) > 1,
            ]
        ):
            raise HTTPException(
                detail=(
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
                    filename=file.filename,
                    file_content_type=file_content_type,
                )

                if is_multipart:
                    if type(response) not in [str, bytes]:
                        response = json.dumps(response)
                yield response

        if content_type == "multipart/mixed":
            return MultipartMixedResponse(
                response_generator(is_multipart=True),
            )
        else:
            return (
                list(response_generator(is_multipart=False))[0]
                if len(files_list + text_files_list) == 1
                else response_generator(is_multipart=False)
            )
    else:
        raise HTTPException(
            detail='Request parameters "files" or "text_files" are required.\n',
            status_code=status.HTTP_400_BAD_REQUEST,
        )


app.include_router(router)
