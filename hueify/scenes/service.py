import logging
from typing import Self
from uuid import UUID

from hueify.http import HttpClient
from hueify.scenes.lookup import SceneLookup
from hueify.scenes.models import (
    SceneAction,
    SceneActivationRequest,
    SceneInfo,
    SceneRecall,
    SceneStatusValue,
)
from hueify.shared.resource.models import ActionResult

logger = logging.getLogger(__name__)


class Scene:
    def __init__(
        self,
        scene_info: SceneInfo,
        client: HttpClient | None = None,
    ) -> None:
        self._scene_info = scene_info
        self._client = client or HttpClient()

    @classmethod
    async def from_name(cls, scene_name: str, client: HttpClient | None = None) -> Self:
        client = client or HttpClient()
        lookup = SceneLookup(client)
        scene_info = await lookup.find_scene_by_name(scene_name)
        return cls(scene_info=scene_info, client=client)

    @classmethod
    async def from_name_in_group(
        cls, scene_name: str, group_id: UUID, client: HttpClient | None = None
    ) -> Self:
        client = client or HttpClient()
        lookup = SceneLookup(client)
        scene_info = await lookup.find_scene_by_name_in_group(scene_name, group_id)
        return cls(scene_info=scene_info, client=client)

    @property
    def id(self) -> UUID:
        return self._scene_info.id

    @property
    def name(self) -> str:
        return self._scene_info.name

    @property
    def group_id(self) -> UUID:
        return self._scene_info.group_id

    async def activate(self) -> ActionResult:
        is_already_active = await self._is_scene_active()

        if is_already_active:
            return ActionResult(message=f"Scene '{self.name}' is already active")

        await self._activate_scene_with_action(SceneAction.ACTIVE)
        return ActionResult(message=f"Scene '{self.name}' activated")

    async def activate_with_dynamic_palette(self) -> ActionResult:
        await self._activate_scene_with_action(SceneAction.DYNAMIC_PALETTE)
        return ActionResult(
            message=f"Scene '{self.name}' activated with dynamic palette"
        )

    async def activate_static(self) -> ActionResult:
        await self._activate_scene_with_action(SceneAction.STATIC)
        return ActionResult(message=f"Scene '{self.name}' activated in static mode")

    async def _activate_scene_with_action(
        self, action: SceneAction, duration_ms: int | None = None
    ) -> None:
        recall = SceneRecall(action=action)
        if duration_ms:
            recall.duration = duration_ms

        request = SceneActivationRequest(recall=recall)
        await self._client.put(f"scene/{self.id}", data=request)

    async def _is_scene_active(self) -> bool:
        scene_info = await self._client.get_resource(
            f"scene/{self.id}", resource_type=SceneInfo
        )

        return (
            scene_info.status and scene_info.status.active != SceneStatusValue.INACTIVE
        )
