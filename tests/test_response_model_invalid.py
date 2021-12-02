from typing import List

import pytest
from apischema import Unsupported
from squall import Squall


class NonPydanticModel:
    pass


# from apischema.schemas import


def test_invalid_response_model_raises():
    with pytest.raises(Unsupported):
        app = Squall()

        @app.get("/", response_model=NonPydanticModel)
        def read_root():
            pass  # pragma: nocover


def test_invalid_response_model_sub_type_raises():
    with pytest.raises(Unsupported):
        app = Squall()

        @app.get("/", response_model=List[NonPydanticModel])
        def read_root():
            pass  # pragma: nocover


@pytest.mark.skip("Implement additional responses validation")
def test_invalid_response_model_in_responses_raises():
    with pytest.raises(Unsupported):
        app = Squall()

        @app.get("/", responses={"500": {"model": NonPydanticModel}})
        def read_root():
            pass  # pragma: nocover


@pytest.mark.skip("Implement additional responses validation")
def test_invalid_response_model_sub_type_in_responses_raises():
    with pytest.raises(Unsupported):
        app = Squall()

        @app.get("/", responses={"500": {"model": List[NonPydanticModel]}})
        def read_root():
            pass  # pragma: nocover
