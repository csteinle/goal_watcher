"""DynamoDB helpers for reading and writing match state, fixtures, and installations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import boto3

from app.goal_watcher.model.installation import Installation
from app.goal_watcher.model.match_state import ActiveFixture, MatchState, MatchStatus

if TYPE_CHECKING:
    from types_boto3_dynamodb.service_resource import Table
else:
    Table = object

logger = logging.getLogger(__name__)


def _get_table(table_name: str) -> Table:
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(table_name)


# --- Match State ---


def get_match_state(table_name: str, event_id: str) -> MatchState | None:
    """Get stored match state for an event."""
    table = _get_table(table_name)
    response = table.get_item(Key={"event_id": event_id})
    item = response.get("Item")
    if not item:
        return None
    return MatchState.model_validate(item)


def put_match_state(table_name: str, state: MatchState) -> None:
    """Store or update match state."""
    table = _get_table(table_name)
    table.put_item(Item=state.model_dump())


def delete_match_state(table_name: str, event_id: str) -> None:
    """Delete match state for a completed event."""
    table = _get_table(table_name)
    table.delete_item(Key={"event_id": event_id})


# --- Active Fixtures ---


def get_active_fixtures(table_name: str) -> list[ActiveFixture]:
    """Get all active (non-completed) fixtures."""
    table = _get_table(table_name)
    response = table.scan(
        FilterExpression="#s <> :completed",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":completed": MatchStatus.COMPLETED},
    )
    items: list[dict[str, Any]] = response.get("Items", [])
    return [ActiveFixture.model_validate(item) for item in items]


def get_live_fixtures(table_name: str) -> list[ActiveFixture]:
    """Get all fixtures currently live."""
    table = _get_table(table_name)
    response = table.scan(
        FilterExpression="#s = :live",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":live": MatchStatus.LIVE},
    )
    items: list[dict[str, Any]] = response.get("Items", [])
    return [ActiveFixture.model_validate(item) for item in items]


def put_fixture(table_name: str, fixture: ActiveFixture) -> None:
    """Store or update an active fixture."""
    table = _get_table(table_name)
    table.put_item(Item=fixture.model_dump())


def update_fixture_status(table_name: str, event_id: str, status: MatchStatus) -> None:
    """Update the status of an active fixture."""
    table = _get_table(table_name)
    table.update_item(
        Key={"event_id": event_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": status},
    )


# --- Installations ---


def get_installations_for_team(table_name: str, team_id: str) -> list[Installation]:
    """Get all SmartApp installations tracking a specific team."""
    table = _get_table(table_name)
    response = table.scan(
        FilterExpression="team_id = :team_id",
        ExpressionAttributeValues={":team_id": team_id},
    )
    items: list[dict[str, Any]] = response.get("Items", [])
    return [Installation.model_validate(item) for item in items]


def get_all_tracked_team_ids(table_name: str) -> set[str]:
    """Get all unique team IDs being tracked across all installations."""
    table = _get_table(table_name)
    response = table.scan(ProjectionExpression="team_id")
    items: list[dict[str, Any]] = response.get("Items", [])
    return {item["team_id"] for item in items if "team_id" in item}
