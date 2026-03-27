"""ESPN API client for fetching scoreboard, teams, and match summaries."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from app.goal_watcher.model.espn import (
    EspnScoreboardResponse,
    EspnSummaryResponse,
    EspnTeamInfo,
    EspnTeamsResponse,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

SITE_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

DEFAULT_TIMEOUT = 10.0


class EspnClientError(Exception):
    """Raised when an ESPN API call fails."""


class EspnClient:
    """Client for the ESPN undocumented public API (soccer endpoints)."""

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def _build_url(self, league_slug: str, resource: str) -> str:
        return f"{SITE_API_BASE}/{league_slug}/{resource}"

    async def fetch_scoreboard(
        self,
        league_slug: str,
        *,
        date: str | None = None,
    ) -> EspnScoreboardResponse:
        """Fetch the scoreboard for a league. Optionally filter by date (YYYYMMDD)."""
        url = self._build_url(league_slug, "scoreboard")
        params: dict[str, str] = {}
        if date:
            params["dates"] = date

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = f"ESPN scoreboard request failed for {league_slug}: {exc}"
                logger.warning(msg)
                raise EspnClientError(msg) from exc

        return EspnScoreboardResponse.model_validate(response.json())

    async def fetch_scoreboards(
        self,
        league_slugs: list[str],
        *,
        date: str | None = None,
    ) -> dict[str, EspnScoreboardResponse]:
        """Fetch scoreboards for multiple leagues. Returns a dict keyed by league slug."""
        results: dict[str, EspnScoreboardResponse] = {}
        for slug in league_slugs:
            try:
                results[slug] = await self.fetch_scoreboard(slug, date=date)
            except EspnClientError:
                logger.warning("Skipping league %s due to error", slug)
        return results

    async def fetch_match_summary(
        self,
        league_slug: str,
        event_id: str,
    ) -> EspnSummaryResponse:
        """Fetch detailed match summary including key events (goals, cards, etc.)."""
        url = self._build_url(league_slug, "summary")
        params = {"event": event_id}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = f"ESPN summary request failed for event {event_id}: {exc}"
                logger.warning(msg)
                raise EspnClientError(msg) from exc

        return EspnSummaryResponse.model_validate(response.json())

    async def fetch_teams(self, league_slug: str) -> list[EspnTeamInfo]:
        """Fetch all teams for a league."""
        url = self._build_url(league_slug, "teams")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = f"ESPN teams request failed for {league_slug}: {exc}"
                logger.warning(msg)
                raise EspnClientError(msg) from exc

        data = EspnTeamsResponse.model_validate(response.json())
        teams: list[EspnTeamInfo] = []
        for sport in data.sports:
            for league in sport.leagues:
                teams.extend(entry.team for entry in league.teams)
        return teams

    async def fetch_all_scottish_teams(
        self,
        league_slugs: list[str],
    ) -> list[EspnTeamInfo]:
        """Fetch teams from all specified Scottish leagues, deduplicated by team ID."""
        seen_ids: set[str] = set()
        all_teams: list[EspnTeamInfo] = []

        for slug in league_slugs:
            try:
                teams = await self.fetch_teams(slug)
                for team in teams:
                    if team.id not in seen_ids:
                        seen_ids.add(team.id)
                        all_teams.append(team)
            except EspnClientError:
                logger.warning("Skipping teams for league %s due to error", slug)

        return sorted(all_teams, key=lambda t: t.display_name)
