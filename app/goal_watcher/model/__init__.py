"""Goal Watcher data models."""

from .espn import (
    EspnCompetition,
    EspnCompetitor,
    EspnEvent,
    EspnKeyEvent,
    EspnLeague,
    EspnScoreboardResponse,
    EspnStatus,
    EspnSummaryResponse,
    EspnTeamEntry,
    EspnTeamInfo,
    EspnTeamsResponse,
)
from .installation import DeviceConfig, Installation
from .match_state import ActiveFixture, MatchState, MatchStatus, TeamScore

__all__ = [
    "ActiveFixture",
    "DeviceConfig",
    "EspnCompetition",
    "EspnCompetitor",
    "EspnEvent",
    "EspnKeyEvent",
    "EspnLeague",
    "EspnScoreboardResponse",
    "EspnStatus",
    "EspnSummaryResponse",
    "EspnTeamEntry",
    "EspnTeamInfo",
    "EspnTeamsResponse",
    "Installation",
    "MatchState",
    "MatchStatus",
    "TeamScore",
]
