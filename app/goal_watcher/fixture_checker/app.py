"""Fixture checker Lambda handler.

Runs on a 15-minute schedule. Scans ESPN for matches involving tracked teams,
updates DynamoDB active_fixtures, and enables/disables the goal poller.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from app.goal_watcher.model.match_state import MatchStatus
from app.goal_watcher.shared.dynamo import (
    get_active_fixtures,
    get_all_tracked_team_ids,
    put_fixture,
    update_fixture_status,
)
from app.goal_watcher.shared.espn_client import EspnClient
from app.goal_watcher.shared.scottish_leagues import ALL_SCOTTISH_LEAGUES

from .fixture_scanner import scan_scoreboards_for_fixtures
from .poller_control import disable_goal_poller, enable_goal_poller

logger = Logger()
tracer = Tracer()

FIXTURES_TABLE = os.environ.get("FIXTURES_TABLE_NAME", "goal-watcher-fixtures")
INSTALLATIONS_TABLE = os.environ.get("INSTALLATIONS_TABLE_NAME", "goal-watcher-installations")
GOAL_POLLER_RULE = os.environ.get("GOAL_POLLER_RULE_NAME", "goal-watcher-goal-poller")


async def _check_fixtures() -> dict[str, Any]:
    """Core fixture checking logic."""
    espn = EspnClient()

    # Get all team IDs being tracked by any installation
    tracked_team_ids = get_all_tracked_team_ids(INSTALLATIONS_TABLE)
    if not tracked_team_ids:
        logger.info("No tracked teams found — disabling goal poller")
        disable_goal_poller(GOAL_POLLER_RULE)
        return {"fixtures_found": 0, "live_count": 0, "poller_enabled": False}

    logger.info("Tracking %d team(s): %s", len(tracked_team_ids), tracked_team_ids)

    # Fetch scoreboards for all Scottish competitions
    league_slugs = [str(league) for league in ALL_SCOTTISH_LEAGUES]
    scoreboards = await espn.fetch_scoreboards(league_slugs)

    # Find fixtures involving tracked teams
    new_fixtures = scan_scoreboards_for_fixtures(scoreboards, tracked_team_ids)

    # Get existing fixtures to update
    existing_fixtures = get_active_fixtures(FIXTURES_TABLE)

    # Upsert new/updated fixtures
    for fixture in new_fixtures:
        put_fixture(FIXTURES_TABLE, fixture)

    # Mark fixtures as completed if they're no longer in the scoreboard
    active_event_ids = {f.event_id for f in new_fixtures}
    for existing in existing_fixtures:
        if existing.event_id not in active_event_ids and existing.status == MatchStatus.LIVE:
            update_fixture_status(FIXTURES_TABLE, existing.event_id, MatchStatus.COMPLETED)
            logger.info("Marked fixture %s as completed", existing.event_id)

    # Count live fixtures to decide on poller
    live_count = sum(1 for f in new_fixtures if f.status == MatchStatus.LIVE)
    scheduled_soon_count = sum(1 for f in new_fixtures if f.status == MatchStatus.SCHEDULED)

    # Enable/disable goal poller based on live matches
    should_enable = live_count > 0 or scheduled_soon_count > 0
    if should_enable:
        enable_goal_poller(GOAL_POLLER_RULE)
        logger.info("Goal poller enabled: %d live, %d scheduled", live_count, scheduled_soon_count)
    else:
        disable_goal_poller(GOAL_POLLER_RULE)
        logger.info("Goal poller disabled: no live or upcoming fixtures")

    return {
        "fixtures_found": len(new_fixtures),
        "live_count": live_count,
        "scheduled_count": scheduled_soon_count,
        "poller_enabled": should_enable,
    }


@logger.inject_lambda_context(clear_state=True)
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda handler for the fixture checker."""
    logger.info("Fixture checker invoked")
    result = asyncio.run(_check_fixtures())
    logger.info("Fixture check complete: %s", result)
    return result
