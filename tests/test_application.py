import pytest
from squall.testclient import TestClient

from .main import app

client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Squall", "version": "0.1.0"},
    "paths": {
        "/api_route": {
            "get": {
                "summary": "Non Operation",
                "operationId": "non_operation_api_route_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
            }
        },
        "/non_decorated_route": {
            "get": {
                "summary": "Non Decorated Route",
                "operationId": "non_decorated_route_non_decorated_route_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
            }
        },
        "/text": {
            "get": {
                "summary": "Get Text",
                "operationId": "get_text_text_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
            }
        },
        "/path/{item_id}": {
            "get": {
                "summary": "Get Id",
                "operationId": "get_id_path__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/str/{item_id}": {
            "get": {
                "summary": "Get Str Id",
                "operationId": "get_str_id_path_str__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/int/{item_id}": {
            "get": {
                "summary": "Get Int Id",
                "operationId": "get_int_id_path_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "integer"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/float/{item_id}": {
            "get": {
                "summary": "Get Float Id",
                "operationId": "get_float_id_path_float__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "number"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param/{item_id}": {
            "get": {
                "summary": "Get Path Param Id",
                "operationId": "get_path_param_id_path_param__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-required/{item_id}": {
            "get": {
                "summary": "Get Path Param Required Id",
                "operationId": "get_path_param_required_id_path_param_required__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-minlength/{item_id}": {
            "get": {
                "summary": "Get Path Param Min Len",
                "operationId": "get_path_param_min_len_path_param_minlength__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-maxlength/{item_id}": {
            "get": {
                "summary": "Get Path Param Max Len",
                "operationId": "get_path_param_max_len_path_param_maxlength__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-min_maxlength/{item_id}": {
            "get": {
                "summary": "Get Path Param Min Max Len",
                "operationId": "get_path_param_min_max_len_path_param_min_maxlength__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-gt/{item_id}": {
            "get": {
                "summary": "Get Path Param Gt",
                "operationId": "get_path_param_gt_path_param_gt__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "minimum": 3,
                            "exclusiveMinimum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-gt0/{item_id}": {
            "get": {
                "summary": "Get Path Param Gt0",
                "operationId": "get_path_param_gt0_path_param_gt0__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "minimum": 0,
                            "exclusiveMinimum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-ge/{item_id}": {
            "get": {
                "summary": "Get Path Param Ge",
                "operationId": "get_path_param_ge_path_param_ge__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "minimum": 3,
                            "exclusiveMinimum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-lt/{item_id}": {
            "get": {
                "summary": "Get Path Param Lt",
                "operationId": "get_path_param_lt_path_param_lt__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "maximum": 3,
                            "exclusiveMaximum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-lt0/{item_id}": {
            "get": {
                "summary": "Get Path Param Lt0",
                "operationId": "get_path_param_lt0_path_param_lt0__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "maximum": 0,
                            "exclusiveMaximum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-le/{item_id}": {
            "get": {
                "summary": "Get Path Param Le",
                "operationId": "get_path_param_le_path_param_le__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "maximum": 3,
                            "exclusiveMaximum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-lt-gt/{item_id}": {
            "get": {
                "summary": "Get Path Param Lt Gt",
                "operationId": "get_path_param_lt_gt_path_param_lt_gt__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "minimum": 1,
                            "exclusiveMinimum": True,
                            "maximum": 3,
                            "exclusiveMaximum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-le-ge/{item_id}": {
            "get": {
                "summary": "Get Path Param Le Ge",
                "operationId": "get_path_param_le_ge_path_param_le_ge__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "number",
                            "minimum": 1,
                            "exclusiveMinimum": False,
                            "maximum": 3,
                            "exclusiveMaximum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-lt-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Lt Int",
                "operationId": "get_path_param_lt_int_path_param_lt_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "maximum": 3,
                            "exclusiveMaximum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-gt-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Gt Int",
                "operationId": "get_path_param_gt_int_path_param_gt_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "minimum": 3,
                            "exclusiveMinimum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-le-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Le Int",
                "operationId": "get_path_param_le_int_path_param_le_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "maximum": 3,
                            "exclusiveMaximum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-ge-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Ge Int",
                "operationId": "get_path_param_ge_int_path_param_ge_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "minimum": 3,
                            "exclusiveMinimum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-lt-gt-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Lt Gt Int",
                "operationId": "get_path_param_lt_gt_int_path_param_lt_gt_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "minimum": 1,
                            "exclusiveMinimum": True,
                            "maximum": 3,
                            "exclusiveMaximum": True,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/path/param-le-ge-int/{item_id}": {
            "get": {
                "summary": "Get Path Param Le Ge Int",
                "operationId": "get_path_param_le_ge_int_path_param_le_ge_int__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "type": "integer",
                            "minimum": 1,
                            "exclusiveMinimum": False,
                            "maximum": 3,
                            "exclusiveMaximum": False,
                        },
                        "name": "item_id",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query": {
            "get": {
                "summary": "Get Query",
                "operationId": "get_query_query_get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "query",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/optional": {
            "get": {
                "summary": "Get Query Optional",
                "operationId": "get_query_optional_query_optional_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "query",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/int": {
            "get": {
                "summary": "Get Query Type",
                "operationId": "get_query_type_query_int_get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "integer"},
                        "name": "query",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/int/optional": {
            "get": {
                "summary": "Get Query Type Optional",
                "operationId": "get_query_type_optional_query_int_optional_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "integer"},
                        "name": "query",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/int/default": {
            "get": {
                "summary": "Get Query Type Int Default",
                "operationId": "get_query_type_int_default_query_int_default_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "integer"},
                        "name": "query",
                        "in": "path",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/param": {
            "get": {
                "summary": "Get Query Param",
                "operationId": "get_query_param_query_param_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"type": "string"},
                        "name": "query",
                        "in": "query",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/param-required": {
            "get": {
                "summary": "Get Query Param Required",
                "operationId": "get_query_param_required_query_param_required_get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "string"},
                        "name": "query",
                        "in": "query",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/query/param-required/int": {
            "get": {
                "summary": "Get Query Param Required Type",
                "operationId": "get_query_param_required_type_query_param_required_int_get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"type": "integer"},
                        "name": "query",
                        "in": "query",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "400": {
                        "description": "Parameters Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPBadRequestError"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/enum-status-code": {
            "get": {
                "summary": "Get Enum Status Code",
                "operationId": "get_enum_status_code_enum_status_code_get",
                "responses": {
                    "201": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
            }
        },
    },
}


@pytest.mark.parametrize(
    "path,expected_status,expected_response",
    [
        ("/api_route", 200, {"message": "Hello World"}),
        ("/non_decorated_route", 200, {"message": "Hello World"}),
        ("/nonexistent", 404, {"detail": "Not Found"}),
        ("/openapi.json", 200, openapi_schema),
    ],
)
def test_get_path(path, expected_status, expected_response):
    response = client.get(path)
    assert response.status_code == expected_status
    assert response.json() == expected_response


def test_swagger_ui():
    response = client.get("/docs")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "swagger-ui-dist" in response.text
    assert (
        "oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect'"
        in response.text
    )


def test_swagger_ui_oauth2_redirect():
    response = client.get("/docs/oauth2-redirect")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "window.opener.swaggerUIRedirectOauth2" in response.text


def test_redoc():
    response = client.get("/redoc")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "redoc@next" in response.text


def test_enum_status_code_response():
    response = client.get("/enum-status-code")
    assert response.status_code == 201, response.text
    assert response.json() == "foo bar"
