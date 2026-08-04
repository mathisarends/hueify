from types import TracebackType
from typing import Self

from hueify.credentials import HueBridgeCredentials
from hueify.http import HttpClient
from hueify.resources import ResourceNamespace
from hueify.sse import EventStream

# Python-facing plural name -> Hue CLIP v2 resource endpoint.
_RESOURCE_NAMES = {
    "behavior_instances": "behavior_instance",
    "behavior_scripts": "behavior_script",
    "bridges": "bridge",
    "bridge_homes": "bridge_home",
    "buttons": "button",
    "camera_motions": "camera_motion",
    "contacts": "contact",
    "devices": "device",
    "device_powers": "device_power",
    "device_software_updates": "device_software_update",
    "entertainments": "entertainment",
    "entertainment_configurations": "entertainment_configuration",
    "geofence_clients": "geofence_client",
    "geolocations": "geolocation",
    "grouped_lights": "grouped_light",
    "grouped_light_levels": "grouped_light_level",
    "grouped_motions": "grouped_motion",
    "homekits": "homekit",
    "lights": "light",
    "light_levels": "light_level",
    "matters": "matter",
    "matter_fabrics": "matter_fabric",
    "motions": "motion",
    "public_images": "public_image",
    "relative_rotaries": "relative_rotary",
    "rooms": "room",
    "scenes": "scene",
    "service_groups": "service_group",
    "smart_scenes": "smart_scene",
    "speakers": "speaker",
    "tampers": "tamper",
    "temperatures": "temperature",
    "wifi_connectivities": "wifi_connectivity",
    "zigbee_connectivities": "zigbee_connectivity",
    "zigbee_device_discoveries": "zigbee_device_discovery",
    "zgp_connectivities": "zgp_connectivity",
    "zones": "zone",
}


class Hueify:
    """Lazy, JSON-first client for the Philips Hue CLIP v2 API."""

    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
    ) -> None:
        self._credentials = self._resolve_credentials(bridge_ip, app_key)
        self._http_client = HttpClient(self._credentials)
        self._resource_namespaces: dict[str, ResourceNamespace] = {}

        for attribute, resource_type in _RESOURCE_NAMES.items():
            setattr(self, attribute, self.resource(resource_type))

        # Constructing or entering Hueify does not open a stream connection.
        self.events = EventStream(self._credentials)

    def resource(self, resource_type: str) -> ResourceNamespace:
        """Return a namespace for any current or future Hue resource type."""
        namespace = self._resource_namespaces.get(resource_type)
        if namespace is None:
            namespace = ResourceNamespace(resource_type, self._http_client)
            self._resource_namespaces[resource_type] = namespace
        return namespace

    def _resolve_credentials(
        self,
        bridge_ip: str | None,
        app_key: str | None,
    ) -> HueBridgeCredentials:
        credential_overrides = {}
        if bridge_ip is not None:
            credential_overrides["hue_bridge_ip"] = bridge_ip
        if app_key is not None:
            credential_overrides["hue_app_key"] = app_key
        return HueBridgeCredentials(**credential_overrides)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.events.close()
        await self._http_client.close()
