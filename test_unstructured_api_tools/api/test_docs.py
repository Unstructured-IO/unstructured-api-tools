from starlette.testclient import TestClient
from prepline_test_project.api.app import app

DOCS_ROUTE = "/test-project/docs"

client = TestClient(app)


def test_docs():
    response = client.get(DOCS_ROUTE)
    assert response.status_code == 200
