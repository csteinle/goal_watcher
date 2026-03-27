"""Goal Watcher — SmartThings Scottish Football Goal Alert."""

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from app.goal_watcher.cdk import GoalWatcherStack
from app.goal_watcher.cdk.constants import STACK_NAME

app = cdk.App()
GoalWatcherStack(app, STACK_NAME)
cdk.Aspects.of(app).add(AwsSolutionsChecks())
app.synth()
