"""Pydantic models for SmartApp installation records in DynamoDB."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceConfig(BaseModel):
    """Device configuration from SmartApp installation."""

    light_device_ids: list[str] = Field(default_factory=list)
    switch_device_ids: list[str] = Field(default_factory=list)


class Installation(BaseModel):
    """A SmartApp installation record — stored in DynamoDB by the Node.js SmartApp."""

    installed_app_id: str
    team_id: str
    team_name: str = ""
    competitions: list[str] = Field(default_factory=list)
    devices: DeviceConfig = Field(default_factory=DeviceConfig)
    auth_token: str = ""
    refresh_token: str = ""
    token_expiry: str = ""
    location_id: str = ""
    last_updated: str = ""
