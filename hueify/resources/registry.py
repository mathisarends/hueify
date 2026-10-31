"""Resource discovery and an explicit raw escape hatch for newer bridge APIs."""

import re
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, RootModel, TypeAdapter

from hueify import models as m
from hueify.http import HttpClient
from hueify.resources.base import ResourceId, ResourceNamespace

_RESOURCE_RESPONSE = TypeAdapter(m.HueApiResponse[m.AnyHueResource])
_RAW_RESPONSE = TypeAdapter(m.HueApiResponse[m.HueResource])


class JsonPayload(RootModel[dict[str, Any]]):
    """Keep dictionary values, including explicit nulls, in raw requests."""


class RawNamespace(ResourceNamespace[m.HueResource]):
    """Unvalidated bridge operations. The bridge decides what is supported.

    This is deliberately separate from the typed namespaces: availability of
    a raw method does not assert that a firmware supports that operation.
    """

    def __init__(self, resource_type: str, http_client: HttpClient) -> None:
        if re.fullmatch(r"[a-z][a-z0-9_]*", resource_type) is None:
            raise ValueError("A resource type must be a CLIP resource name")
        super().__init__(resource_type, _RAW_RESPONSE, http_client)

    async def create(
        self, data: Mapping[str, Any] | BaseModel
    ) -> m.HueApiResponse[m.ResourceIdentifier]:
        return await self._create(_payload(data))

    async def update(
        self, resource_id: ResourceId, data: Mapping[str, Any] | BaseModel
    ) -> m.HueApiResponse[m.ResourceIdentifier]:
        return await self._update(resource_id, _payload(data))

    async def delete(
        self, resource_id: ResourceId
    ) -> m.HueApiResponse[m.ResourceIdentifier]:
        return await self._delete(resource_id)


def _payload(data: Mapping[str, Any] | BaseModel) -> JsonPayload:
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json", exclude_none=True)
    return JsonPayload(dict(data))


class ResourceRegistry:
    """List every resource, resolve references, or address a raw endpoint."""

    def __init__(
        self, http_client: HttpClient, namespaces: Iterable[ResourceNamespace]
    ) -> None:
        self._http_client = http_client
        self._namespaces = {
            namespace.resource_type: namespace for namespace in namespaces
        }

    @property
    def types(self) -> tuple[str, ...]:
        """Resource types with a built-in namespace, regardless of bridge support."""
        return tuple(sorted(self._namespaces))

    def __getitem__(self, resource_type: m.ResourceType | str) -> ResourceNamespace:
        kind = str(resource_type)
        namespace = self._namespaces.get(kind)
        return namespace if namespace is not None else self.of(kind)

    def of(self, resource_type: m.ResourceType | str) -> RawNamespace:
        """Return an explicit raw namespace, also for a known resource type."""
        return RawNamespace(str(resource_type), self._http_client)

    async def list(self) -> m.HueApiResponse[m.AnyHueResource]:
        return await self._http_client.get("", _RESOURCE_RESPONSE)

    async def get(self, reference: m.ResourceReference) -> m.AnyHueResource:
        return await self[reference.rtype].get_one(reference.rid)
