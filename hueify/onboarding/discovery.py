import httpx
from pydantic import BaseModel


class DiscoveredBridge(BaseModel):
    id: str
    internalipaddress: str


async def discover_bridges() -> list[DiscoveredBridge]:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://discovery.meethue.com/")
        response.raise_for_status()
        bridges = response.json()
        if not bridges:
            raise RuntimeError("No Hue Bridge found on the network.")
        return [DiscoveredBridge(**b) for b in bridges]
