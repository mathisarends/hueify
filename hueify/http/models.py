from enum import StrEnum
from typing import Any


class HttpMethods(StrEnum):
    GET = "GET"


type ApiResponse = dict[str, Any]
