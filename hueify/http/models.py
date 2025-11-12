from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class HttpMethods(StrEnum):
    GET = "GET"


type ApiResponse = dict[str, Any]


T = TypeVar("T")


class HueApiError(BaseModel):
    description: str


class HueApiResponse(BaseModel, Generic[T]):
    errors: list[HueApiError] = Field(default_factory=list)
    data: list[T]

    def get_single_resource(self) -> T:
        if not self.data:
            raise ValueError("No resource found in API response")
        return self.data[0]
