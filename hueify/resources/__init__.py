from hueify.resources.base import ResourceId, ResourceNamespace, UpdateNamespace
from hueify.resources.controls import LightCommands, Transition
from hueify.resources.grouped_lights import GroupedLightNamespace
from hueify.resources.groups import GroupNamespace, RoomNamespace, ZoneNamespace
from hueify.resources.lights import LightNamespace
from hueify.resources.registry import RawNamespace, ResourceRegistry
from hueify.resources.scenes import SceneNamespace
from hueify.resources.services import (
    BehaviorInstanceNamespace,
    DeviceNamespace,
    DeviceSoftwareUpdateNamespace,
    EnabledNamespace,
    GeofenceClientNamespace,
    HomekitNamespace,
    MatterNamespace,
    MotionNamespace,
    SmartSceneNamespace,
    ZigbeeDeviceDiscoveryNamespace,
)

__all__ = [
    "BehaviorInstanceNamespace",
    "DeviceNamespace",
    "DeviceSoftwareUpdateNamespace",
    "EnabledNamespace",
    "GeofenceClientNamespace",
    "GroupNamespace",
    "GroupedLightNamespace",
    "HomekitNamespace",
    "LightCommands",
    "LightNamespace",
    "MatterNamespace",
    "MotionNamespace",
    "RawNamespace",
    "ResourceId",
    "ResourceNamespace",
    "ResourceRegistry",
    "RoomNamespace",
    "SceneNamespace",
    "SmartSceneNamespace",
    "Transition",
    "UpdateNamespace",
    "ZigbeeDeviceDiscoveryNamespace",
    "ZoneNamespace",
]
