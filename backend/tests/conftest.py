import pytest
from fastapi.testclient import TestClient

from voyager_tracker.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
