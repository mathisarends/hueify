from abc import ABC, abstractmethod
from typing import Self

from hueify.http.client import HttpClient


class NamedResourceMixin(ABC):
    @classmethod
    @abstractmethod
    async def from_name(cls, name: str, client: HttpClient | None = None) -> Self:
        pass
