from uuid import UUID
from hueify.http.client import HttpClient
from hueify.lights.models import LightStateUpdate


class LightService:
    def __init__(self, client: HttpClient | None = None) -> None:
        self._client = client or HttpClient()

    async def turn_on(self, light_id: UUID) -> None:
        light_id_str = str(light_id)
        update = LightStateUpdate(on=True)
        await self._client.put(f"light/{light_id_str}", data=update)

    async def turn_off(self, light_id: UUID) -> None:
        light_id_str = str(light_id)
        update = LightStateUpdate(on=False)
        await self._client.put(f"light/{light_id_str}", data=update)
