"""Tests for the fixture scanner."""

from __future__ import annotations

from app.goal_watcher.fixture_checker.fixture_scanner import (
    _event_status_to_match_status,
    _event_to_fixture,
    scan_scoreboards_for_fixtures,
)
from app.goal_watcher.model.espn import (
    EspnCompetitor,
    EspnEvent,
    EspnScoreboardResponse,
    EspnStatus,
    EspnTeamInfo,
)
from app.goal_watcher.model.match_state import MatchStatus


def _make_team_info(*, team_id: str = "254", display_name: str = "Falkirk", abbreviation: str = "FALK") -> EspnTeamInfo:
    return EspnTeamInfo(**{"id": team_id, "displayName": display_name, "abbreviation": abbreviation})


def _make_competitor(
    *,
    comp_id: str = "254",
    home_away: str = "home",
    score: str = "0",
    display_name: str = "Falkirk",
) -> EspnCompetitor:
    return EspnCompetitor(
        **{
            "id": comp_id,
            "homeAway": home_away,
            "score": score,
            "team": {"id": comp_id, "displayName": display_name},
        },
    )


def _make_status(state: str = "in") -> EspnStatus:
    return EspnStatus(
        **{
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
    )


def _make_event(
    *,
    event_id: str = "742521",
    state: str = "in",
    home_id: str = "254",
    home_name: str = "Falkirk",
    away_id: str = "250",
    away_name: str = "St Mirren",
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
                            "score": "0",
                            "team": {"id": home_id, "displayName": home_name},
                        },
                        {
                            "id": away_id,
                            "homeAway": "away",
                            "score": "0",
                            "team": {"id": away_id, "displayName": away_name},
                        },
                    ],
                },
            ],
        },
    )


def _make_scoreboard(*events: EspnEvent) -> EspnScoreboardResponse:
    return EspnScoreboardResponse(events=list(events))


class TestEventStatusToMatchStatus:
    def test_in_maps_to_live(self) -> None:
        assert _event_status_to_match_status("in") == MatchStatus.LIVE

    def test_post_maps_to_completed(self) -> None:
        assert _event_status_to_match_status("post") == MatchStatus.COMPLETED

    def test_pre_maps_to_scheduled(self) -> None:
        assert _event_status_to_match_status("pre") == MatchStatus.SCHEDULED

    def test_unknown_maps_to_scheduled(self) -> None:
        assert _event_status_to_match_status("something_else") == MatchStatus.SCHEDULED


class TestEventToFixture:
    def test_creates_correct_active_fixture(self) -> None:
        event = _make_event(home_id="254", home_name="Falkirk", away_id="250", away_name="St Mirren", state="in")
        fixture = _event_to_fixture(event, "sco.1", "254")

        assert fixture is not None
        assert fixture.event_id == "742521"
        assert fixture.league_slug == "sco.1"
        assert fixture.home_team_id == "254"
        assert fixture.home_team_name == "Falkirk"
        assert fixture.away_team_id == "250"
        assert fixture.away_team_name == "St Mirren"
        assert fixture.status == MatchStatus.LIVE
        assert fixture.tracked_team_id == "254"
        assert fixture.match_date == "2026-03-21T15:00Z"

    def test_returns_none_for_event_without_competitions(self) -> None:
        event = EspnEvent(**{"id": "1", "date": "2026-03-21T15:00Z", "competitions": []})
        assert _event_to_fixture(event, "sco.1", "254") is None


class TestScanScoreboardsForFixtures:
    def test_finds_fixtures_with_tracked_teams(self) -> None:
        event = _make_event(home_id="254", away_id="250")
        scoreboard = _make_scoreboard(event)
        scoreboards = {"sco.1": scoreboard}

        fixtures = scan_scoreboards_for_fixtures(scoreboards, {"254"})

        assert len(fixtures) == 1
        assert fixtures[0].home_team_id == "254"
        assert fixtures[0].tracked_team_id == "254"

    def test_ignores_events_without_tracked_teams(self) -> None:
        event = _make_event(home_id="254", away_id="250")
        scoreboard = _make_scoreboard(event)
        scoreboards = {"sco.1": scoreboard}

        fixtures = scan_scoreboards_for_fixtures(scoreboards, {"999"})

        assert len(fixtures) == 0

    def test_handles_multiple_leagues(self) -> None:
        event1 = _make_event(event_id="1", home_id="254", away_id="250")
        event2 = _make_event(event_id="2", home_id="260", away_id="261")
        scoreboards = {
            "sco.1": _make_scoreboard(event1),
            "sco.2": _make_scoreboard(event2),
        }

        fixtures = scan_scoreboards_for_fixtures(scoreboards, {"254", "260"})

        assert len(fixtures) == 2
        event_ids = {f.event_id for f in fixtures}
        assert event_ids == {"1", "2"}
