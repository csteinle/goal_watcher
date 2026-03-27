"""CDK test fixtures."""

from __future__ import annotations

import pytest
from aws_cdk import App
from aws_cdk.assertions import Template

from app.goal_watcher.cdk.goal_watcher_stack import GoalWatcherStack


@pytest.fixture
def template() -> Template:
    app = App()
    stack = GoalWatcherStack(app, "TestStack")
    return Template.from_stack(stack)
