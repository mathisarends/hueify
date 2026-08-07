import re
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import UUID

import httpx
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from hueify import cli
from hueify.cli import app
from hueify.errors import HueifyError, MissingCredentialsError
from hueify.models import (
    EntertainmentConfiguration,
    GroupArchetype,
    GroupMetadata,
    HueApiResponse,
    Light,
    LightMetadata,
    NamedMetadata,
    OnState,
    ResourceIdentifier,
    ResourceReference,
    ResourceType,
    Room,
    Scene,
    SceneMetadata,
    SceneStatus,
    SceneStatusValue,
    StreamingStatus,
    Zone,
)

runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

RESOURCE_ID = UUID("a1b2c3d4-1111-2222-3333-444455556666")
OWNER_ID = UUID("b1b2c3d4-1111-2222-3333-444455556666")


def bridge_mock() -> MagicMock:
    bridge = MagicMock()
    bridge.__aenter__ = AsyncMock(return_value=bridge)
    bridge.__aexit__ = AsyncMock(return_value=None)
    return bridge


def update_response() -> HueApiResponse[ResourceIdentifier]:
    return HueApiResponse[ResourceIdentifier](
        data=[ResourceIdentifier(rid=RESOURCE_ID, rtype=ResourceType.LIGHT)]
    )


def test_setup_command_runs_the_interactive_onboarding() -> None:
    with patch("hueify.onboarding.setup.setup") as setup:
        result = runner.invoke(app, ["setup"])

    assert result.exit_code == 0
    setup.assert_called_once_with()


def test_bare_invocation_prints_contextual_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 2
    output = ANSI_ESCAPE.sub("", result.output)
    assert "setup" in output
    assert "--json" in output


def test_main_forwards_arguments_to_the_public_application() -> None:
    command = MagicMock()

    with patch.object(cli, "app", command):
        result = cli.main(["--version"])

    assert result == 0
    command.assert_called_once_with(args=["--version"], prog_name="hueify")


def test_main_explains_how_to_install_the_optional_cli_extra(capsys) -> None:
    with patch.object(cli, "app", None), pytest.raises(SystemExit) as exit_info:
        cli.main([])

    assert exit_info.value.code == 1
    assert "hueify[cli]" in capsys.readouterr().err


def test_the_global_output_modes_are_mutually_exclusive() -> None:
    result = runner.invoke(app, ["version-info", "--json", "--plain"])

    assert result.exit_code == 2
    assert "either --json or --plain" in ANSI_ESCAPE.sub("", result.output)


def test_version_info_has_human_plain_and_json_forms() -> None:
    eager = runner.invoke(app, ["--version"])
    plain = runner.invoke(app, ["--plain", "version-info"])
    structured = runner.invoke(app, ["--json", "version-info"])
    human = runner.invoke(app, ["version-info"])

    assert eager.exit_code == plain.exit_code == structured.exit_code == 0
    assert human.exit_code == 0
    assert eager.output.strip()
    assert plain.output.strip()
    assert '"version"' in structured.output
    assert human.output.startswith("Hueify ")


