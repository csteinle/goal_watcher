"""Tests for the goal detector."""

from __future__ import annotations

from app.goal_watcher.goal_poller.goal_detector import (
    build_match_state_from_event,
    detect_goals,
)
from app.goal_watcher.model.espn import (
    EspnEvent,
    EspnKeyEvent,
    EspnKeyEventAthlete,
    EspnKeyEventClock,
    EspnKeyEventParticipant,
    EspnKeyEventTeam,
    EspnKeyEventType,
)
from app.goal_watcher.model.match_state import MatchState, MatchStatus, TeamScore


def _make_match_state(
    *,
    event_id: str = "742521",
    league_slug: str = "sco.1",
    home_id: str = "254",
    home_name: str = "Falkirk",
    home_score: int = 0,
    away_id: str = "250",
    away_name: str = "St Mirren",
    away_score: int = 0,
    status: MatchStatus = MatchStatus.LIVE,
) -> MatchState:
    return MatchState(
        event_id=event_id,
        league_slug=league_slug,
        home=TeamScore(team_id=home_id, team_name=home_name, score=home_score, home_away="home"),
        away=TeamScore(team_id=away_id, team_name=away_name, score=away_score, home_away="away"),
        status=status,
    )


def _make_espn_event(
    *,
    event_id: str = "742521",
    state: str = "in",
    home_id: str = "254",
    home_name: str = "Falkirk",
    home_score: str = "1",
    away_id: str = "250",
    away_name: str = "St Mirren",
    away_score: str = "2",
) -> EspnEvent:
    return EspnEvent(
        **{
            "id": event_id,
            "date": "2026-03-21T15:00Z",
            "name": f"{away_name} at {home_name}",
            "shortName": "STM @ FALK",
            "competitions": [
                {
                    "id": event_id,
                    "date": "2026-03-21T15:00Z",
                    "startDate": "2026-03-21T15:00Z",
                    "status": {
                        "clock": 2700.0,
                        "displayClock": "45'",
                        "period": 1,
                        "type": {
                            "id": "2",
                            "name": "STATUS_IN_PROGRESS",
                            "state": state,
                            "completed": state == "post",
                            "description": "In Progress",
                            "detail": "45'",
                            "shortDetail": "45'",
                        },
                    },
                    "competitors": [
                        {
                            "id": home_id,
                            "homeAway": "home",
                            "score": home_score,
                            "team": {"id": home_id, "displayName": home_name},
                        },
                        {
                            "id": away_id,
                            "homeAway": "away",
                            "score": away_score,
                            "team": {"id": away_id, "displayName": away_name},
                        },
                    ],
                },
            ],
        },
    )


def _make_key_event(
    *,
    key_event_id: str = "1",
    scorer_name: str = "John McGinn",
    scorer_id: str = "9001",
    team_id: str = "254",
    team_name: str = "Falkirk",
    minute: str = "34'",
) -> EspnKeyEvent:
    return EspnKeyEvent(
        id=key_event_id,
        type=EspnKeyEventType(id="1", text="Goal", type="goal"),
        text=f"Goal - {scorer_name}",
        clock=EspnKeyEventClock(**{"value": 2040.0, "displayValue": minute}),
        team=EspnKeyEventTeam(**{"id": team_id, "displayName": team_name}),
        participants=[
            EspnKeyEventParticipant(athlete=EspnKeyEventAthlete(**{"id": scorer_id, "displayName": scorer_name}))
        ],
        **{"scoringPlay": True},
    )


class TestDetectGoals:
    def test_no_previous_state_no_goals_returned(self) -> None:
        """First sighting of a match — don't fire for historical goals."""
        current = _make_match_state(home_score=1, away_score=0)
        goals = detect_goals(None, current)
        assert goals == []

    def test_no_previous_state_zero_score_no_goals(self) -> None:
        """First sighting at 0-0 also returns no goals."""
        current = _make_match_state(home_score=0, away_score=0)
        goals = detect_goals(None, current)
        assert goals == []

    def test_home_team_scores_one_goal(self) -> None:
        previous = _make_match_state(home_score=0, away_score=0)
        current = _make_match_state(home_score=1, away_score=0)

        goals = detect_goals(previous, current)

        assert len(goals) == 1
        goal = goals[0]
        assert goal.scoring_team_id == "254"
        assert goal.scoring_team_name == "Falkirk"
        assert goal.opponent_team_name == "St Mirren"
        assert goal.new_home_score == 1
        assert goal.new_away_score == 0
        assert "GOAL" in goal.description

    def test_away_team_scores_one_goal(self) -> None:
        previous = _make_match_state(home_score=0, away_score=0)
        current = _make_match_state(home_score=0, away_score=1)

        goals = detect_goals(previous, current)

        assert len(goals) == 1
        goal = goals[0]
        assert goal.scoring_team_id == "250"
        assert goal.scoring_team_name == "St Mirren"
        assert goal.opponent_team_name == "Falkirk"
        assert goal.new_home_score == 0
        assert goal.new_away_score == 1

    def test_both_teams_score_in_same_poll_interval(self) -> None:
        previous = _make_match_state(home_score=0, away_score=0)
        current = _make_match_state(home_score=1, away_score=1)

        goals = detect_goals(previous, current)

        assert len(goals) == 2
        scoring_team_ids = {g.scoring_team_id for g in goals}
        assert scoring_team_ids == {"254", "250"}

    def test_no_score_change_no_goals_returned(self) -> None:
        previous = _make_match_state(home_score=1, away_score=1)
        current = _make_match_state(home_score=1, away_score=1)

        goals = detect_goals(previous, current)
        assert goals == []

    def test_with_key_events_picks_up_scorer_and_minute(self) -> None:
        previous = _make_match_state(home_score=0, away_score=0)
        current = _make_match_state(home_score=1, away_score=0)

        key_events = [_make_key_event(scorer_name="John McGinn", team_id="254", minute="34'")]

        goals = detect_goals(previous, current, key_events=key_events)

        assert len(goals) == 1
        assert goals[0].scorer_name == "John McGinn"
        assert goals[0].minute == "34'"


class TestBuildMatchStateFromEvent:
    def test_creates_correct_match_state(self) -> None:
        event = _make_espn_event(home_score="1", away_score="2", state="in")
        state = build_match_state_from_event(event, "sco.1")

        assert state is not None
        assert state.event_id == "742521"
        assert state.league_slug == "sco.1"
        assert state.home.team_id == "254"
        assert state.home.team_name == "Falkirk"
        assert state.home.score == 1
        assert state.away.team_id == "250"
        assert state.away.team_name == "St Mirren"
        assert state.away.score == 2
        assert state.status == MatchStatus.LIVE

    def test_returns_none_for_empty_event(self) -> None:
        event = EspnEvent(**{"id": "1", "date": "2026-03-21T15:00Z", "competitions": []})
        assert build_match_state_from_event(event, "sco.1") is None

    def test_post_state_maps_to_completed(self) -> None:
        event = _make_espn_event(state="post")
        state = build_match_state_from_event(event, "sco.1")
        assert state is not None
        assert state.status == MatchStatus.COMPLETED

    def test_pre_state_maps_to_scheduled(self) -> None:
        event = _make_espn_event(state="pre")
        state = build_match_state_from_event(event, "sco.1")
        assert state is not None
        assert state.status == MatchStatus.SCHEDULED
