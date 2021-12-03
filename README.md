<p align="center">
    <a href="https://github.com/mtag-dev/squall/">
        <img src="docs/assets/squall-logo.png" alt="Squall" width="300"/>
    </a>
</p>
<p align="center">
    <em>Squall, API framework which looks ahead</em>
</p>

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/codecov/c/github/mtag-dev/squall?color=%2334D058)](https://pypi.org/project/python-squall/)
[![Test](https://github.com/mtag-dev/squall/workflows/Test/badge.svg?event=push&branch=master)](https://github.com/mtag-dev/squall/actions/workflows/test.yml)
[![PyPi](https://img.shields.io/pypi/v/python-squall?color=%2334D058&label=pypi%20package)](https://pypi.org/project/python-squall/)
[![PyVersions](https://img.shields.io/pypi/pyversions/python-squall.svg?color=%2334D058)](https://pypi.org/project/python-squall/)

--- 
#### Navigation



## About
### Motivation


### Performance


## Usage
### Install

```shell
pip3 install python-squall
```

You also need some ASGI server. Let's install Uvicorn, the most popular one.

```shell
pip3 install uvicorn
```

### Quick start

Create `example.py` with the following content

```Python
from typing import List, Optional
from dataclasses import dataclass
from squall import Squall

app = Squall()


@dataclass
class Item:
    name: str
    value: Optional[int] = None


@app.get("/get", response_model=List[Item])
async def handle_get() -> List[Item]:
    return [
        Item(name="null_value"),
        Item(name="int_value", value=8)
    ]


@app.post("/post", response_model=Item)
async def handle_post(data: Item) -> Item:
    return data
```

And run it

```shell
uvicorn example:app
```

Now, we are able to surf our GET endpoint on: http://127.0.0.1:8000/get

And let's play with `curl` on POST endpoint

```shell
# curl -X 'POST' 'http://127.0.0.1:8000/post' -H 'Content-Type: application/json' -d '{"name": "string", "value": 234}'
{
  "name": "string",
  "value": 234
}
```

Type checking and validation is done by [apischema](https://wyfo.github.io/apischema/) for both, Request and Response.


```shell
# curl -X 'POST' 'http://127.0.0.1:8000/post' -H 'Content-Type: application/json' -d '{"name": "string", "value": "not_an_int"}'
{
  "details": [
    {
      "loc": [
        "value"
      ],
      "msg": "expected type integer, found string"
    },
    {
      "loc": [
        "value"
      ],
      "msg": "expected type null, found string"
    }
  ]
}
```


### OpenAPI generation

OpenAPI for your app generates automatically based on route parameters and schema you have defined.

There are support for ReDoc and Swagger out of the box. You can reach it locally once your application started:

- Swagger: http://127.0.0.1:8000/doc
- ReDoc: http://127.0.0.1:8000/redoc

![Example Get](docs/assets/openapi-example.png)


### Routing

Squall provides familiar decorators for any method route registration on both, application itself and on nested routers.

| Method   |      app      |  router * |
|:----------|:--------------|:------|
| GET | @app.get | @router.get |
| PUT | @app.put   | @router.put |
| POST | @app.post | @router.post |
| DELETE | @app.delete | @router.delete |
| OPTIONS | @app.options | @router.options |
| HEAD | @app.head | @router.head |
| PATCH | @app.patch | @router.patch |
| TRACE | @app.trace | @router.trace |

__* `router = squall.Router()`__

Nested routers supports prefixes and further nesting.

```Python
from squall import Router, Squall

animals_router = Router(prefix="/animals")


@animals_router.get("/")
async def get_animals():
    return []


@animals_router.get("/cat")
async def get_cat():
    return []

dogs_router = Router(prefix="/dogs")


@dogs_router.get("/list")
async def get_all_dogs():
    return []


animals_router.include_router(dogs_router)

app = Squall()
app.include_router(animals_router)
```

Will give us

![Animals routing](docs/assets/animals-routing.png)

Nested routing is usually used for splitting applications into files and achieving better project structure.
### HEAD parameters



### Body processing


## Roadmap

## Dependencies

## Acknowledgments

## Versioning

## License

MIT
