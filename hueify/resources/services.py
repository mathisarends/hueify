"""Typed namespaces for CLIP v2 device and sensor services."""

from hueify.http import HttpClient
from hueify.models import (
    BehaviorInstance,
    BehaviorInstanceUpdate,
    Device,
    DeviceSoftwareUpdate,
    DeviceSoftwareUpdateUpdate,
    DeviceUpdate,
    DiscoveryAction,
    EnabledUpdate,
    GeofenceClient,
    GeofenceClientUpdate,
    Homekit,
    HomekitUpdate,
    HueApiResponse,
    HueResource,
    IdentifyAction,
    Matter,
    MatterAction,
    MatterUpdate,
    MetadataUpdate,
    Motion,
    MotionSensitivityUpdate,
    MotionUpdate,
    ResourceIdentifier,
    SmartScene,
    SmartSceneCreate,
    SmartSceneRecall,
    SmartSceneUpdate,
    SoftwareInstall,
    UserTestUpdate,
    ZigbeeDeviceDiscovery,
    ZigbeeDeviceDiscoveryUpdate,
)
from hueify.resources.base import ResourceId, UpdateNamespace


class EnabledNamespace[TResource: HueResource, TUpdate: EnabledUpdate](
    UpdateNamespace[TResource, TUpdate]
):
    async def enable(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, self._update_model(enabled=True))

    async def disable(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, self._update_model(enabled=False))


class DeviceNamespace(UpdateNamespace[Device, DeviceUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("device", Device, DeviceUpdate, http_client)

    async def rename(
        self, resource_id: ResourceId, name: str
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, DeviceUpdate(metadata=MetadataUpdate(name=name))
        )

    async def identify(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, DeviceUpdate(identify=IdentifyAction()))

    async def set_usertest(
        self, resource_id: ResourceId, enabled: bool
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, DeviceUpdate(usertest=UserTestUpdate(usertest=enabled))
        )

    async def delete(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(resource_id)


class MotionNamespace(EnabledNamespace[Motion, MotionUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("motion", Motion, MotionUpdate, http_client)

    async def set_sensitivity(
        self, resource_id: ResourceId, sensitivity: int
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id,
            MotionUpdate(sensitivity=MotionSensitivityUpdate(sensitivity=sensitivity)),
        )


class DeviceSoftwareUpdateNamespace(
    UpdateNamespace[DeviceSoftwareUpdate, DeviceSoftwareUpdateUpdate]
):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__(
            "device_software_update",
            DeviceSoftwareUpdate,
            DeviceSoftwareUpdateUpdate,
            http_client,
        )

    async def install(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, DeviceSoftwareUpdateUpdate(install=SoftwareInstall())
        )


class BehaviorInstanceNamespace(
    EnabledNamespace[BehaviorInstance, BehaviorInstanceUpdate]
):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__(
            "behavior_instance", BehaviorInstance, BehaviorInstanceUpdate, http_client
        )


class GeofenceClientNamespace(UpdateNamespace[GeofenceClient, GeofenceClientUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__(
            "geofence_client", GeofenceClient, GeofenceClientUpdate, http_client
        )

    async def set_at_home(
        self, resource_id: ResourceId, at_home: bool
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, GeofenceClientUpdate(is_at_home=at_home))


class ZigbeeDeviceDiscoveryNamespace(
    UpdateNamespace[ZigbeeDeviceDiscovery, ZigbeeDeviceDiscoveryUpdate]
):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__(
            "zigbee_device_discovery",
            ZigbeeDeviceDiscovery,
            ZigbeeDeviceDiscoveryUpdate,
            http_client,
        )

    async def search(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, ZigbeeDeviceDiscoveryUpdate(action=DiscoveryAction())
        )


class HomekitNamespace(UpdateNamespace[Homekit, HomekitUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("homekit", Homekit, HomekitUpdate, http_client)

    async def reset(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, HomekitUpdate(action="homekit_reset"))


class MatterNamespace(UpdateNamespace[Matter, MatterUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("matter", Matter, MatterUpdate, http_client)

    async def reset(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(resource_id, MatterUpdate(action=MatterAction()))


class SmartSceneNamespace(UpdateNamespace[SmartScene, SmartSceneUpdate]):
    def __init__(self, http_client: HttpClient) -> None:
        super().__init__("smart_scene", SmartScene, SmartSceneUpdate, http_client)

    async def create(
        self, data: SmartSceneCreate
    ) -> HueApiResponse[ResourceIdentifier]:
        if not isinstance(data, SmartSceneCreate):
            raise TypeError("smart_scene.create expects SmartSceneCreate")
        return await self._create(data)

    async def delete(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self._delete(resource_id)

    async def activate(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, SmartSceneUpdate(recall=SmartSceneRecall(action="activate"))
        )

    async def deactivate(
        self, resource_id: ResourceId
    ) -> HueApiResponse[ResourceIdentifier]:
        return await self.update(
            resource_id, SmartSceneUpdate(recall=SmartSceneRecall(action="deactivate"))
        )
