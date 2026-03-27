"""SmartThings REST API notifier — sends device commands when goals are scored."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.goal_watcher.model.installation import Installation

logger = logging.getLogger(__name__)

SMARTTHINGS_API_BASE = "https://api.smartthings.com/v1"
DEFAULT_TIMEOUT = 10.0
FLASH_DELAY_SECONDS = 2.0
FLASH_REPEAT_COUNT = 3


class SmartThingsNotifierError(Exception):
    """Raised when a SmartThings API call fails."""


class SmartThingsNotifier:
    """Client for the SmartThings REST API to control devices."""

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def _headers(self, auth_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

    async def send_device_command(
        self,
        auth_token: str,
        device_id: str,
        capability: str,
        command: str,
        arguments: list[Any] | None = None,
    ) -> None:
        """Send a single command to a SmartThings device."""
        url = f"{SMARTTHINGS_API_BASE}/devices/{device_id}/commands"
        body = {
            "commands": [
                {
                    "component": "main",
                    "capability": capability,
                    "command": command,
                    **({"arguments": arguments} if arguments else {}),
                },
            ],
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, json=body, headers=self._headers(auth_token))
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = f"SmartThings command failed for device {device_id}: {exc}"
                logger.warning(msg)
                raise SmartThingsNotifierError(msg) from exc

    async def flash_lights(self, auth_token: str, device_ids: list[str]) -> None:
        """Flash a set of lights on and off."""
        for _ in range(FLASH_REPEAT_COUNT):
            for device_id in device_ids:
                await self.send_device_command(auth_token, device_id, "switch", "on")
            await asyncio.sleep(FLASH_DELAY_SECONDS)
            for device_id in device_ids:
                await self.send_device_command(auth_token, device_id, "switch", "off")
            await asyncio.sleep(FLASH_DELAY_SECONDS)

        # Leave lights on at the end as a visual indicator
        for device_id in device_ids:
            await self.send_device_command(auth_token, device_id, "switch", "on")

    async def toggle_switches(self, auth_token: str, device_ids: list[str]) -> None:
        """Toggle switches on then off."""
        for device_id in device_ids:
            await self.send_device_command(auth_token, device_id, "switch", "on")

        await asyncio.sleep(FLASH_DELAY_SECONDS * 2)

        for device_id in device_ids:
            await self.send_device_command(auth_token, device_id, "switch", "off")

    async def notify_installation(
        self,
        installation: Installation,
        goal_description: str,
    ) -> None:
        """Trigger all configured devices for an installation when a goal is scored."""
        token = installation.auth_token
        if not token:
            logger.warning("No auth token for installation %s — skipping", installation.installed_app_id)
            return

        logger.info("Notifying installation %s: %s", installation.installed_app_id, goal_description)

        # Flash lights
        if installation.devices.light_device_ids:
            try:
                await self.flash_lights(token, installation.devices.light_device_ids)
            except SmartThingsNotifierError:
                logger.exception("Failed to flash lights for installation %s", installation.installed_app_id)

        # Toggle switches
        if installation.devices.switch_device_ids:
            try:
                await self.toggle_switches(token, installation.devices.switch_device_ids)
            except SmartThingsNotifierError:
                logger.exception("Failed to toggle switches for installation %s", installation.installed_app_id)
