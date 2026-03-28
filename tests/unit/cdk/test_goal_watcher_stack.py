"""Tests for GoalWatcherStack CDK resources."""

from __future__ import annotations

import pytest
from aws_cdk.assertions import Match, Template

# CDK synth uses jsii (Node.js subprocess) which requires socket access
pytestmark = pytest.mark.enable_socket


class TestDynamoDBTables:
    """DynamoDB table resource assertions."""

    def test_three_tables_created(self, template: Template) -> None:
        template.resource_count_is("AWS::DynamoDB::Table", 3)

    def test_tables_use_pay_per_request_billing(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"BillingMode": "PAY_PER_REQUEST", "TableName": "goal-watcher-installations"},
        )
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"BillingMode": "PAY_PER_REQUEST", "TableName": "goal-watcher-match-state"},
        )
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {"BillingMode": "PAY_PER_REQUEST", "TableName": "goal-watcher-fixtures"},
        )

    def test_installations_table_has_team_id_gsi(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "goal-watcher-installations",
                "GlobalSecondaryIndexes": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "IndexName": "team-id-index",
                                "KeySchema": [{"AttributeName": "team_id", "KeyType": "HASH"}],
                            }
                        )
                    ]
                ),
            },
        )

    def test_all_tables_have_point_in_time_recovery(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "goal-watcher-installations",
                "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
            },
        )
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "goal-watcher-match-state",
                "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
            },
        )
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "TableName": "goal-watcher-fixtures",
                "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
            },
        )


class TestLambdaLayer:
    """Lambda layer resource assertions."""

    def test_dependency_layer_created(self, template: Template) -> None:
        template.resource_count_is("AWS::Lambda::LayerVersion", 1)

    def test_python_functions_use_dependency_layer(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-fixture-checker", "Layers": Match.any_value()},
        )
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-goal-poller", "Layers": Match.any_value()},
        )

    def test_smartapp_has_no_layer(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-smartapp", "Layers": Match.absent()},
        )


class TestLambdaFunctions:
    """Lambda function resource assertions."""

    def test_three_functions_created(self, template: Template) -> None:
        template.resource_count_is("AWS::Lambda::Function", 3)

    def test_all_functions_use_arm64(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-fixture-checker", "Architectures": ["arm64"]},
        )
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-goal-poller", "Architectures": ["arm64"]},
        )
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"FunctionName": "goal-watcher-smartapp", "Architectures": ["arm64"]},
        )

    def test_fixture_checker_environment_variables(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": "goal-watcher-fixture-checker",
                "Environment": {
                    "Variables": Match.object_like(
                        {
                            "FIXTURES_TABLE_NAME": Match.any_value(),
                            "INSTALLATIONS_TABLE_NAME": Match.any_value(),
                            "GOAL_POLLER_RULE_NAME": "goal-watcher-goal-poller",
                            "POWERTOOLS_SERVICE_NAME": "fixture-checker",
                            "LOG_LEVEL": "INFO",
                        }
                    )
                },
            },
        )

    def test_goal_poller_environment_variables(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": "goal-watcher-goal-poller",
                "Environment": {
                    "Variables": Match.object_like(
                        {
                            "MATCH_STATE_TABLE_NAME": Match.any_value(),
                            "FIXTURES_TABLE_NAME": Match.any_value(),
                            "INSTALLATIONS_TABLE_NAME": Match.any_value(),
                            "POWERTOOLS_SERVICE_NAME": "goal-poller",
                            "LOG_LEVEL": "INFO",
                        }
                    )
                },
            },
        )

    def test_smartapp_has_installations_table_env_var(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {
                "FunctionName": "goal-watcher-smartapp",
                "Environment": {
                    "Variables": Match.object_like(
                        {
                            "INSTALLATIONS_TABLE_NAME": Match.any_value(),
                        }
                    )
                },
            },
        )


class TestApiGateway:
    """API Gateway resource assertions."""

    def test_rest_api_created(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::ApiGateway::RestApi",
            {"Name": "Goal Watcher SmartApp"},
        )


class TestCloudWatchEvents:
    """CloudWatch Events rule assertions."""

    def test_two_rules_created(self, template: Template) -> None:
        template.resource_count_is("AWS::Events::Rule", 2)

    def test_fixture_checker_rule_runs_every_15_minutes(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Events::Rule",
            {
                "Name": "goal-watcher-fixture-checker",
                "ScheduleExpression": "rate(15 minutes)",
                "State": "ENABLED",
            },
        )

    def test_goal_poller_rule_starts_disabled(self, template: Template) -> None:
        template.has_resource_properties(
            "AWS::Events::Rule",
            {
                "Name": "goal-watcher-goal-poller",
                "ScheduleExpression": "rate(1 minute)",
                "State": "DISABLED",
            },
        )


class TestStackOutputs:
    """Stack output assertions."""

    def test_all_outputs_present(self, template: Template) -> None:
        template.has_output("ApiEndpointOutput", {})
        template.has_output("InstallationsTableOutput", {})
        template.has_output("MatchStateTableOutput", {})
        template.has_output("FixturesTableOutput", {})
        template.has_output("FixtureCheckerFunctionOutput", {})
        template.has_output("GoalPollerFunctionOutput", {})
        template.has_output("SmartAppFunctionOutput", {})
