"""Pydantic models for ESPN API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EspnStatusType(BaseModel):
    """Status type from ESPN API (e.g., STATUS_IN_PROGRESS, STATUS_FULL_TIME)."""

    id: str
    name: str
    state: str  # "pre", "in", "post"
    completed: bool
    description: str
    detail: str
    short_detail: str = Field(alias="shortDetail")


class EspnStatus(BaseModel):
    """Match status from ESPN API."""

    clock: float = 0.0
    display_clock: str = Field("0'", alias="displayClock")
    period: int = 0
    type: EspnStatusType


class EspnTeamInfo(BaseModel):
    """Team info nested inside a competitor."""

    id: str
    uid: str | None = None
    abbreviation: str = ""
    display_name: str = Field(alias="displayName")
    short_display_name: str = Field("", alias="shortDisplayName")
    name: str = ""
    color: str = ""
    alternate_color: str = Field("", alias="alternateColor")
    is_active: bool = Field(True, alias="isActive")


class EspnCompetitor(BaseModel):
    """A competitor (team) in a competition/match."""

    id: str
    type: str = "team"
    order: int = 0
    home_away: str = Field(alias="homeAway")
    winner: bool = False
    score: str = "0"
    form: str = ""
    team: EspnTeamInfo


class EspnVenue(BaseModel):
    """Match venue."""

    id: str = ""
    full_name: str = Field("", alias="fullName")


class EspnCompetition(BaseModel):
    """A competition (match) within an event."""

    id: str
    date: str
    start_date: str = Field("", alias="startDate")
    status: EspnStatus
    venue: EspnVenue | None = None
    competitors: list[EspnCompetitor] = []


class EspnEvent(BaseModel):
    """A single event (match) from the scoreboard."""

    id: str
    uid: str = ""
    date: str
    name: str = ""
    short_name: str = Field("", alias="shortName")
    competitions: list[EspnCompetition] = []


class EspnLeague(BaseModel):
    """League metadata from the scoreboard response."""

    id: str
    name: str = ""
    abbreviation: str = ""
    slug: str = ""


class EspnScoreboardResponse(BaseModel):
    """Top-level response from the ESPN scoreboard endpoint."""

    leagues: list[EspnLeague] = []
    events: list[EspnEvent] = []


# --- Match Summary models ---


class EspnKeyEventType(BaseModel):
    """Type descriptor for a key event."""

    id: str
    text: str = ""
    type: str = ""  # "goal", "yellowcard", "redcard", "substitution"


class EspnKeyEventPeriod(BaseModel):
    """Period info for a key event."""

    number: int = 0


class EspnKeyEventClock(BaseModel):
    """Clock info for a key event."""

    value: float = 0.0
    display_value: str = Field("", alias="displayValue")


class EspnKeyEventTeam(BaseModel):
    """Minimal team info in a key event."""

    id: str
    display_name: str = Field("", alias="displayName")


class EspnKeyEventAthlete(BaseModel):
    """Athlete info nested in a participant."""

    id: str
    display_name: str = Field("", alias="displayName")


class EspnKeyEventParticipant(BaseModel):
    """Participant (athlete) in a key event."""

    athlete: EspnKeyEventAthlete


class EspnKeyEvent(BaseModel):
    """A key event from the match summary (goal, card, sub, etc.)."""

    id: str
    type: EspnKeyEventType
    text: str = ""
    short_text: str = Field("", alias="shortText")
    period: EspnKeyEventPeriod | None = None
    clock: EspnKeyEventClock | None = None
    scoring_play: bool = Field(False, alias="scoringPlay")
    team: EspnKeyEventTeam | None = None
    participants: list[EspnKeyEventParticipant] = []
    shootout: bool = False


class EspnSummaryResponse(BaseModel):
    """Response from the ESPN match summary endpoint (partial — only fields we need)."""

    key_events: list[EspnKeyEvent] = Field([], alias="keyEvents")


# --- Teams endpoint models ---


class EspnTeamEntry(BaseModel):
    """A team entry from the teams endpoint."""

    team: EspnTeamInfo


class EspnTeamsLeague(BaseModel):
    """League with teams from the teams endpoint."""

    id: str
    name: str = ""
    slug: str = ""
    teams: list[EspnTeamEntry] = []


class EspnTeamsSport(BaseModel):
    """Sport wrapper from the teams endpoint."""

    id: str
    name: str = ""
    leagues: list[EspnTeamsLeague] = []


class EspnTeamsResponse(BaseModel):
    """Top-level response from the ESPN teams endpoint."""

    sports: list[EspnTeamsSport] = []
