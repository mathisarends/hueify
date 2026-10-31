from __future__ import annotations

from difflib import SequenceMatcher
from urllib.parse import quote
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from hueify.errors import AmbiguousResourceError, ResourceNotFoundError
from hueify.http import HttpClient
from hueify.models import HueApiResponse, HueModel, HueResource, ResourceIdentifier

type ResourceId = str | UUID

_FUZZY_MATCH_CUTOFF = 0.75


class ResourceNamespace[TResource: HueResource]:
    """Typed, stateless interface for one Hue CLIP v2 resource endpoint."""

    def __init__(
        self,
        resource_type: str,
        response_adapter: TypeAdapter[HueApiResponse[TResource]],
        http_client: HttpClient,
    ) -> None:
        self.resource_type = resource_type
        self._response_adapter = response_adapter
        self._http_client = http_client

    async def list(self) -> HueApiResponse[TResource]:
        return await self._http_client.get(self.resource_type, self._response_adapter)

    async def get(self, resource_id: ResourceId) -> HueApiResponse[TResource]:
        return await self._http_client.get(
            self._resource_path(resource_id), self._response_adapter
        )

    async def get_one(self, resource_id: ResourceId) -> TResource:
        response = await self.get(resource_id)
        if not response.data:
            raise ResourceNotFoundError(
                f"No {self.resource_type.replace('_', ' ')} with ID {resource_id}"
            )
        return response.data[0]

    async def find_by_name(self, name: str, *, fuzzy: bool = True) -> TResource:
        return self._find_by_name(name, (await self.list()).data, fuzzy=fuzzy)

    def _find_by_name(
        self, name: str, resources: list[TResource], *, fuzzy: bool
    ) -> TResource:
        wanted = _normalized(name)
        named_resources: list[tuple[str, TResource]] = []
        for resource in resources:
            resource_name = _resource_name(resource)
            if resource_name is None:
                continue
            named_resources.append((resource_name, resource))
        exact = [pair for pair in named_resources if _normalized(pair[0]) == wanted]
        if exact:
            return self._unique_match(name, exact)

        ranked_resources = sorted(
            named_resources,
            key=lambda pair: (
                -_similarity(wanted, pair[0]),
                _normalized(pair[0]),
                pair[0],
            ),
        )
        if (
            fuzzy
            and ranked_resources
            and _similarity(wanted, ranked_resources[0][0]) >= _FUZZY_MATCH_CUTOFF
        ):
            best_score = _similarity(wanted, ranked_resources[0][0])
            matches = [
                pair
                for pair in ranked_resources
                if _similarity(wanted, pair[0]) == best_score
            ]
            return self._unique_match(name, matches)

        known = ", ".join(pair[0] for pair in ranked_resources)
        raise ResourceNotFoundError(
            f"No {self.resource_type} named {name!r}. Known names: {known or 'none'}"
        )

    def _unique_match(
        self, name: str, matches: list[tuple[str, TResource]]
    ) -> TResource:
        if len(matches) == 1:
            return matches[0][1]
        candidates = "; ".join(
            f"{resource_name!r} (ID {resource.id})"
            for resource_name, resource in matches
        )
        raise AmbiguousResourceError(
            f"Ambiguous {self.resource_type} name {name!r}. Candidates: {candidates}. Use an ID or narrow the group."
        )

    async def _create(self, data: BaseModel) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.post(self.resource_type, data)

    async def _update(
        self, resource_id: ResourceId, data: BaseModel
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.put(self._resource_path(resource_id), data)

    async def _delete(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._http_client.delete(self._resource_path(resource_id))

    def _resource_path(self, resource_id: ResourceId) -> str:
        return f"{self.resource_type}/{quote(str(resource_id), safe='')}"


class UpdateNamespace[TResource: HueResource, TUpdate: HueModel](
    ResourceNamespace[TResource]
):
    """Reads and partial writes with a dedicated, validated request model."""

    def __init__(
        self,
        resource_type: str,
        resource_model: type[TResource],
        update_model: type[TUpdate],
        http_client: HttpClient,
    ) -> None:
        super().__init__(
            resource_type, TypeAdapter(HueApiResponse[resource_model]), http_client
        )
        self._update_model = update_model

    async def update(
        self, resource_id: ResourceId, data: TUpdate
    ) -> HueApiResponse[ResourceIdentifier]:
        if not isinstance(data, self._update_model):
            raise TypeError(
                f"{self.resource_type}.update expects {self._update_model.__name__}"
            )
        return await self._update(resource_id, data)


def _normalized(name: str) -> str:
    return name.strip().casefold()


def _resource_name(resource: BaseModel) -> str | None:
    metadata = getattr(resource, "metadata", None)
    metadata_name = (
        metadata.get("name")
        if isinstance(metadata, dict)
        else getattr(metadata, "name", None)
    )
    name = metadata_name or getattr(resource, "name", None)
    return name if isinstance(name, str) else None


def _similarity(normalized_name: str, candidate: str) -> float:
    return SequenceMatcher(
        None, normalized_name, _normalized(candidate), autojunk=False
    ).ratio()
