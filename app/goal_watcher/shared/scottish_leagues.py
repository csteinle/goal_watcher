"""Scottish football league constants for the ESPN API."""

from __future__ import annotations

from enum import StrEnum


class ScottishLeague(StrEnum):
    """ESPN slugs for Scottish football competitions."""

    PREMIERSHIP = "sco.1"
    CHAMPIONSHIP = "sco.2"
    LEAGUE_ONE = "sco.3"
    LEAGUE_TWO = "sco.4"
    SCOTTISH_CUP = "sco.tennents"
    LEAGUE_CUP = "sco.cis"
    CHALLENGE_CUP = "sco.challenge"


ALL_SCOTTISH_LEAGUES: list[ScottishLeague] = list(ScottishLeague)

LEAGUE_DISPLAY_NAMES: dict[ScottishLeague, str] = {
    ScottishLeague.PREMIERSHIP: "Scottish Premiership",
    ScottishLeague.CHAMPIONSHIP: "Scottish Championship",
    ScottishLeague.LEAGUE_ONE: "Scottish League One",
    ScottishLeague.LEAGUE_TWO: "Scottish League Two",
    ScottishLeague.SCOTTISH_CUP: "Scottish Cup",
    ScottishLeague.LEAGUE_CUP: "Scottish League Cup",
    ScottishLeague.CHALLENGE_CUP: "Scottish Challenge Cup",
}
