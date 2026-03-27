"""Goal detection logic — compares stored match state with live scores to detect new goals."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.goal_watcher.model.espn import EspnEvent, EspnKeyEvent
from app.goal_watcher.model.match_state import MatchState, MatchStatus, TeamScore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GoalEvent:
    """Represents a detected goal."""

    event_id: str
    league_slug: str
    scoring_team_id: str
    scoring_team_name: str
    opponent_team_name: str
    scorer_name: str
    minute: str
    new_home_score: int
    new_away_score: int
    home_team_name: str
    away_team_name: str
    description: str


def build_match_state_from_event(event: EspnEvent, league_slug: str) -> MatchState | None:
    """Build a MatchState from a live ESPN event."""
    if not event.competitions:
        return None

    comp = event.competitions[0]
    home = next((c for c in comp.competitors if c.home_away == "home"), None)
    away = next((c for c in comp.competitors if c.home_away == "away"), None)

    if not home or not away:
        return None

    state = comp.status.type.state
    match state:
        case "in":
            status = MatchStatus.LIVE
        case "post":
            status = MatchStatus.COMPLETED
        case _:
            status = MatchStatus.SCHEDULED

    return MatchState(
        event_id=event.id,
        league_slug=league_slug,
        home=TeamScore(
            team_id=home.id,
            team_name=home.team.display_name,
            score=int(home.score),
            home_away="home",
        ),
        away=TeamScore(
            team_id=away.id,
            team_name=away.team.display_name,
            score=int(away.score),
            home_away="away",
        ),
        status=status,
    )


def detect_goals(
    previous: MatchState | None,
    current: MatchState,
    key_events: list[EspnKeyEvent] | None = None,
) -> list[GoalEvent]:
    """Detect new goals by comparing previous and current match state.

    If key_events are provided (from the match summary), use them to get scorer details.
    Otherwise, infer from the score change.
    """
    goals: list[GoalEvent] = []

    if previous is None:
        # First time seeing this match — if score is already > 0, we missed earlier goals
        # Don't fire alerts for goals we didn't witness in real time
        if current.home_score > 0 or current.away_score > 0:
            logger.info(
                "New match %s already has score %d-%d — skipping historical goals",
                current.event_id,
                current.home_score,
                current.away_score,
            )
        return goals

    home_diff = current.home_score - previous.home_score
    away_diff = current.away_score - previous.away_score

    if home_diff == 0 and away_diff == 0:
        return goals

    # Try to match goals with key events for scorer details
    scoring_events = _get_recent_scoring_events(key_events) if key_events else []

    if home_diff > 0:
        for i in range(home_diff):
            scorer_info = _find_scorer_for_team(scoring_events, current.home.team_id, i)
            goals.append(
                GoalEvent(
                    event_id=current.event_id,
                    league_slug=current.league_slug,
                    scoring_team_id=current.home.team_id,
                    scoring_team_name=current.home.team_name,
                    opponent_team_name=current.away.team_name,
                    scorer_name=scorer_info.get("name", "Unknown"),
                    minute=scorer_info.get("minute", ""),
                    new_home_score=current.home_score,
                    new_away_score=current.away_score,
                    home_team_name=current.home.team_name,
                    away_team_name=current.away.team_name,
                    description=f"⚽ GOAL! {current.home.team_name} {current.home_score}-{current.away_score} {current.away.team_name}",
                ),
            )

    if away_diff > 0:
        for i in range(away_diff):
            scorer_info = _find_scorer_for_team(scoring_events, current.away.team_id, i)
            goals.append(
                GoalEvent(
                    event_id=current.event_id,
                    league_slug=current.league_slug,
                    scoring_team_id=current.away.team_id,
                    scoring_team_name=current.away.team_name,
                    opponent_team_name=current.home.team_name,
                    scorer_name=scorer_info.get("name", "Unknown"),
                    minute=scorer_info.get("minute", ""),
                    new_home_score=current.home_score,
                    new_away_score=current.away_score,
                    home_team_name=current.home.team_name,
                    away_team_name=current.away.team_name,
                    description=f"⚽ GOAL! {current.home.team_name} {current.home_score}-{current.away_score} {current.away.team_name}",
                ),
            )

    for goal in goals:
        logger.info("Goal detected: %s — %s (%s)", goal.description, goal.scorer_name, goal.minute)

    return goals


def _get_recent_scoring_events(key_events: list[EspnKeyEvent]) -> list[EspnKeyEvent]:
    """Filter key events to only scoring plays."""
    return [e for e in key_events if e.scoring_play and e.type.type == "goal"]


def _find_scorer_for_team(
    scoring_events: list[EspnKeyEvent],
    team_id: str,
    index: int,
) -> dict[str, str]:
    """Find scorer info from key events for a specific team goal."""
    team_goals = [e for e in scoring_events if e.team and e.team.id == team_id]

    # Get the most recent goals (they're at the end of the list)
    if index < len(team_goals):
        event = team_goals[-(index + 1)]
        name = event.participants[0].athlete.display_name if event.participants else "Unknown"
        minute = event.clock.display_value if event.clock else ""
        return {"name": name, "minute": minute}

    return {"name": "Unknown", "minute": ""}
