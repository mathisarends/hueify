import asyncio
from collections.abc import Coroutine
from enum import StrEnum
from uuid import UUID

import httpx
import typer
from pydantic import BaseModel, ValidationError

from hueify import Hueify
from hueify.errors import (
    EntertainmentAuthenticationError,
    HueifyError,
    MissingCredentialsError,
    ResourceNotFoundError,
    StreamAuthenticationError,
)
from hueify.models import (
    EntertainmentConfiguration,
    HueApiResponse,
    Light,
    NamedResource,
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
from hueify.resources.base import ResourceNamespace

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
    except ValidationError as error:
        typer.echo(_validation_error_message(error), err=True)
        raise typer.Exit(2) from error
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2) from error
    except HueifyError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


def _validation_error_message(error: ValidationError) -> str:
    """Turn Pydantic's diagnostic payload into a concise command-line error."""
    details = []
    for issue in error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    ):
        location = ".".join(str(part) for part in issue["loc"])
        message = issue["msg"]
        details.append(f"Invalid {location}: {message}" if location else message)
    return "; ".join(details) or "Invalid command value"


async def list_lights() -> list[Light]:
    async with Hueify() as hue:
        return _list_data(await hue.lights.list())


async def list_rooms() -> list[Room]:
    async with Hueify() as hue:
        return _list_data(await hue.rooms.list())


async def list_zones() -> list[Zone]:
    async with Hueify() as hue:
        return _list_data(await hue.zones.list())


async def list_scenes() -> list[Scene]:
    async with Hueify() as hue:
        return _list_data(await hue.scenes.list())


async def list_entertainment_areas() -> list[EntertainmentConfiguration]:
    async with Hueify() as hue:
        return _list_data(await hue.entertainment.list())


def _list_data[T: BaseModel](response: HueApiResponse[T]) -> list[T]:
    if response.errors:
        raise HueifyError("; ".join(error.description for error in response.errors))
    return response.data


def _control_namespace(hue: Hueify, group: ControlGroup) -> ControlNamespace:
    match group:
        case ControlGroup.LIGHTS:
            return hue.lights
        case ControlGroup.ROOMS:
            return hue.rooms
        case ControlGroup.ZONES:
            return hue.zones


async def _resolve_target(
    namespace: ResourceNamespace[NamedResource],
    target: str,
    *,
    fuzzy: bool = True,
) -> ResourceId:
    try:
        UUID(target)
    except ValueError:
        if not fuzzy:
            return (await namespace.find_by_name(target, fuzzy=False)).id
        return (await namespace.find_by_name(target)).id
    return target


async def turn_on(
    group: ControlGroup,
    target: str,
    *,
    brightness: float | None,
    transition: float | None,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
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
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
        return await namespace.turn_off(resource_id, transition=transition)


async def toggle(
    group: ControlGroup,
    target: str,
    *,
    transition: float | None,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
        return await namespace.toggle(resource_id, transition=transition)


async def set_brightness(
    group: ControlGroup,
    target: str,
    percent: float,
    *,
    transition: float | None,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
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
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
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
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
        return await namespace.set_color_temperature(
            resource_id,
            kelvin,
            brightness=brightness,
            transition=transition,
        )


async def identify(
    group: ControlGroup,
    target: str,
    *,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        namespace = _control_namespace(hue, group)
        resource_id = await _resolve_target(namespace, target, fuzzy=fuzzy)
        return await namespace.identify(resource_id)


async def activate_scene(
    target: str,
    *,
    brightness: float | None,
    transition: float | None,
    dynamic: bool,
    fuzzy: bool = True,
    room: str | None = None,
    zone: str | None = None,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        if room is not None and zone is not None:
            raise ValueError("Choose either --room or --zone, not both")
        group_id = None
        if room is not None:
            group_id = await _resolve_target(hue.rooms, room, fuzzy=fuzzy)
        elif zone is not None:
            group_id = await _resolve_target(hue.zones, zone, fuzzy=fuzzy)
        try:
            UUID(target)
        except ValueError:
            if group_id is not None:
                resource_id = (
                    await hue.scenes.find_by_name(
                        target, group_id=group_id, fuzzy=fuzzy
                    )
                ).id
            else:
                resource_id = await _resolve_target(hue.scenes, target, fuzzy=fuzzy)
        else:
            resource_id = target
            if group_id is not None and str(
                (await hue.scenes.get_one(target)).group.rid
            ) != str(group_id):
                raise ResourceNotFoundError(
                    f"Scene {target} does not belong to group {group_id}"
                )
        return await hue.scenes.activate(
            resource_id,
            brightness=brightness,
            transition=transition,
            dynamic=dynamic,
        )


async def start_entertainment_area(
    target: str,
    *,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        resource_id = await _resolve_target(hue.entertainment, target, fuzzy=fuzzy)
        return await hue.entertainment.start(resource_id)


async def stop_entertainment_area(
    target: str,
    *,
    fuzzy: bool = True,
) -> HueApiResponse[ResourceIdentifier]:
    async with Hueify() as hue:
        resource_id = await _resolve_target(hue.entertainment, target, fuzzy=fuzzy)
        return await hue.entertainment.stop(resource_id)
