from starlette.testclient import TestClient
from prepline_test_project.api.app import app

DOCS_ROUTE = "/test-project/docs"
OPENAPI_ROUTE = "/test-project/openapi.json"
HEALTHCHECK_ROUTE = "/healthcheck"

client = TestClient(app)


def test_openapi():
    response = client.get(OPENAPI_ROUTE)
    assert response.status_code == 200


def test_docs():
    response = client.get(DOCS_ROUTE)
    assert response.status_code == 200


def test_healthcheck():
    response = client.get(HEALTHCHECK_ROUTE)
    assert response.status_code == 200
    assert response.json() == {"healthcheck": "HEALTHCHECK STATUS: EVERYTHING OK!"}
