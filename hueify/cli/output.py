import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import typer
from pydantic import JsonValue
from rich.console import Console
from rich.table import Table
from typer import Context

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

type ListedResource = Light | Room | Zone | Scene | EntertainmentConfiguration


@dataclass(frozen=True, slots=True)
class OutputOptions:
    """Global output settings, shared by every command."""

    json: bool
    plain: bool
    no_color: bool

    @classmethod
    def from_context(cls, context: Context) -> "OutputOptions":
        if not isinstance(context.obj, cls):
            raise RuntimeError("The CLI output context has not been initialised")
        return context.obj


def print_json(value: JsonValue) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _resource_json(resource: NamedResource) -> dict[str, JsonValue]:
    # Pydantic's return annotation is deliberately broad. At mode="json" this
    # cast records the narrower guarantee made by Pydantic's serializer.
    return cast("dict[str, JsonValue]", resource.model_dump(mode="json"))


def _resource_state(resource: ListedResource) -> str:
    match resource:
        case Light(is_on=True):
            return "on"
        case Light(is_on=False):
            return "off"
        case Light():
            return ""
        case Scene(status=status) if status is not None:
            return str(status)
        case EntertainmentConfiguration(status=status) if status is not None:
            return str(status)
        case Room() | Zone() | Scene() | EntertainmentConfiguration():
            return ""


def write_resources(
    context: Context,
    resources: Sequence[ListedResource],
    title: str,
) -> None:
    output = OutputOptions.from_context(context)
    if output.json:
        print_json([_resource_json(resource) for resource in resources])
        return

    rows = [
        (str(resource.id), resource.name, _resource_state(resource))
        for resource in resources
    ]
    if output.plain:
        for row in rows:
            typer.echo("\t".join(row))
        return

    table = Table(title=title)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("State")
    for row in rows:
        table.add_row(*row)
    Console(no_color=output.no_color).print(table)


def write_response(
    context: Context,
    response: HueApiResponse[ResourceIdentifier],
) -> None:
    output = OutputOptions.from_context(context)
    if output.json:
        print_json(cast("dict[str, JsonValue]", response.model_dump(mode="json")))
        return

    if output.plain:
        for identifier in response.data:
            typer.echo(f"{identifier.rid}\t{identifier.rtype}")
        return
    typer.echo(f"Updated {len(response.data)} resource(s).")
