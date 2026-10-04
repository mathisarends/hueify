from collections.abc import Callable
from types import TracebackType
from typing import Self, overload

from pydantic import TypeAdapter

from hueify import models as m
from hueify.credentials import load_credentials
from hueify.entertainment import EntertainmentNamespace
from hueify.http import HttpClient
from hueify.models import HueEvent
from hueify.resources import (
    BehaviorInstanceNamespace,
    DeviceNamespace,
    DeviceSoftwareUpdateNamespace,
    EnabledNamespace,
    GeofenceClientNamespace,
    GroupedLightNamespace,
    HomekitNamespace,
    LightNamespace,
    MatterNamespace,
    MotionNamespace,
    ResourceNamespace,
    ResourceRegistry,
    RoomNamespace,
    SceneNamespace,
    SmartSceneNamespace,
    UpdateNamespace,
    ZigbeeDeviceDiscoveryNamespace,
    ZoneNamespace,
)
from hueify.sse import (
    ConnectionHandler,
    EventHandler,
    EventResourceType,
    EventStream,
    ReconnectPolicy,
)


class Hueify:
    """Typed, stateless client for the Philips Hue CLIP v2 API.

    Credentials are read from the constructor arguments, the
    ``HUE_BRIDGE_IP``/``HUE_APP_KEY`` environment variables and a ``.env``
    file, in that order. ``HUE_CLIENT_KEY`` comes along for entertainment
    streaming, which is the only thing that needs it.

    Subscribing to events and starting the stream read better on the client
    itself, so those delegate to ``hue.events``, which owns the connection and
    reports its state.
    """

    def __init__(
        self,
        bridge_ip: str | None = None,
        app_key: str | None = None,
        client_key: str | None = None,
        reconnect: ReconnectPolicy | None = None,
    ) -> None:
        self._credentials = load_credentials(bridge_ip, app_key, client_key)
        self._http_client = HttpClient(self._credentials)
        self.lights = LightNamespace(self._http_client)
        self.rooms = RoomNamespace(self._http_client)
        self.zones = ZoneNamespace(self._http_client)
        self.scenes = SceneNamespace(self._http_client)
        self.entertainment = EntertainmentNamespace(
            self._http_client, self._credentials
        )
        self.grouped_lights = GroupedLightNamespace(self._http_client)
        self.smart_scenes = SmartSceneNamespace(self._http_client)
        self.devices = DeviceNamespace(self._http_client)
        self.device_power = self._read_namespace("device_power", m.DevicePower)
        self.device_software_updates = DeviceSoftwareUpdateNamespace(self._http_client)
        self.bridges = UpdateNamespace(
            "bridge", m.Bridge, m.HueModel, self._http_client
        )
        self.bridge_homes = self._read_namespace("bridge_home", m.BridgeHome)
        self.service_groups = UpdateNamespace(
            "service_group", m.ServiceGroup, m.ServiceGroupUpdate, self._http_client
        )
        self.motions = MotionNamespace(self._http_client)
        self.camera_motions = EnabledNamespace(
            "camera_motion", m.CameraMotion, m.EnabledUpdate, self._http_client
        )
        self.temperatures = EnabledNamespace(
            "temperature", m.Temperature, m.EnabledUpdate, self._http_client
        )
        self.light_levels = EnabledNamespace(
            "light_level", m.LightLevel, m.EnabledUpdate, self._http_client
        )
        self.buttons = UpdateNamespace(
            "button", m.Button, m.ButtonUpdate, self._http_client
        )
        self.bell_buttons = UpdateNamespace(
            "bell_button", m.BellButton, m.HueModel, self._http_client
        )
        self.relative_rotaries = UpdateNamespace(
            "relative_rotary", m.RelativeRotary, m.HueModel, self._http_client
        )
        self.contacts = EnabledNamespace(
            "contact", m.Contact, m.EnabledUpdate, self._http_client
        )
        self.tampers = UpdateNamespace(
            "tamper", m.Tamper, m.HueModel, self._http_client
        )
        self.grouped_motions = UpdateNamespace(
            "grouped_motion", m.GroupedMotion, m.HueModel, self._http_client
        )
        self.grouped_light_levels = UpdateNamespace(
            "grouped_light_level", m.GroupedLightLevel, m.HueModel, self._http_client
        )
        self.zigbee_connectivity = UpdateNamespace(
            "zigbee_connectivity",
            m.ZigbeeConnectivity,
            m.ZigbeeConnectivityUpdate,
            self._http_client,
        )
        self.zgp_connectivity = UpdateNamespace(
            "zgp_connectivity", m.ZgpConnectivity, m.HueModel, self._http_client
        )
        self.wifi_connectivity = UpdateNamespace(
            "wifi_connectivity", m.WifiConnectivity, m.HueModel, self._http_client
        )
        self.zigbee_device_discovery = ZigbeeDeviceDiscoveryNamespace(self._http_client)
        self.entertainment_services = UpdateNamespace(
            "entertainment", m.Entertainment, m.HueModel, self._http_client
        )
        self.speakers = UpdateNamespace(
            "speaker", m.Speaker, m.HueModel, self._http_client
        )
        self.behavior_scripts = UpdateNamespace(
            "behavior_script", m.BehaviorScript, m.HueModel, self._http_client
        )
        self.behavior_instances = BehaviorInstanceNamespace(self._http_client)
        self.geofence_clients = GeofenceClientNamespace(self._http_client)
        self.geolocations = UpdateNamespace(
            "geolocation", m.Geolocation, m.HueModel, self._http_client
        )
        self.homekit = HomekitNamespace(self._http_client)
        self.matter = MatterNamespace(self._http_client)
        self.matter_fabrics = UpdateNamespace(
            "matter_fabric", m.MatterFabric, m.HueModel, self._http_client
        )
        self.convenience_area_motions = EnabledNamespace(
            "convenience_area_motion",
            m.ConvenienceAreaMotion,
            m.EnabledUpdate,
            self._http_client,
        )
        self.security_area_motions = EnabledNamespace(
            "security_area_motion",
            m.SecurityAreaMotion,
            m.EnabledUpdate,
            self._http_client,
        )
        self.motion_area_candidates = UpdateNamespace(
            "motion_area_candidate",
            m.MotionAreaCandidate,
            m.HueModel,
            self._http_client,
        )
        self.motion_area_configurations = EnabledNamespace(
            "motion_area_configuration",
            m.MotionAreaConfiguration,
            m.EnabledUpdate,
            self._http_client,
        )
        self.switch_input_configurations = UpdateNamespace(
            "switch_input_configuration",
            m.SwitchInputConfiguration,
            m.SwitchInputConfigurationUpdate,
            self._http_client,
        )
        self.resources = ResourceRegistry(
            self._http_client,
            (
                value
                for value in vars(self).values()
                if isinstance(value, ResourceNamespace)
            ),
        )
        self.events = EventStream(self._credentials, reconnect)

    def _read_namespace[T: m.HueResource](
        self, kind: str, model: type[T]
    ) -> ResourceNamespace[T]:
        return ResourceNamespace(
            kind, TypeAdapter(m.HueApiResponse[model]), self._http_client
        )

    async def __aenter__(self) -> Self:
        return self

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> EventHandler[T]: ...

    @overload
    def on[T: HueEvent](
        self, resource_type: EventResourceType, handler: None = None
    ) -> Callable[[EventHandler[T]], EventHandler[T]]: ...

    def on[T: HueEvent](
        self,
        resource_type: EventResourceType,
        handler: EventHandler[T] | None = None,
    ) -> EventHandler[T] | Callable[[EventHandler[T]], EventHandler[T]]:
        return self.events.on(resource_type, handler)

    def off[T: HueEvent](
        self, resource_type: EventResourceType, handler: EventHandler[T]
    ) -> None:
        self.events.off(resource_type, handler)

    def on_connection_change(self, handler: ConnectionHandler) -> ConnectionHandler:
        return self.events.on_connection_change(handler)

    def off_connection_change(self, handler: ConnectionHandler) -> None:
        self.events.off_connection_change(handler)

    async def start_stream(self, timeout: float | None = None) -> None:
        """Start receiving events in the background; calling twice is harmless.

        Pass a timeout to wait for the first connection and raise when the
        bridge does not answer in time.
        """
        await self.events.start(timeout)

    async def stop_stream(self) -> None:
        await self.events.stop()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.events.stop()
        await self._http_client.close()
