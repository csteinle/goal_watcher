"""CDK stack constants."""

from __future__ import annotations

from enum import StrEnum

STACK_NAME = "GoalWatcherStack"

# DynamoDB table names
INSTALLATIONS_TABLE_NAME = "goal-watcher-installations"
MATCH_STATE_TABLE_NAME = "goal-watcher-match-state"
FIXTURES_TABLE_NAME = "goal-watcher-fixtures"

# CloudWatch Events rule names
FIXTURE_CHECKER_RULE_NAME = "goal-watcher-fixture-checker"
GOAL_POLLER_RULE_NAME = "goal-watcher-goal-poller"


class Outputs(StrEnum):
    """CloudFormation stack output names."""

    API_ENDPOINT = "ApiEndpointOutput"
    INSTALLATIONS_TABLE = "InstallationsTableOutput"
    MATCH_STATE_TABLE = "MatchStateTableOutput"
    FIXTURES_TABLE = "FixturesTableOutput"
    FIXTURE_CHECKER_FUNCTION = "FixtureCheckerFunctionOutput"
    GOAL_POLLER_FUNCTION = "GoalPollerFunctionOutput"
    SMARTAPP_FUNCTION = "SmartAppFunctionOutput"
