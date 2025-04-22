import unittest
from unittest.mock import AsyncMock, MagicMock
import asyncio

from hueify.controllers.group_controller import GroupController


class TestGroupController(unittest.TestCase):
    def setUp(self):
        self.bridge_mock = MagicMock()
        self.bridge_mock.get_request = AsyncMock()
        self.bridge_mock.put_request = AsyncMock()

        self.test_groups = {
            "1": {
                "name": "Wohnzimmer",
                "lights": ["1", "2", "3"],
                "type": "Room",
                "state": {"all_on": False, "any_on": True},
                "recycle": False,
                "class_": "Living room",
                "action": {
                    "on": True,
                    "bri": 144,
                    "hue": 8402,
                    "sat": 140,
                    "effect": "none",
                    "xy": [0.4575, 0.4101],
                    "ct": 366,
                    "alert": "none",
                    "colormode": "ct",
                },
            }
        }

        self.test_group_info = {
            "name": "Wohnzimmer",
            "lights": ["1", "2", "3"],
            "type": "Room",
            "state": {"all_on": False, "any_on": True},
            "recycle": False,
            "class_": "Living room",
            "action": {
                "on": True,
                "bri": 144,
                "hue": 8402,
                "sat": 140,
                "effect": "none",
                "xy": [0.4575, 0.4101],
                "ct": 366,
                "alert": "none",
                "colormode": "ct",
            },
        }

        self.bridge_mock.get_request.side_effect = self.mock_get_request
        self.bridge_mock.put_request.side_effect = self.mock_put_request

        self.controller = GroupController(self.bridge_mock, "Wohnzimmer")

    async def mock_get_request(self, endpoint):
        """Mock für bridge.get_request"""
        if endpoint == "groups":
            return self.test_groups
        elif endpoint == "groups/1":
            return self.test_group_info
        else:
            return {}

    async def mock_put_request(self, endpoint, data):
        """Mock für bridge.put_request"""
        return [
            {
                "success": {f"/groups/1/action/{key}": value}
                for key, value in data.items()
            }
        ]

    async def async_test(self, coroutine):
        """Hilfsmethode zum Ausführen von async Tests"""
        return await coroutine

    def test_initialize(self):
        # Test, dass initialize die Gruppe korrekt auflöst
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.controller.initialize())

        self.assertEqual(self.controller._group_id, "1")
        self.assertEqual(self.controller._group_info, self.test_group_info)

    def test_turn_on(self):
        # Test, dass turn_on den richtigen API-Call macht
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.controller.initialize())

        # Führe turn_on aus
        result = loop.run_until_complete(self.controller.turn_on())

        # Überprüfe, dass der richtige API-Call gemacht wurde
        self.bridge_mock.put_request.assert_called_with(
            "groups/1/action", {"on": True, "transitiontime": 4}
        )

    def test_set_brightness(self):
        # Test, dass set_brightness_percentage die Helligkeit korrekt setzt
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.controller.initialize())

        # Setze Helligkeit auf 50%
        result = loop.run_until_complete(self.controller.set_brightness_percentage(50))

        # Berechne erwarteten Helligkeitswert (50% von 254)
        expected_brightness = round(50 * 254 / 100)

        # Überprüfe, dass der richtige API-Call gemacht wurde
        self.bridge_mock.put_request.assert_called_with(
            "groups/1/action",
            {"on": True, "bri": expected_brightness, "transitiontime": None},
        )


if __name__ == "__main__":
    unittest.main()
