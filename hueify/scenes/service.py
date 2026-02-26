import logging
from uuid import UUID

from hueify.http import HttpClient
from hueify.scenes.schemas import (
    SceneAction,
    SceneActivationRequest,
    SceneInfo,
    SceneRecall,
    SceneStatusValue,
)
from hueify.shared.resource.models import ActionResult

logger = logging.getLogger(__name__)


class Scene:
    def __init__(self, scene_info: SceneInfo, client: HttpClient) -> None:
        self._scene_info = scene_info
        self._client = client

    @property
    def id(self) -> UUID:
        return self._scene_info.id

    @property
    def name(self) -> str:
        return self._scene_info.name

    async def activate(self) -> ActionResult:
        was_already_active = (
            self._scene_info.status
            and self._scene_info.status.active != SceneStatusValue.INACTIVE
        )

        request = SceneActivationRequest(recall=SceneRecall(action=SceneAction.ACTIVE))
        await self._client.put(f"scene/{self.id}", data=request)

        if was_already_active:
            return ActionResult(message=f"Scene '{self.name}' was already active")

        return ActionResult(message=f"Scene '{self.name}' activated")
