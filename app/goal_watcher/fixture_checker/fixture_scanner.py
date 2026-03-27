"""Fixture scanner — discovers upcoming and live matches for tracked teams."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.goal_watcher.model.espn import EspnEvent, EspnScoreboardResponse
from app.goal_watcher.model.match_state import ActiveFixture, MatchStatus

logger = logging.getLogger(__name__)


def _event_status_to_match_status(state: str) -> MatchStatus:
    """Map ESPN event state to our MatchStatus."""
    match state:
        case "in":
            return MatchStatus.LIVE
        case "post":
            return MatchStatus.COMPLETED
        case _:
            return MatchStatus.SCHEDULED


def _event_involves_team(event: EspnEvent, team_ids: set[str]) -> str | None:
    """Check if any competitor in the event matches a tracked team. Returns the matched team ID or None."""
    for competition in event.competitions:
        for competitor in competition.competitors:
            if competitor.id in team_ids:
                return competitor.id
    return None


def _event_to_fixture(event: EspnEvent, league_slug: str, tracked_team_id: str) -> ActiveFixture | None:
    """Convert an ESPN event to an ActiveFixture."""
    if not event.competitions:
        return None

    comp = event.competitions[0]
    home = next((c for c in comp.competitors if c.home_away == "home"), None)
    away = next((c for c in comp.competitors if c.home_away == "away"), None)

    if not home or not away:
        return None

    return ActiveFixture(
        event_id=event.id,
        league_slug=league_slug,
        home_team_id=home.id,
        home_team_name=home.team.display_name,
        away_team_id=away.id,
        away_team_name=away.team.display_name,
        match_date=event.date,
        status=_event_status_to_match_status(comp.status.type.state),
        tracked_team_id=tracked_team_id,
        last_updated=datetime.now(tz=UTC).isoformat(),
    )


def scan_scoreboards_for_fixtures(
    scoreboards: dict[str, EspnScoreboardResponse],
    tracked_team_ids: set[str],
) -> list[ActiveFixture]:
    """Scan multiple league scoreboards and return fixtures involving tracked teams.

    Args:
        scoreboards: Dict of league_slug → scoreboard response.
        tracked_team_ids: Set of ESPN team IDs being tracked by any SmartApp installation.

    Returns:
        List of ActiveFixture objects for matches involving tracked teams.
    """
    fixtures: list[ActiveFixture] = []

    for league_slug, scoreboard in scoreboards.items():
        for event in scoreboard.events:
            matched_team_id = _event_involves_team(event, tracked_team_ids)
            if matched_team_id:
                fixture = _event_to_fixture(event, league_slug, matched_team_id)
                if fixture:
                    fixtures.append(fixture)
                    logger.info(
                        "Found fixture: %s vs %s (%s) — status=%s",
                        fixture.home_team_name,
                        fixture.away_team_name,
                        league_slug,
                        fixture.status,
                    )

    return fixtures
