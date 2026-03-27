"""Goal Watcher CDK Stack."""

from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from cdk_nag import NagSuppressions
from constructs import Construct

from .constants import (
    FIXTURES_TABLE_NAME,
    GOAL_POLLER_RULE_NAME,
    INSTALLATIONS_TABLE_NAME,
    MATCH_STATE_TABLE_NAME,
    Outputs,
)


class GoalWatcherStack(Stack):
    """Main CDK stack for the Goal Watcher application."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- DynamoDB Tables ---

        installations_table = dynamodb.Table(
            self,
            "InstallationsTable",
            table_name=INSTALLATIONS_TABLE_NAME,
            partition_key=dynamodb.Attribute(name="installedAppId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )
        # GSI for looking up installations by team_id
        installations_table.add_global_secondary_index(
            index_name="team-id-index",
            partition_key=dynamodb.Attribute(name="team_id", type=dynamodb.AttributeType.STRING),
        )

        match_state_table = dynamodb.Table(
            self,
            "MatchStateTable",
            table_name=MATCH_STATE_TABLE_NAME,
            partition_key=dynamodb.Attribute(name="event_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        fixtures_table = dynamodb.Table(
            self,
            "FixturesTable",
            table_name=FIXTURES_TABLE_NAME,
            partition_key=dynamodb.Attribute(name="event_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        # --- Lambda Functions ---

        # Python Fixture Checker Lambda
        fixture_checker_fn = lambda_.Function(
            self,
            "FixtureCheckerFunction",
            function_name="goal-watcher-fixture-checker",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="app.goal_watcher.fixture_checker.app.handler",
            code=lambda_.Code.from_asset(
                "app",
                exclude=[
                    "**/__pycache__",
                    "goal_watcher/cdk/**",
                    "goal_watcher/goal_poller/**",
                ],
            ),
            architecture=lambda_.Architecture.ARM_64,
            memory_size=256,
            timeout=Duration.seconds(120),
            environment={
                "FIXTURES_TABLE_NAME": fixtures_table.table_name,
                "INSTALLATIONS_TABLE_NAME": installations_table.table_name,
                "GOAL_POLLER_RULE_NAME": GOAL_POLLER_RULE_NAME,
                "POWERTOOLS_SERVICE_NAME": "fixture-checker",
                "LOG_LEVEL": "INFO",
            },
            logging_format=lambda_.LoggingFormat.JSON,
            log_group=logs.LogGroup(
                self,
                "FixtureCheckerLogGroup",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Python Goal Poller Lambda
        goal_poller_fn = lambda_.Function(
            self,
            "GoalPollerFunction",
            function_name="goal-watcher-goal-poller",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="app.goal_watcher.goal_poller.app.handler",
            code=lambda_.Code.from_asset(
                "app",
                exclude=[
                    "**/__pycache__",
                    "goal_watcher/cdk/**",
                    "goal_watcher/fixture_checker/**",
                ],
            ),
            architecture=lambda_.Architecture.ARM_64,
            memory_size=256,
            timeout=Duration.seconds(120),
            environment={
                "MATCH_STATE_TABLE_NAME": match_state_table.table_name,
                "FIXTURES_TABLE_NAME": fixtures_table.table_name,
                "INSTALLATIONS_TABLE_NAME": installations_table.table_name,
                "POWERTOOLS_SERVICE_NAME": "goal-poller",
                "LOG_LEVEL": "INFO",
            },
            logging_format=lambda_.LoggingFormat.JSON,
            log_group=logs.LogGroup(
                self,
                "GoalPollerLogGroup",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Node.js SmartApp Lambda
        smartapp_fn = lambda_.Function(
            self,
            "SmartAppFunction",
            function_name="goal-watcher-smartapp",
            runtime=lambda_.Runtime.NODEJS_22_X,
            handler="src/index.handler",
            code=lambda_.Code.from_asset(
                "smartapp",
                exclude=["node_modules/.cache"],
            ),
            architecture=lambda_.Architecture.ARM_64,
            memory_size=256,
            timeout=Duration.seconds(30),
            environment={
                "INSTALLATIONS_TABLE_NAME": installations_table.table_name,
            },
            logging_format=lambda_.LoggingFormat.JSON,
            log_group=logs.LogGroup(
                self,
                "SmartAppLogGroup",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # --- DynamoDB Permissions ---

        installations_table.grant_read_write_data(smartapp_fn)
        installations_table.grant_read_data(fixture_checker_fn)
        installations_table.grant_read_data(goal_poller_fn)

        match_state_table.grant_read_write_data(goal_poller_fn)
        fixtures_table.grant_read_write_data(fixture_checker_fn)
        fixtures_table.grant_read_write_data(goal_poller_fn)

        # --- API Gateway for SmartApp webhook ---

        api = apigw.RestApi(
            self,
            "SmartAppApi",
            rest_api_name="Goal Watcher SmartApp",
            description="Webhook endpoint for SmartThings SmartApp lifecycle events",
        )
        api.root.add_method("POST", apigw.LambdaIntegration(smartapp_fn))

        # --- CloudWatch Events Rules ---

        # Fixture checker: every 15 minutes (always enabled)
        events.Rule(
            self,
            "FixtureCheckerRule",
            rule_name="goal-watcher-fixture-checker",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            targets=[targets.LambdaFunction(fixture_checker_fn)],
        )

        # Goal poller: every 60 seconds (starts DISABLED)
        goal_poller_rule = events.Rule(
            self,
            "GoalPollerRule",
            rule_name=GOAL_POLLER_RULE_NAME,
            schedule=events.Schedule.rate(Duration.minutes(1)),
            targets=[targets.LambdaFunction(goal_poller_fn)],
            enabled=False,
        )

        # Grant the fixture checker permission to enable/disable the goal poller rule
        goal_poller_rule.grant(fixture_checker_fn.role, "events:EnableRule", "events:DisableRule")  # type: ignore[union-attr]

        # --- cdk-nag Suppressions ---

        NagSuppressions.add_stack_suppressions(
            self,
            [
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "Access logging not required for personal project webhook endpoint",
                },
                {
                    "id": "AwsSolutions-APIG2",
                    "reason": "Request validation handled by SmartThings SDK in the Lambda",
                },
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "SmartThings webhook requires unauthenticated access — auth handled by SDK signature verification",
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "No Cognito required — SmartThings handles auth via its own OAuth flow",
                },
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "AWS managed policies used for Lambda basic execution role",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard permissions are scoped to specific DynamoDB tables and EventBridge rules",
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "Using latest available Lambda runtimes (Python 3.13, Node.js 22)",
                },
            ],
        )

        # --- Stack Outputs ---

        CfnOutput(self, Outputs.API_ENDPOINT, value=api.url)
        CfnOutput(self, Outputs.INSTALLATIONS_TABLE, value=installations_table.table_name)
        CfnOutput(self, Outputs.MATCH_STATE_TABLE, value=match_state_table.table_name)
        CfnOutput(self, Outputs.FIXTURES_TABLE, value=fixtures_table.table_name)
        CfnOutput(self, Outputs.FIXTURE_CHECKER_FUNCTION, value=fixture_checker_fn.function_name)
        CfnOutput(self, Outputs.GOAL_POLLER_FUNCTION, value=goal_poller_fn.function_name)
        CfnOutput(self, Outputs.SMARTAPP_FUNCTION, value=smartapp_fn.function_name)
