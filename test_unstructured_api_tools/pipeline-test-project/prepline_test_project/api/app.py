#####################################################################
# THIS FILE IS AUTOMATICALLY GENERATED BY UNSTRUCTURED API TOOLS.
# DO NOT MODIFY DIRECTLY
#####################################################################


from fastapi import FastAPI, Request, status
import logging
import os

from .process_file_1 import router as process_file_1_router
from .process_file_2 import router as process_file_2_router
from .process_file_3 import router as process_file_3_router
from .process_file_4 import router as process_file_4_router
from .process_file_5 import router as process_file_5_router
from .process_text_1 import router as process_text_1_router
from .process_text_2 import router as process_text_2_router
from .process_text_3 import router as process_text_3_router
from .process_text_4 import router as process_text_4_router
from .process_text_file_1 import router as process_text_file_1_router
from .process_text_file_2 import router as process_text_file_2_router
from .process_text_file_3 import router as process_text_file_3_router
from .process_text_file_4 import router as process_text_file_4_router


app = FastAPI(
    title="Unstructured Pipeline API",
    description="""""",
    version="1.0.0",
    docs_url="/test-project/docs",
    openapi_url="/test-project/openapi.json",
)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", None)
if allowed_origins:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins.split(","),
        allow_methods=["OPTIONS", "POST"],
        allow_headers=["Content-Type"],
    )

app.include_router(process_file_1_router)
app.include_router(process_file_2_router)
app.include_router(process_file_3_router)
app.include_router(process_file_4_router)
app.include_router(process_file_5_router)
app.include_router(process_text_1_router)
app.include_router(process_text_2_router)
app.include_router(process_text_3_router)
app.include_router(process_text_4_router)
app.include_router(process_text_file_1_router)
app.include_router(process_text_file_2_router)
app.include_router(process_text_file_3_router)
app.include_router(process_text_file_4_router)


# Filter out /healthcheck noise
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/healthcheck") == -1


# Filter out /metrics noise
class MetricsCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/metrics") == -1


logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())
logging.getLogger("uvicorn.access").addFilter(MetricsCheckFilter())


@app.get("/healthcheck", status_code=status.HTTP_200_OK, include_in_schema=False)
def healthcheck(request: Request):
    return {"healthcheck": "HEALTHCHECK STATUS: EVERYTHING OK!"}
