"""Tests for the poller control module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.goal_watcher.fixture_checker.poller_control import (
    disable_goal_poller,
    enable_goal_poller,
    is_goal_poller_enabled,
)

RULE_NAME = "GoalWatcher-GoalPollerRule"


class TestEnableGoalPoller:
    @patch("app.goal_watcher.fixture_checker.poller_control._get_events_client")
    def test_calls_enable_rule(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        enable_goal_poller(RULE_NAME)

        mock_client.enable_rule.assert_called_once_with(Name=RULE_NAME)


class TestDisableGoalPoller:
    @patch("app.goal_watcher.fixture_checker.poller_control._get_events_client")
    def test_calls_disable_rule(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        disable_goal_poller(RULE_NAME)

        mock_client.disable_rule.assert_called_once_with(Name=RULE_NAME)


class TestIsGoalPollerEnabled:
    @patch("app.goal_watcher.fixture_checker.poller_control._get_events_client")
    def test_returns_true_when_enabled(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.describe_rule.return_value = {"State": "ENABLED"}
        mock_get_client.return_value = mock_client

        assert is_goal_poller_enabled(RULE_NAME) is True
        mock_client.describe_rule.assert_called_once_with(Name=RULE_NAME)

    @patch("app.goal_watcher.fixture_checker.poller_control._get_events_client")
    def test_returns_false_when_disabled(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.describe_rule.return_value = {"State": "DISABLED"}
        mock_get_client.return_value = mock_client

        assert is_goal_poller_enabled(RULE_NAME) is False

    @patch("app.goal_watcher.fixture_checker.poller_control._get_events_client")
    def test_returns_false_when_state_missing(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.describe_rule.return_value = {}
        mock_get_client.return_value = mock_client

        assert is_goal_poller_enabled(RULE_NAME) is False
