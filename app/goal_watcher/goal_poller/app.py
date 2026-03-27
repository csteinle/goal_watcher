"""Goal poller Lambda handler.

Runs every 60 seconds (only when enabled by fixture checker).
Polls ESPN for live match scores, detects new goals, and notifies SmartThings devices.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from app.goal_watcher.model.match_state import ActiveFixture, MatchStatus
from app.goal_watcher.shared.dynamo import (
    get_installations_for_team,
    get_live_fixtures,
    get_match_state,
    put_match_state,
    update_fixture_status,
)
from app.goal_watcher.shared.espn_client import EspnClient, EspnClientError

from .goal_detector import GoalEvent, build_match_state_from_event, detect_goals
from .smartthings_notifier import SmartThingsNotifier

logger = Logger()
tracer = Tracer()

MATCH_STATE_TABLE = os.environ.get("MATCH_STATE_TABLE_NAME", "goal-watcher-match-state")
FIXTURES_TABLE = os.environ.get("FIXTURES_TABLE_NAME", "goal-watcher-fixtures")
INSTALLATIONS_TABLE = os.environ.get("INSTALLATIONS_TABLE_NAME", "goal-watcher-installations")


async def _process_fixture(
    fixture: ActiveFixture,
    event_lookup: dict[str, tuple[str, Any]],
    espn: EspnClient,
    notifier: SmartThingsNotifier,
) -> tuple[int, int]:
    """Process a single live fixture. Returns (goals_detected, notifications_sent)."""
    if fixture.event_id not in event_lookup:
        logger.warning("Fixture %s not found in scoreboard — may have ended", fixture.event_id)
        update_fixture_status(FIXTURES_TABLE, fixture.event_id, MatchStatus.COMPLETED)
        return 0, 0

    league_slug, event = event_lookup[fixture.event_id]

    current_state = build_match_state_from_event(event, league_slug)
    if not current_state:
        return 0, 0

    previous_state = get_match_state(MATCH_STATE_TABLE, fixture.event_id)

    key_events = None
    try:
        summary = await espn.fetch_match_summary(league_slug, fixture.event_id)
        key_events = summary.key_events
    except EspnClientError:
        logger.warning("Could not fetch summary for event %s", fixture.event_id)

    goals = detect_goals(previous_state, current_state, key_events)

    notifications = 0
    if goals:
        for goal in goals:
            notifications += await _notify_for_goal(goal, notifier)

    put_match_state(MATCH_STATE_TABLE, current_state)

    if current_state.status == MatchStatus.COMPLETED:
        update_fixture_status(FIXTURES_TABLE, fixture.event_id, MatchStatus.COMPLETED)
        logger.info("Match %s completed: %s", fixture.event_id, current_state)

    return len(goals), notifications


async def _poll_and_notify() -> dict[str, Any]:
    """Core polling and notification logic."""
    espn = EspnClient()
    notifier = SmartThingsNotifier()

    # Get all live fixtures
    live_fixtures = get_live_fixtures(FIXTURES_TABLE)
    if not live_fixtures:
        logger.info("No live fixtures — nothing to poll")
        return {"matches_polled": 0, "goals_detected": 0, "notifications_sent": 0}

    logger.info("Polling %d live fixture(s)", len(live_fixtures))

    total_goals = 0
    total_notifications = 0

    # Group fixtures by league for efficient API calls
    leagues_to_poll: set[str] = {f.league_slug for f in live_fixtures}
    scoreboards = await espn.fetch_scoreboards(list(leagues_to_poll))

    # Build a lookup of event_id → ESPN event
    event_lookup: dict[str, tuple[str, Any]] = {}
    for league_slug, scoreboard in scoreboards.items():
        for event in scoreboard.events:
            event_lookup[event.id] = (league_slug, event)

    for fixture in live_fixtures:
        fixture_goals, fixture_notifications = await _process_fixture(
            fixture,
            event_lookup,
            espn,
            notifier,
        )
        total_goals += fixture_goals
        total_notifications += fixture_notifications

    return {
        "matches_polled": len(live_fixtures),
        "goals_detected": total_goals,
        "notifications_sent": total_notifications,
    }


async def _notify_for_goal(goal: GoalEvent, notifier: SmartThingsNotifier) -> int:
    """Send notifications for a single goal event. Returns notification count."""
    installations = get_installations_for_team(INSTALLATIONS_TABLE, goal.scoring_team_id)
    if not installations:
        logger.info("No installations tracking team %s — skipping notification", goal.scoring_team_id)
        return 0

    count = 0
    for installation in installations:
        try:
            await notifier.notify_installation(installation, goal.description)
            count += 1
        except Exception:
            logger.exception(
                "Failed to notify installation %s for goal",
                installation.installed_app_id,
            )

    return count


@logger.inject_lambda_context(clear_state=True)
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda handler for the goal poller."""
    logger.info("Goal poller invoked")
    result = asyncio.run(_poll_and_notify())
    logger.info("Goal poll complete: %s", result)
    return result
