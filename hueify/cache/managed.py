from abc import ABC, abstractmethod

from hueify.http import HttpClient


class ManagedCache(ABC):
    @abstractmethod
    async def populate(self, http_client: HttpClient) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...
