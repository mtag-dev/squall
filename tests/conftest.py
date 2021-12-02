import pytest
from squall import Squall
from squall.testclient import TestClient


@pytest.fixture(scope="function")
def app():
    return Squall()


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)
