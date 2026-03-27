"""Pydantic models for DynamoDB match state and active fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MatchStatus(StrEnum):
    """Status of a match."""

    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"


class TeamScore(BaseModel):
    """Score for a single team in a match."""

    team_id: str
    team_name: str
    score: int = 0
    home_away: str = ""  # "home" or "away"


class MatchState(BaseModel):
    """Stored state for a single match — used to detect score changes."""

    event_id: str
    league_slug: str
    home: TeamScore
    away: TeamScore
    status: MatchStatus = MatchStatus.LIVE
    last_updated: str = Field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    @property
    def home_score(self) -> int:
        return self.home.score

    @property
    def away_score(self) -> int:
        return self.away.score


class ActiveFixture(BaseModel):
    """A tracked fixture discovered by the fixture checker."""

    event_id: str
    league_slug: str
    home_team_id: str
    home_team_name: str
    away_team_id: str
    away_team_name: str
    match_date: str
    status: MatchStatus = MatchStatus.SCHEDULED
    tracked_team_id: str = ""  # which team triggered tracking
    last_updated: str = Field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
