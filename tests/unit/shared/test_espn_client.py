"""Tests for the ESPN API client."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.goal_watcher.shared.espn_client import EspnClient, EspnClientError


def _build_scoreboard_payload(
    *,
    league_id: str = "735",
    league_name: str = "Scottish Premiership",
    league_slug: str = "sco.1",
    event_id: str = "742521",
    event_date: str = "2026-03-21T15:00Z",
    event_name: str = "St Mirren at Falkirk",
    short_name: str = "STM @ FALK",
    home_id: str = "254",
    home_abbr: str = "FALK",
    home_name: str = "Falkirk",
    home_score: str = "1",
    away_id: str = "250",
    away_abbr: str = "STM",
    away_name: str = "St Mirren",
    away_score: str = "2",
    state: str = "post",
) -> dict[str, Any]:
    """Build a realistic ESPN scoreboard JSON payload."""
    return {
        "leagues": [{"id": league_id, "name": league_name, "slug": league_slug}],
        "events": [
            {
                "id": event_id,
                "date": event_date,
                "name": event_name,
                "shortName": short_name,
                "competitions": [
                    {
                        "id": event_id,
                        "date": event_date,
                        "startDate": event_date,
                        "status": {
                            "clock": 5400.0,
                            "displayClock": "90'+5'",
                            "period": 2,
                            "type": {
                                "id": "28",
                                "name": "STATUS_FULL_TIME",
                                "state": state,
                                "completed": state == "post",
                                "description": "Full Time",
                                "detail": "FT",
                                "shortDetail": "FT",
                            },
                        },
                        "competitors": [
                            {
                                "id": home_id,
                                "type": "team",
                                "order": 0,
                                "homeAway": "home",
                                "winner": False,
                                "score": home_score,
                                "form": "LDWWL",
                                "team": {
                                    "id": home_id,
                                    "uid": f"s:600~t:{home_id}",
                                    "abbreviation": home_abbr,
                                    "displayName": home_name,
                                    "shortDisplayName": home_name,
                                    "name": home_name,
                                    "color": "000099",
                                    "alternateColor": "ffffff",
                                    "isActive": True,
                                },
                            },
                            {
                                "id": away_id,
                                "type": "team",
                                "order": 1,
                                "homeAway": "away",
                                "winner": True,
                                "score": away_score,
                                "form": "WWDWL",
                                "team": {
                                    "id": away_id,
                                    "uid": f"s:600~t:{away_id}",
                                    "abbreviation": away_abbr,
                                    "displayName": away_name,
                                    "shortDisplayName": away_name,
                                    "name": away_name,
                                    "color": "000000",
                                    "alternateColor": "ffffff",
                                    "isActive": True,
                                },
                            },
                        ],
                    },
                ],
            },
        ],
    }


def _build_summary_payload(
    *,
    event_id: str = "1",
    scorer_name: str = "John McGinn",
    scorer_id: str = "9001",
    team_id: str = "254",
    team_name: str = "Falkirk",
    minute: str = "34'",
) -> dict[str, Any]:
    return {
        "keyEvents": [
            {
                "id": event_id,
                "type": {"id": "1", "text": "Goal", "type": "goal"},
                "text": f"Goal - {scorer_name}",
                "shortText": f"{scorer_name} 34'",
                "period": {"number": 1},
                "clock": {"value": 2040.0, "displayValue": minute},
                "scoringPlay": True,
                "team": {"id": team_id, "displayName": team_name},
                "participants": [{"athlete": {"id": scorer_id, "displayName": scorer_name}}],
                "shootout": False,
            },
        ],
    }


def _build_teams_payload(
    teams: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if teams is None:
        teams = [
            {"id": "254", "displayName": "Falkirk", "abbreviation": "FALK"},
            {"id": "250", "displayName": "St Mirren", "abbreviation": "STM"},
        ]
    return {
        "sports": [
            {
                "id": "600",
                "name": "Soccer",
                "leagues": [
                    {
                        "id": "735",
                        "name": "Scottish Premiership",
                        "slug": "sco.1",
                        "teams": [
                            {
                                "team": {
                                    "id": t["id"],
                                    "displayName": t["displayName"],
                                    "abbreviation": t.get("abbreviation", ""),
                                    "shortDisplayName": t["displayName"],
                                    "name": t["displayName"],
                                    "color": "000000",
                                    "alternateColor": "ffffff",
                                    "isActive": True,
                                },
                            }
                            for t in teams
                        ],
                    },
                ],
            },
        ],
    }


def _mock_httpx_response(json_data: dict[str, Any], status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=MagicMock(spec=httpx.Request),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestFetchScoreboard:
    async def test_success_returns_parsed_response(self) -> None:
        payload = _build_scoreboard_payload()
        mock_response = _mock_httpx_response(payload)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            result = await client.fetch_scoreboard("sco.1")

        assert len(result.leagues) == 1
        assert result.leagues[0].id == "735"
        assert result.leagues[0].name == "Scottish Premiership"
        assert len(result.events) == 1
        assert result.events[0].id == "742521"
        assert result.events[0].name == "St Mirren at Falkirk"

        comp = result.events[0].competitions[0]
        home = next(c for c in comp.competitors if c.home_away == "home")
        away = next(c for c in comp.competitors if c.home_away == "away")
        assert home.team.display_name == "Falkirk"
        assert away.team.display_name == "St Mirren"
        assert home.score == "1"
        assert away.score == "2"

    async def test_with_date_parameter(self) -> None:
        payload = _build_scoreboard_payload()
        mock_response = _mock_httpx_response(payload)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            await client.fetch_scoreboard("sco.1", date="20260321")

        mock_client.get.assert_called_once()
        _, kwargs = mock_client.get.call_args
        assert kwargs["params"] == {"dates": "20260321"}

    async def test_http_error_raises_espn_client_error(self) -> None:
        mock_response = _mock_httpx_response({}, status_code=500)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(EspnClientError, match="ESPN scoreboard request failed"),
        ):
            client = EspnClient()
            await client.fetch_scoreboard("sco.1")


class TestFetchScoreboards:
    async def test_multiple_leagues_one_fails_gracefully(self) -> None:
        payload_ok = _build_scoreboard_payload(league_slug="sco.1")
        mock_resp_ok = _mock_httpx_response(payload_ok)
        mock_resp_fail = _mock_httpx_response({}, status_code=500)

        call_count = 0

        async def mock_get(url: str, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if "sco.2" in url:
                return mock_resp_fail
            return mock_resp_ok

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            results = await client.fetch_scoreboards(["sco.1", "sco.2"])

        assert "sco.1" in results
        assert "sco.2" not in results
        assert len(results) == 1


class TestFetchMatchSummary:
    async def test_success_parses_key_events(self) -> None:
        payload = _build_summary_payload(scorer_name="John McGinn", minute="34'")
        mock_response = _mock_httpx_response(payload)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            result = await client.fetch_match_summary("sco.1", "742521")

        assert len(result.key_events) == 1
        event = result.key_events[0]
        assert event.scoring_play is True
        assert event.type.type == "goal"
        assert event.participants[0].athlete.display_name == "John McGinn"
        assert event.clock is not None
        assert event.clock.display_value == "34'"


class TestFetchTeams:
    async def test_success_extracts_team_list(self) -> None:
        payload = _build_teams_payload()
        mock_response = _mock_httpx_response(payload)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            teams = await client.fetch_teams("sco.1")

        assert len(teams) == 2
        names = {t.display_name for t in teams}
        assert names == {"Falkirk", "St Mirren"}


class TestFetchAllScottishTeams:
    async def test_deduplicates_by_team_id(self) -> None:
        """Teams appearing in multiple leagues should only appear once."""
        league1_teams = [
            {"id": "254", "displayName": "Falkirk", "abbreviation": "FALK"},
            {"id": "250", "displayName": "St Mirren", "abbreviation": "STM"},
        ]
        league2_teams = [
            {"id": "254", "displayName": "Falkirk", "abbreviation": "FALK"},
            {"id": "260", "displayName": "Celtic", "abbreviation": "CEL"},
        ]

        responses = iter(
            [
                _mock_httpx_response(_build_teams_payload(teams=league1_teams)),
                _mock_httpx_response(_build_teams_payload(teams=league2_teams)),
            ]
        )

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = lambda *_args, **_kwargs: next(responses)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.goal_watcher.shared.espn_client.httpx.AsyncClient", return_value=mock_client):
            client = EspnClient()
            teams = await client.fetch_all_scottish_teams(["sco.1", "sco.2"])

        ids = [t.id for t in teams]
        assert len(ids) == 3
        assert len(set(ids)) == 3
        # Should be sorted by display_name
        names = [t.display_name for t in teams]
        assert names == sorted(names)