def test_light_list_uses_the_hueify_api_and_writes_stable_plain_output() -> None:
    light = Light(
        id=RESOURCE_ID,
        metadata=LightMetadata(name="Desk"),
        owner=ResourceReference(
            rid=OWNER_ID,
            rtype=ResourceType.DEVICE,
        ),
        on=OnState(on=True),
    )
    hue = bridge_mock()
    hue.lights.list = AsyncMock(return_value=SimpleNamespace(data=[light]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(app, ["--plain", "light", "list"])

    assert result.exit_code == 0
    assert result.output == f"{light.id}\tDesk\ton\n"
    hue.lights.list.assert_awaited_once_with()


def test_resource_list_json_preserves_the_full_model_shape() -> None:
    light = Light(
        id=RESOURCE_ID,
        metadata=LightMetadata(name="Desk"),
        owner=ResourceReference(rid=OWNER_ID, rtype=ResourceType.DEVICE),
        on=OnState(on=False),
    )
    hue = bridge_mock()
    hue.lights.list = AsyncMock(return_value=SimpleNamespace(data=[light]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(app, ["light", "list", "--json"])
        plain_result = runner.invoke(app, ["light", "--plain", "list"])

    assert result.exit_code == 0
    assert plain_result.exit_code == 0
    assert str(RESOURCE_ID) in result.output
    assert '"metadata"' in result.output
    assert plain_result.output.endswith("\tDesk\toff\n")


def test_no_color_is_accepted_after_the_subcommand() -> None:
    light = Light(
        id=RESOURCE_ID,
        metadata=LightMetadata(name="Desk"),
        owner=ResourceReference(rid=OWNER_ID, rtype=ResourceType.DEVICE),
        on=OnState(on=True),
    )
    hue = bridge_mock()
    hue.lights.list = AsyncMock(return_value=SimpleNamespace(data=[light]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(
            app,
            ["light", "list", "--no-color"],
            env={"FORCE_COLOR": "1"},
        )

    assert result.exit_code == 0
    assert "\x1b[" not in result.output
    assert "Desk" in result.output


def test_every_resource_app_lists_its_typed_models_in_human_output() -> None:
    group_metadata = GroupMetadata(
        name="Kitchen",
        archetype=GroupArchetype.KITCHEN,
    )
    reference = ResourceReference(rid=OWNER_ID, rtype=ResourceType.ROOM)
    room = Room(id=RESOURCE_ID, metadata=group_metadata)
    zone = Zone(id=RESOURCE_ID, metadata=group_metadata)
    scene = Scene(
        id=RESOURCE_ID,
        metadata=SceneMetadata(name="Dinner"),
        group=reference,
        status=SceneStatus(active=SceneStatusValue.ACTIVE),
    )
    area = EntertainmentConfiguration(
        id=RESOURCE_ID,
        metadata=NamedMetadata(name="TV"),
        status=StreamingStatus.ACTIVE,
    )
    hue = bridge_mock()
    hue.rooms.list = AsyncMock(return_value=SimpleNamespace(data=[room]))
    hue.zones.list = AsyncMock(return_value=SimpleNamespace(data=[zone]))
    hue.scenes.list = AsyncMock(return_value=SimpleNamespace(data=[scene]))
    hue.entertainment.list = AsyncMock(return_value=SimpleNamespace(data=[area]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        results = [
            runner.invoke(app, [group, "list"])
            for group in ("room", "zone", "scene", "entertainment")
        ]

    assert all(result.exit_code == 0 for result in results)
    assert "Kitchen" in results[0].output
    assert "Kitchen" in results[1].output
    assert "Dinner" in results[2].output
    assert "active=<" not in results[2].output
    assert "last_recall" not in results[2].output
    assert "active" in results[3].output
    hue.rooms.list.assert_awaited_once_with()
    hue.zones.list.assert_awaited_once_with()
    hue.scenes.list.assert_awaited_once_with()
    hue.entertainment.list.assert_awaited_once_with()


def test_scene_list_renders_only_the_active_status_value() -> None:
    scene = Scene(
        id=RESOURCE_ID,
        metadata=SceneMetadata(name="Dinner"),
        group=ResourceReference(rid=OWNER_ID, rtype=ResourceType.ROOM),
        status=SceneStatus(
            active=SceneStatusValue.DYNAMIC_PALETTE,
            last_recall="2026-08-07T20:00:00Z",
        ),
    )
    hue = bridge_mock()
    hue.scenes.list = AsyncMock(return_value=SimpleNamespace(data=[scene]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(app, ["--plain", "scene", "list"])

    assert result.exit_code == 0
    assert result.output == f"{RESOURCE_ID}\tDinner\tdynamic_palette\n"


def test_light_on_resolves_a_name_and_passes_all_control_options() -> None:
    resource_id = UUID("a1b2c3d4-1111-2222-3333-444455556666")
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.lights.find_by_name = AsyncMock(return_value=SimpleNamespace(id=resource_id))
    hue.lights.turn_on = AsyncMock(return_value=SimpleNamespace(data=[]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(
            app,
            [
                "light",
                "on",
                "Desk",
                "--brightness",
                "60",
                "--transition",
                "0.3",
            ],
        )

    assert result.exit_code == 0
    hue.lights.find_by_name.assert_awaited_once_with("Desk")
    hue.lights.turn_on.assert_awaited_once_with(
        resource_id, brightness=60.0, transition=0.3
    )
    assert result.output == "Updated 0 resource(s).\n"


def test_light_off_uses_a_uuid_without_an_unnecessary_lookup() -> None:
    resource_id = "a1b2c3d4-1111-2222-3333-444455556666"
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.lights.turn_off = AsyncMock(return_value=SimpleNamespace(data=[]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(app, ["light", "off", resource_id])

    assert result.exit_code == 0
    hue.lights.find_by_name.assert_not_called()
    hue.lights.turn_off.assert_awaited_once_with(resource_id, transition=None)


def test_shared_control_commands_dispatch_to_the_selected_namespace() -> None:
    response = update_response()
    hue = bridge_mock()
    hue.lights.find_by_name = AsyncMock(return_value=SimpleNamespace(id=RESOURCE_ID))
    hue.rooms.find_by_name = AsyncMock(return_value=SimpleNamespace(id=RESOURCE_ID))
    hue.zones.find_by_name = AsyncMock(return_value=SimpleNamespace(id=RESOURCE_ID))
    hue.rooms.toggle = AsyncMock(return_value=response)
    hue.zones.set_brightness = AsyncMock(return_value=response)
    hue.lights.set_hex = AsyncMock(return_value=response)
    hue.rooms.set_color_temperature = AsyncMock(return_value=response)
    hue.zones.identify = AsyncMock(return_value=response)

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        toggle_result = runner.invoke(
            app, ["room", "toggle", "Kitchen", "--transition", "0.2"]
        )
        brightness_result = runner.invoke(
            app,
            ["zone", "brightness", "Upstairs", "42", "--transition", "0.4"],
        )
        color_result = runner.invoke(
            app,
            [
                "--json",
                "light",
                "color",
                "Desk",
                "#ff00aa",
                "--brightness",
                "80",
                "--transition",
                "0.1",
            ],
        )
        temperature_result = runner.invoke(
            app,
            [
                "--plain",
                "room",
                "temperature",
                "Kitchen",
                "2700",
                "--brightness",
                "50",
            ],
        )
        identify_result = runner.invoke(app, ["zone", "identify", "Upstairs"])

    assert all(
        result.exit_code == 0
        for result in (
            toggle_result,
            brightness_result,
            color_result,
            temperature_result,
            identify_result,
        )
    )
    hue.rooms.toggle.assert_awaited_once_with(RESOURCE_ID, transition=0.2)
    hue.zones.set_brightness.assert_awaited_once_with(RESOURCE_ID, 42.0, transition=0.4)
    hue.lights.set_hex.assert_awaited_once_with(
        RESOURCE_ID,
        "#ff00aa",
        brightness=80.0,
        transition=0.1,
    )
    hue.rooms.set_color_temperature.assert_awaited_once_with(
        RESOURCE_ID,
        2700,
        brightness=50.0,
        transition=None,
    )
    hue.zones.identify.assert_awaited_once_with(RESOURCE_ID)
    assert '"data"' in color_result.output
    assert temperature_result.output == f"{RESOURCE_ID}\tlight\n"
    assert hue.rooms.find_by_name.await_args_list == [call("Kitchen"), call("Kitchen")]
    assert hue.zones.find_by_name.await_args_list == [
        call("Upstairs"),
        call("Upstairs"),
    ]


def test_scene_activate_uses_the_scene_api() -> None:
    resource_id = UUID("a1b2c3d4-1111-2222-3333-444455556666")
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.scenes.find_by_name = AsyncMock(return_value=SimpleNamespace(id=resource_id))
    hue.scenes.activate = AsyncMock(return_value=SimpleNamespace(data=[]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(
            app,
            ["scene", "activate", "Movie time", "--brightness", "35", "--dynamic"],
        )

    assert result.exit_code == 0
    hue.scenes.activate.assert_awaited_once_with(
        resource_id, brightness=35.0, transition=None, dynamic=True
    )


def test_entertainment_start_resolves_the_area_name() -> None:
    resource_id = UUID("a1b2c3d4-1111-2222-3333-444455556666")
    hue = MagicMock()
    hue.__aenter__ = AsyncMock(return_value=hue)
    hue.__aexit__ = AsyncMock(return_value=None)
    hue.entertainment.find_by_name = AsyncMock(
        return_value=SimpleNamespace(id=resource_id)
    )
    hue.entertainment.start = AsyncMock(return_value=SimpleNamespace(data=[]))

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(app, ["entertainment", "start", "TV"])

    assert result.exit_code == 0
    hue.entertainment.start.assert_awaited_once_with(resource_id)


def test_scene_and_entertainment_accept_uuids_without_name_lookups() -> None:
    resource_id = str(RESOURCE_ID)
    response = update_response()
    hue = bridge_mock()
    hue.scenes.activate = AsyncMock(return_value=response)
    hue.entertainment.stop = AsyncMock(return_value=response)

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        scene_result = runner.invoke(app, ["scene", "activate", resource_id])
        stop_result = runner.invoke(app, ["entertainment", "stop", resource_id])

    assert scene_result.exit_code == stop_result.exit_code == 0
    hue.scenes.find_by_name.assert_not_called()
    hue.entertainment.find_by_name.assert_not_called()
    hue.scenes.activate.assert_awaited_once_with(
        resource_id,
        brightness=None,
        transition=None,
        dynamic=False,
    )
    hue.entertainment.stop.assert_awaited_once_with(resource_id)


def test_missing_credentials_are_a_clean_error_with_a_stable_exit_code() -> None:
    with patch(
        "hueify.cli.operations.Hueify",
        side_effect=MissingCredentialsError("HUE_APP_KEY is missing"),
    ):
        result = runner.invoke(app, ["light", "list"])

    assert result.exit_code == 3
    assert result.output == "HUE_APP_KEY is missing\n"


@pytest.mark.parametrize(
    ("error", "exit_code"),
    [
        (ValueError("invalid command value"), 2),
        (HueifyError("bridge rejected the command"), 1),
        (httpx.ConnectError("bridge is offline"), 4),
    ],
)
def test_bridge_failures_have_stable_exit_codes(
    error: Exception,
    exit_code: int,
) -> None:
    with patch("hueify.cli.operations.Hueify", side_effect=error):
        result = runner.invoke(app, ["light", "list"])

    assert result.exit_code == exit_code
    assert result.output == f"{error}\n"


def test_pydantic_validation_errors_are_concise_cli_errors() -> None:
    try:
        from hueify.models import DimmingState

        DimmingState(brightness=150)
    except ValidationError as error:
        validation_error = error
    else:  # pragma: no cover - the model constraint is part of the public API
        pytest.fail("Expected brightness validation to fail")

    hue = bridge_mock()
    hue.lights.set_brightness = AsyncMock(side_effect=validation_error)

    with patch("hueify.cli.operations.Hueify", return_value=hue):
        result = runner.invoke(
            app,
            ["light", "brightness", str(RESOURCE_ID), "150"],
        )

    assert result.exit_code == 2
    assert result.output == (
        "Invalid brightness: Input should be less than or equal to 100\n"
    )
    assert "pydantic.dev" not in result.output
