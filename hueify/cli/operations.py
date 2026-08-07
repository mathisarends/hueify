import asyncio
from collections.abc import Coroutine
from enum import StrEnum
from uuid import UUID

import httpx
import typer

from hueify import Hueify
from hueify.errors import (
    EntertainmentAuthenticationError,
    HueifyError,
    MissingCredentialsError,
    StreamAuthenticationError,
)
from hueify.models import (
    EntertainmentConfiguration,
    HueApiResponse,
    Light,
    ResourceIdentifier,
    Room,
    Scene,
    Zone,
)
from hueify.resources import (
    LightNamespace,
    ResourceId,
    RoomNamespace,
    ZoneNamespace,
)

type ControlNamespace = LightNamespace | RoomNamespace | ZoneNamespace


class ControlGroup(StrEnum):
    LIGHTS = "lights"
    ROOMS = "rooms"
    ZONES = "zones"


def run[T](coroutine: Coroutine[object, object, T]) -> T:
    """Run one bridge operation and translate failures into CLI exit codes."""
    try:
        return asyncio.run(coroutine)
    except (
        MissingCredentialsError,
        StreamAuthenticationError,
        EntertainmentAuthenticationError,
    ) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(3) from error
    except httpx.HTTPError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(4) from error
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    except HueifyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


async def list_lights() -> list[Light]:
    async with Hueify() as hue:
        return (await hue.lights.list()).data


async def list_rooms() -> list[Room]:
    async with Hueify() as hue:
        return (await hue.rooms.list()).data


async def list_zones() -> list[Zone]:
    async with Hueify() as hue:
        return (await hue.zones.list()).data


async def list_scenes() -> list[Scene]:
    async with Hueify() as hue:
        return (await hue.scenes.list()).data


async def list_entertainment_areas() -> list[EntertainmentConfiguration]:
    async with Hueify() as hue:
        return (await hue.entertainment.list()).data


def _control_namespace(hue: Hueify, group: ControlGroup) -> ControlNamespace:
    match group:
        case ControlGroup.LIGHTS:
            return hue.lights
        case ControlGroup.ROOMS:
            return hue.rooms
        case ControlGroup.ZONES:
            return hue.zones


async def _resolve_target(
    namespace: ControlNamespace,
    target: str,
) -> ResourceId:
    try:
        UUID(target)
    except ValueError:
        return (await namespace.find_by_name(target)).id
    return target


async def turn_on(
    group: ControlGroup,
    target: str,
    *,
    brightness: float | None,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.turn_on(
            resource_id,
            brightness=brightness,
            transition=transition,
        )


async def turn_off(
    group: ControlGroup,
    target: str,
    *,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.turn_off(resource_id, transition=transition)


async def toggle(
    group: ControlGroup,
    target: str,
    *,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.toggle(resource_id, transition=transition)


async def set_brightness(
    group: ControlGroup,
    target: str,
    percent: float,
    *,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.set_brightness(
            resource_id,
            percent,
            transition=transition,
        )


async def set_color(
    group: ControlGroup,
    target: str,
    hex_color: str,
    *,
    brightness: float | None,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.set_hex(
            resource_id,
            hex_color,
            brightness=brightness,
            transition=transition,
        )


async def set_temperature(
    group: ControlGroup,
    target: str,
    kelvin: int,
    *,
    brightness: float | None,
    transition: float | None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.set_color_temperature(
            resource_id,
            kelvin,
            brightness=brightness,
            transition=transition,
        )


async def identify(
    group: ControlGroup,
    target: str,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target)
        return await namespace.identify(resource_id)


async def activate_scene(
    target: str,
    *,
    brightness: float | None,
    transition: float | None,
    dynamic: bool,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        try:
            UUID(target)
        except ValueError:
            resource_id = (await hue.scenes.find_by_name(target)).id
        else:
            resource_id = target
        return await hue.scenes.activate(
            resource_id,
            brightness=brightness,
            transition=transition,
            dynamic=dynamic,
        )


async def start_entertainment_area(
    target: str,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        try:
            UUID(target)
        except ValueError:
            resource_id = (await hue.entertainment.find_by_name(target)).id
        else:
            resource_id = target
        return await hue.entertainment.start(resource_id)


async def stop_entertainment_area(
    target: str,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        try:
            UUID(target)
        except ValueError:
            resource_id = (await hue.entertainment.find_by_name(target)).id
        else:
            resource_id = target
        return await hue.entertainment.stop(resource_id)
