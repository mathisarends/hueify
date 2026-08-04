from collections.abc import Mapping
from typing import Any
from urllib.parse import quote
from uuid import UUID

from hueify.http import HttpClient
from hueify.http.schemas import ApiResponse

type JsonObject = dict[str, Any]
type JsonMapping = Mapping[str, Any]
type ResourceId = str | UUID


class ResourceNamespace:
    """Thin JSON interface for one Hue CLIP v2 resource endpoint."""

    def __init__(self, resource_type: str, http_client: HttpClient) -> None:
        if not resource_type or not resource_type.replace("_", "").isalnum():
            raise ValueError(f"Invalid Hue resource type: {resource_type!r}")
        self.resource_type = resource_type
        self._http_client = http_client

    async def get_all(self) -> ApiResponse:
        """Return the complete Hue response for all resources of this type."""
        return await self._http_client.get(self.resource_type)

    async def get(self, resource_id: ResourceId) -> ApiResponse:
        """Return the complete Hue response for a resource ID."""
        return await self._http_client.get(self._resource_path(resource_id))

    async def create(self, data: JsonMapping) -> ApiResponse:
        """POST JSON to the resource collection and return Hue's response."""
        return await self._http_client.post(self.resource_type, data)

    async def update(self, resource_id: ResourceId, data: JsonMapping) -> ApiResponse:
        """PUT JSON to a resource ID and return Hue's response."""
        return await self._http_client.put(self._resource_path(resource_id), data)

    async def delete(self, resource_id: ResourceId) -> ApiResponse:
        """DELETE a resource ID and return Hue's response."""
        return await self._http_client.delete(self._resource_path(resource_id))

    def _resource_path(self, resource_id: ResourceId) -> str:
        return f"{self.resource_type}/{quote(str(resource_id), safe='')}"

    def __repr__(self) -> str:
        return f"ResourceNamespace(resource_type={self.resource_type!r})"
