import pytest
from squall import Squall
from squall.testclient import TestClient


@pytest.fixture(scope="function")
def app():
    return Squall()


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session")
def response_file(tmp_path_factory):
    file_path = tmp_path_factory.mktemp("data") / "response_file.txt"
    with open(file_path, "w") as fp:
        fp.writelines(["salo", "kovbasa", "saltison"])
    return file_path
