"""CDK test fixtures."""

from __future__ import annotations

import tempfile
from unittest.mock import patch

import pytest
from aws_cdk import App, aws_lambda as lambda_
from aws_cdk.assertions import Template

from app.goal_watcher.cdk.goal_watcher_stack import GoalWatcherStack


class _StubDependencyLayer(lambda_.LayerVersion):
    """Stub that avoids Docker bundling during CDK unit tests."""

    def __init__(self, scope: App, id: str, **_kwargs: object) -> None:  # noqa: A002
        super().__init__(
            scope,
            id,
            code=lambda_.Code.from_asset(tempfile.mkdtemp()),
        )


@pytest.fixture
def template() -> Template:
    with patch("app.goal_watcher.cdk.goal_watcher_stack.DependencyLayer", _StubDependencyLayer):
        app = App()
        stack = GoalWatcherStack(app, "TestStack")
    return Template.from_stack(stack)
