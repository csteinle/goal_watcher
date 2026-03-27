"""Tests for the SmartThings notifier."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.goal_watcher.goal_poller.smartthings_notifier import (
    FLASH_REPEAT_COUNT,
    SmartThingsNotifier,
    SmartThingsNotifierError,
)
from app.goal_watcher.model.installation import DeviceConfig, Installation


def _make_installation(
    *,
    installed_app_id: str = "app-001",
    team_id: str = "254",
    team_name: str = "Falkirk",
    auth_token: str = "tok_abc123",
    light_ids: list[str] | None = None,
    switch_ids: list[str] | None = None,
) -> Installation:
    return Installation(
        installed_app_id=installed_app_id,
        team_id=team_id,
        team_name=team_name,
        auth_token=auth_token,
        devices=DeviceConfig(
            light_device_ids=light_ids or [],
            switch_device_ids=switch_ids or [],
        ),
    )


def _mock_httpx_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(spec=httpx.Request),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestSendDeviceCommand:
    async def test_success_correct_http_call(self) -> None:
        mock_response = _mock_httpx_response(200)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.goal_poller.smartthings_notifier.httpx.AsyncClient", return_value=mock_client):
            notifier = SmartThingsNotifier()
            await notifier.send_device_command("tok_abc", "dev-1", "switch", "on")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        url = call_args[0][0]
        assert "devices/dev-1/commands" in url

        body = call_args[1]["json"]
        assert body["commands"][0]["capability"] == "switch"
        assert body["commands"][0]["command"] == "on"

        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer tok_abc"

    async def test_http_error_raises_notifier_error(self) -> None:
        mock_response = _mock_httpx_response(500)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.goal_watcher.goal_poller.smartthings_notifier.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(SmartThingsNotifierError, match="SmartThings command failed"),
        ):
            notifier = SmartThingsNotifier()
            await notifier.send_device_command("tok_abc", "dev-1", "switch", "on")


class TestFlashLights:
    @patch("app.goal_watcher.goal_poller.smartthings_notifier.asyncio.sleep", new_callable=AsyncMock)
    async def test_calls_on_off_in_sequence(self, mock_sleep: AsyncMock) -> None:
        notifier = SmartThingsNotifier()
        notifier.send_device_command = AsyncMock()

        device_ids = ["light-1", "light-2"]
        await notifier.flash_lights("tok_abc", device_ids)

        # Each repeat: on for each device, sleep, off for each device, sleep
        # Then final on for each device
        # total send_device_command calls = FLASH_REPEAT_COUNT * (2 * len(devices)) + len(devices)
        expected_calls = FLASH_REPEAT_COUNT * (2 * len(device_ids)) + len(device_ids)
        assert notifier.send_device_command.call_count == expected_calls

        # Verify sleep was called for each on/off cycle
        assert mock_sleep.call_count == FLASH_REPEAT_COUNT * 2

        # Verify last calls are "on" (leave lights on at end)
        last_calls = notifier.send_device_command.call_args_list[-len(device_ids) :]
        for call in last_calls:
            assert call[0][3] == "on"


class TestNotifyInstallation:
    @patch("app.goal_watcher.goal_poller.smartthings_notifier.asyncio.sleep", new_callable=AsyncMock)
    async def test_calls_flash_lights_and_toggle_switches(self, _mock_sleep: AsyncMock) -> None:
        notifier = SmartThingsNotifier()
        notifier.flash_lights = AsyncMock()
        notifier.toggle_switches = AsyncMock()

        installation = _make_installation(
            auth_token="tok_abc",
            light_ids=["light-1"],
            switch_ids=["switch-1"],
        )

        await notifier.notify_installation(installation, "⚽ GOAL!")

        notifier.flash_lights.assert_called_once_with("tok_abc", ["light-1"])
        notifier.toggle_switches.assert_called_once_with("tok_abc", ["switch-1"])

    async def test_skips_if_no_auth_token(self) -> None:
        notifier = SmartThingsNotifier()
        notifier.flash_lights = AsyncMock()
        notifier.toggle_switches = AsyncMock()

        installation = _make_installation(
            auth_token="",
            light_ids=["light-1"],
            switch_ids=["switch-1"],
        )

        await notifier.notify_installation(installation, "⚽ GOAL!")

        notifier.flash_lights.assert_not_called()
        notifier.toggle_switches.assert_not_called()
