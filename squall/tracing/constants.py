from enum import Enum


class SpanName(str, Enum):
    response_preparation = "Response preparation"
    pulling_request_data = "Getting response data"
    handle = "Handling"
    returning_response = "Sending response"
    middleware_processing = "Middleware processing"
