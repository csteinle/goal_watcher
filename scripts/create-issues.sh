#!/usr/bin/env bash
# Creates all open TODO items as GitHub issues.
# Prerequisites: gh auth login

set -euo pipefail

REPO="csteinle/goal_watcher"

echo "Creating GitHub issues for goal_watcher TODO items..."

# ── Deployment ────────────────────────────────────────────────────────────────

gh issue create --repo "$REPO" \
  --title "Deploy GoalWatcherStack to AWS" \
  --body "## Overview

All steps required to get the stack live and the SmartApp registered with SmartThings.

## Steps

- [ ] Create a SmartThings developer account at https://developer.smartthings.com/
- [ ] Register a new SmartApp project — Automation for the SmartThings App, WebHook Endpoint hosting type
- [ ] Bootstrap CDK (first time only): \`cdk bootstrap\`
- [ ] Deploy the stack: \`cdk deploy GoalWatcherStack\`
- [ ] Copy the \`ApiEndpoint\` output URL into SmartThings Developer Workspace as the webhook endpoint
- [ ] Set app permissions: \`r:devices:*\`, \`x:devices:*\`
- [ ] Install the SmartApp on phone → select team → pick lights/switches → select competitions"

# ── Testing & Validation ──────────────────────────────────────────────────────

gh issue create --repo "$REPO" \
  --title "Integration and end-to-end testing" \
  --body "## Overview

Manual integration and end-to-end tests to verify the full system works against live AWS infrastructure and real SmartThings devices. Requires deployment to be complete first.

## Test cases

- [ ] Invoke Fixture Checker Lambda manually on a live Scottish match day — verify \`active_fixtures\` table is populated and Goal Poller rule is enabled
- [ ] Invoke Goal Poller Lambda during a live match — verify goal detection fires correctly (score change detected, scorer attributed)
- [ ] End-to-end: verify SmartThings lights flash and switches toggle when a goal is detected
- [ ] Test SmartApp installation lifecycle (install, update, uninstall) on a real SmartThings hub
- [ ] Verify OAuth token storage and retrieval works correctly between the Node.js SmartApp and the Python poller reading from DynamoDB"

# ── Enhancements ──────────────────────────────────────────────────────────────

gh issue create --repo "$REPO" \
  --title "Push notifications via SmartThings notification capability" \
  --body "## Overview

In addition to flashing lights and toggling switches, send a push notification to the user's phone when a goal is scored.

## Details

- Add a notification device picker to the SmartApp config page (optional)
- Send a notification with scorer and score, e.g. \`⚽ GOAL! McInnes 67' — St Johnstone 1–0 Aberdeen\`
- Should be opt-in; no notification device = silent mode"

gh issue create --repo "$REPO" \
  --title "Colour support for smart bulbs (flash in team colours)" \
  --body "## Overview

When a goal is scored, flash lights in the team's colours rather than just on/off cycling.

## Details

- Add a colour capability picker in the SmartApp devices page
- Map teams to their primary colours (e.g. St Johnstone blue = \`#003DA5\`)
- Use the SmartThings \`colorControl\` capability to set hue/saturation before flashing
- Fall back to plain on/off for bulbs without colour support"

gh issue create --repo "$REPO" \
  --title "Match start and end notifications" \
  --body "## Overview

Notify the user when a tracked team's match kicks off and when the final whistle blows, not just on goals.

## Details

- Detect \`STATUS_IN\` transition in the Fixture Checker (match just went live)
- Detect \`STATUS_POST\` / \`STATUS_FINAL\` transition in the Goal Poller (match ended)
- Send a notification and/or trigger a short light flash on match start and end
- Include current score in the end notification"

gh issue create --repo "$REPO" \
  --title "Opponent goal alerts" \
  --body "## Overview

Optionally alert the user when the opposing team scores (not just the tracked team).

## Details

- Add a toggle in the SmartApp config page: 'Also alert on opponent goals'
- Detect score increases for the non-tracked team in the Goal Poller
- Use a different alert pattern (e.g. single flash instead of triple) to distinguish"

gh issue create --repo "$REPO" \
  --title "OAuth token refresh in the Python Goal Poller" \
  --body "## Overview

The Python Goal Poller reads SmartApp installations from DynamoDB (including OAuth tokens written by the Node.js SmartApp SDK). Currently it relies on the SDK having stored a valid token; there is no refresh logic in the Python side.

## Details

- Investigate the SmartThings OAuth token refresh flow
- Implement token refresh in \`smartthings_notifier.py\` or a new \`auth.py\` module when a 401 is received
- Store the refreshed token back to the installations DynamoDB table
- Add unit tests for the refresh path"

gh issue create --repo "$REPO" \
  --title "Lambda dependency layer built from uv.lock" \
  --body "## Overview

Currently Python dependencies are bundled directly into the Lambda zip. Extracting them into a Lambda Layer would speed up deployments and reduce zip size.

## Details

- Create a \`DependencyLayer\` CDK construct that exports requirements via \`uv export\` and builds a Lambda Layer
- Wire it to all three Python Lambdas (fixture_checker, goal_poller)
- Exclude CDK and dev dependencies from the layer
- Follow the pattern described in the AWS Serverless Copilot instructions"

gh issue create --repo "$REPO" \
  --title "Replace CloudWatch Events enable/disable with EventBridge Scheduler" \
  --body "## Overview

The current approach toggles a CloudWatch Events rule on/off to control when the Goal Poller runs. EventBridge Scheduler offers a cleaner alternative with better observability.

## Details

- Replace the enable/disable CloudWatch Events rule pattern with an EventBridge Scheduler that creates/deletes a schedule when a match goes live/ends
- Remove the \`poller_control.py\` module and the CloudWatch Events IAM permissions
- Update CDK stack to use \`aws_scheduler\` constructs
- Update unit tests accordingly"

gh issue create --repo "$REPO" \
  --title "Match-day awareness in the Fixture Checker" \
  --body "## Overview

The Fixture Checker currently polls ESPN every 15 minutes regardless of whether any matches are scheduled. Adding match-day awareness would reduce unnecessary API calls and AWS costs.

## Details

- Use the ESPN calendar endpoint to check if any tracked competitions have fixtures today
- Skip the full scoreboard scan on non-match days
- Consider caching the calendar check in DynamoDB with a TTL of a few hours
- Document the ESPN calendar endpoint in the README ESPN API section"

# ── Code Quality ──────────────────────────────────────────────────────────────

gh issue create --repo "$REPO" \
  --title "Increase test coverage to 80%+" \
  --body "## Overview

Current coverage is ~70%. The 80% threshold is set in the Copilot instructions but not yet enforced in pytest config or CI.

## Files with low coverage

- \`app/goal_watcher/shared/dynamo.py\` — 35% (DynamoDB CRUD helpers untested)
- \`app/goal_watcher/fixture_checker/app.py\` — Lambda handler untested
- \`app/goal_watcher/goal_poller/app.py\` — Lambda handler untested

## Tasks

- [ ] Add tests for \`dynamo.py\` CRUD functions (mock DynamoDB client)
- [ ] Add tests for fixture_checker Lambda handler (\`app.py\`)
- [ ] Add tests for goal_poller Lambda handler (\`app.py\`)
- [ ] Raise pytest coverage threshold from 60% to 80% in \`pyproject.toml\`"

gh issue create --repo "$REPO" \
  --title "Add pre-commit hooks validation to CI" \
  --body "## Overview

Pre-commit hooks are configured locally but are not run in CI. A dedicated workflow would catch any hooks that were bypassed locally.

## Details

- Add \`.github/workflows/pre-commit.yml\` that runs \`pre-commit run --all-files\`
- Use \`pre-commit/action\` or install + run manually via uv
- Matches the pattern of existing separate CI workflows (ruff, mypy, pytest, spellcheck)"

gh issue create --repo "$REPO" \
  --title "Add taplo TOML formatting" \
  --body "## Overview

The Python Copilot instructions specify taplo for TOML formatting and linting, but it is not yet set up in this project.

## Details

- Add \`taplo\` to dev dependencies (or use the pre-commit hook directly)
- Add a taplo pre-commit hook to \`.pre-commit-config.yaml\`
- Add a \`taplo.toml\` config if needed
- Run taplo on \`pyproject.toml\` and \`cdk.json\` to auto-format
- Add a \`taplo-lint\` step to CI (or include in the pre-commit CI workflow)"

echo ""
echo "Done! All issues created."
