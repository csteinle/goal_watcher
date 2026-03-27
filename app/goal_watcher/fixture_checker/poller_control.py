"""Poller control — enables and disables the goal poller CloudWatch Events rule."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from types_boto3_events import EventBridgeClient
else:
    EventBridgeClient = object

logger = logging.getLogger(__name__)


def _get_events_client() -> EventBridgeClient:
    return boto3.client("events")


def enable_goal_poller(rule_name: str) -> None:
    """Enable the goal poller CloudWatch Events rule."""
    client = _get_events_client()
    client.enable_rule(Name=rule_name)
    logger.info("Enabled goal poller rule: %s", rule_name)


def disable_goal_poller(rule_name: str) -> None:
    """Disable the goal poller CloudWatch Events rule."""
    client = _get_events_client()
    client.disable_rule(Name=rule_name)
    logger.info("Disabled goal poller rule: %s", rule_name)


def is_goal_poller_enabled(rule_name: str) -> bool:
    """Check if the goal poller CloudWatch Events rule is currently enabled."""
    client = _get_events_client()
    response = client.describe_rule(Name=rule_name)
    state = response.get("State", "DISABLED")
    return state == "ENABLED"
