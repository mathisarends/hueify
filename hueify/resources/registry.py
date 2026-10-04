"""Resource discovery and an explicit raw escape hatch for newer bridge APIs."""

import re
from collections.abc import Iterable, Mapping
from typing import Annotated, Any

from pydantic import BaseModel, Discriminator, RootModel, Tag, TypeAdapter

from hueify import models as m
from hueify.http import HttpClient
from hueify.resources.base import ResourceId, ResourceNamespace


def _resource_tag(value: Any) -> str:
    kind = (
        value.get("type") if isinstance(value, dict) else getattr(value, "type", None)
    )
    tag = str(kind)
    return tag if tag in _RESOURCE_TYPES else "other"


_RESOURCE_TYPES = frozenset(
    {
        "light",
        "grouped_light",
        "room",
        "zone",
        "scene",
        "smart_scene",
        "device",
        "device_power",
        "device_software_update",
        "bridge",
        "bridge_home",
        "service_group",
        "motion",
        "camera_motion",
        "temperature",
        "light_level",
        "button",
        "bell_button",
        "relative_rotary",
        "contact",
        "tamper",
        "grouped_motion",
        "grouped_light_level",
        "zigbee_connectivity",
        "zgp_connectivity",
        "wifi_connectivity",
        "zigbee_device_discovery",
        "entertainment",
        "entertainment_configuration",
        "speaker",
        "behavior_script",
        "behavior_instance",
        "geofence_client",
        "geolocation",
        "homekit",
        "matter",
        "matter_fabric",
        "convenience_area_motion",
        "security_area_motion",
        "motion_area_candidate",
        "motion_area_configuration",
        "switch_input_configuration",
    }
)


AnyHueResource = Annotated[
    Annotated[m.Light, Tag("light")]
    | Annotated[m.GroupedLight, Tag("grouped_light")]
    | Annotated[m.Room, Tag("room")]
    | Annotated[m.Zone, Tag("zone")]
    | Annotated[m.Scene, Tag("scene")]
    | Annotated[m.SmartScene, Tag("smart_scene")]
    | Annotated[m.Device, Tag("device")]
    | Annotated[m.DevicePower, Tag("device_power")]
    | Annotated[m.DeviceSoftwareUpdate, Tag("device_software_update")]
    | Annotated[m.Bridge, Tag("bridge")]
    | Annotated[m.BridgeHome, Tag("bridge_home")]
    | Annotated[m.ServiceGroup, Tag("service_group")]
    | Annotated[m.Motion, Tag("motion")]
    | Annotated[m.CameraMotion, Tag("camera_motion")]
    | Annotated[m.Temperature, Tag("temperature")]
    | Annotated[m.LightLevel, Tag("light_level")]
    | Annotated[m.Button, Tag("button")]
    | Annotated[m.BellButton, Tag("bell_button")]
    | Annotated[m.RelativeRotary, Tag("relative_rotary")]
    | Annotated[m.Contact, Tag("contact")]
    | Annotated[m.Tamper, Tag("tamper")]
    | Annotated[m.GroupedMotion, Tag("grouped_motion")]
    | Annotated[m.GroupedLightLevel, Tag("grouped_light_level")]
    | Annotated[m.ZigbeeConnectivity, Tag("zigbee_connectivity")]
    | Annotated[m.ZgpConnectivity, Tag("zgp_connectivity")]
    | Annotated[m.WifiConnectivity, Tag("wifi_connectivity")]
    | Annotated[m.ZigbeeDeviceDiscovery, Tag("zigbee_device_discovery")]
    | Annotated[m.Entertainment, Tag("entertainment")]
    | Annotated[m.EntertainmentConfiguration, Tag("entertainment_configuration")]
    | Annotated[m.Speaker, Tag("speaker")]
    | Annotated[m.BehaviorScript, Tag("behavior_script")]
    | Annotated[m.BehaviorInstance, Tag("behavior_instance")]
    | Annotated[m.GeofenceClient, Tag("geofence_client")]
    | Annotated[m.Geolocation, Tag("geolocation")]
    | Annotated[m.Homekit, Tag("homekit")]
    | Annotated[m.Matter, Tag("matter")]
    | Annotated[m.MatterFabric, Tag("matter_fabric")]
    | Annotated[m.ConvenienceAreaMotion, Tag("convenience_area_motion")]
    | Annotated[m.SecurityAreaMotion, Tag("security_area_motion")]
    | Annotated[m.MotionAreaCandidate, Tag("motion_area_candidate")]
    | Annotated[m.MotionAreaConfiguration, Tag("motion_area_configuration")]
    | Annotated[m.SwitchInputConfiguration, Tag("switch_input_configuration")]
    | Annotated[m.HueResource, Tag("other")],
    Discriminator(_resource_tag),
]

_RESOURCE_RESPONSE = TypeAdapter(m.HueApiResponse[AnyHueResource])
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

    async def list(self) -> m.HueApiResponse[AnyHueResource]:
        return await self._http_client.get("", _RESOURCE_RESPONSE)

    async def get(self, reference: m.ResourceReference) -> BaseModel:
        return await self[reference.rtype].get_one(reference.rid)
