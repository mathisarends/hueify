from abc import ABC, abstractmethod

from hueify.http import HttpClient


class PopulatableCache(ABC):
    @abstractmethod
    async def populate(self, http_client: HttpClient) -> None: ...
