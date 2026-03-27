# Actions Log

Record of all development actions taken on the Goal Watcher project.

---

## 2026-03-27 — Initial Build

### Session Summary

Built a complete Samsung SmartThings app that triggers home events (flash lights, toggle switches) when a selected Scottish football team scores a goal. Uses the ESPN undocumented public API and deploys to AWS via CDK.

### Architecture

**Hybrid: Python AWS backend + Node.js SmartThings frontend**

- **Fixture Checker Lambda** (Python, every 15 min) — discovers live/upcoming matches for tracked teams, enables/disables goal poller via CloudWatch Events
- **Goal Poller Lambda** (Python, every 60s, starts disabled) — detects score changes via ESPN API, fetches scorer details, triggers SmartThings devices via REST API
- **SmartApp Lambda** (Node.js) — SmartThings app UI for team selection, device configuration, competition filtering
- **DynamoDB** — 3 tables: installations, match_state, active_fixtures
- **API Gateway** — webhook endpoint for SmartThings lifecycle events
- **CloudWatch Events** — 2 rules: fixture checker (always on, 15 min), goal poller (toggled, 60s)

### Actions Taken

#### Phase 1: Project Scaffold (`3828f00`)
- Initialized git repo on `main` branch
- Created `pyproject.toml` with uv, targeting Python 3.14
- Configured ruff (lint + format), mypy (strict + pydantic plugin), pytest (socket-disabled, coverage)
- Created `.gitignore`, `.python-version`, `.pre-commit-config.yaml`, `cspell.config.yaml`
- Set up `cdk.json` and `cdk.context.json`
- Created full directory structure with `__init__.py` files for all packages
- Ran `uv sync` to install all dependencies

#### Phase 2: Core Application Logic (`34157f8`)

**Pydantic Models** (`app/goal_watcher/model/`)
- `espn.py` — ESPN API response models: scoreboard, competition, competitor, team, status, key events, summary, teams endpoint
- `match_state.py` — DynamoDB models: `MatchState`, `ActiveFixture`, `TeamScore`, `MatchStatus` enum
- `installation.py` — SmartApp installation model: `Installation`, `DeviceConfig`

**Shared Modules** (`app/goal_watcher/shared/`)
- `espn_client.py` — Async httpx client with methods: `fetch_scoreboard`, `fetch_scoreboards`, `fetch_match_summary`, `fetch_teams`, `fetch_all_scottish_teams`
- `dynamo.py` — DynamoDB helpers: CRUD for match state, active fixtures, installations (with `TYPE_CHECKING` guard for boto3 stubs)
- `scottish_leagues.py` — `ScottishLeague` StrEnum with all 7 competitions (sco.1–sco.4, cups)

**Fixture Checker Lambda** (`app/goal_watcher/fixture_checker/`)
- `fixture_scanner.py` — Scans ESPN scoreboards for matches involving tracked teams, maps ESPN states to `MatchStatus`
- `poller_control.py` — Enables/disables goal poller CloudWatch Events rule via EventBridge API
- `app.py` — Lambda handler: fetches tracked teams → polls ESPN → updates DynamoDB fixtures → toggles goal poller

**Goal Poller Lambda** (`app/goal_watcher/goal_poller/`)
- `goal_detector.py` — Compares stored vs live scores, detects new goals, attributes scorers from ESPN key events. Skips historical goals on first sighting.
- `smartthings_notifier.py` — SmartThings REST API client: `send_device_command`, `flash_lights` (3x on/off cycle), `toggle_switches`, `notify_installation`
- `app.py` — Lambda handler: reads live fixtures → polls ESPN → detects goals → fetches summaries → notifies SmartThings devices

**CDK Stack** (`app/goal_watcher/cdk/`)
- `constants.py` — Stack name, table names, rule names, `Outputs` StrEnum
- `goal_watcher_stack.py` — Full CDK stack: 3 DynamoDB tables (PAY_PER_REQUEST, PITR, GSI on team_id), 3 Lambda functions (ARM64, JSON logging), API Gateway, 2 CloudWatch Events rules, IAM permissions, cdk-nag AwsSolutionsChecks with targeted suppressions

**Node.js SmartApp** (`smartapp/`)
- `src/index.js` — Lambda handler bridging API Gateway events to SmartApp HTTP callback
- `src/smartapp.js` — SmartApp config pages: team selector dropdown, competition multi-select, light/switch device pickers. Lifecycle handlers for install/update/uninstall.
- `src/teams.js` — 42 Scottish football teams with **verified** ESPN IDs (fetched live from ESPN API for all 4 leagues)
- `src/dynamodb-context-store.js` — DynamoDB context store adapter for SmartThings SDK (get/put/update/delete)
- `package.json` — Dependencies: `@smartthings/smartapp`, `@aws-sdk/client-dynamodb`, `@aws-sdk/lib-dynamodb`

**CI/CD** (`.github/workflows/`)
- `ruff.yml` — Ruff lint + format check
- `mypy.yml` — Mypy strict type checking
- `pytest.yml` — Pytest with JUnit results + coverage reporting (60% threshold)
- `spellcheck.yml` — cspell

**CDK App Entry** (`app/app.py`)
- Instantiates `GoalWatcherStack` with cdk-nag `AwsSolutionsChecks` aspect

#### Phase 3: Documentation (`bd50663`)
- Created `README.md` with architecture diagram, two-poller design explanation, competitions table, prerequisites, setup/deployment guide, development commands, project structure, and how-it-works flow

#### Phase 4: Unit Tests (`7628ead`)

**Python Unit Tests (37 passing)**
- `tests/unit/shared/test_espn_client.py` (7 tests) — Scoreboard fetch (success, date param, HTTP error), multi-league with graceful failure, match summary, teams extraction, deduplication
- `tests/unit/fixture_checker/test_fixture_scanner.py` (9 tests) — Status mapping (all 4 states), fixture creation, scoreboard scanning (tracked teams, ignored teams, multi-league)
- `tests/unit/fixture_checker/test_poller_control.py` (5 tests) — Enable/disable/check CloudWatch Events rules
- `tests/unit/goal_poller/test_goal_detector.py` (11 tests) — No previous state, home/away goals, both teams score, no change, scorer attribution from key events, build match state, empty event, post/pre states
- `tests/unit/goal_poller/test_smartthings_notifier.py` (5 tests) — Device commands (success, error), flash lights sequence, notify installation (with/without auth token)

**CDK Stack Tests (14 passing)**
- `tests/unit/cdk/test_goal_watcher_stack.py` — DynamoDB (3 tables, PAY_PER_REQUEST, PITR, GSI), Lambda (3 functions, ARM64, env vars), API Gateway, CloudWatch Events (2 rules, poller starts disabled), stack outputs (7 present)

**Config changes**
- Added `pytest-asyncio`, `faker`, `boto3` to dev deps
- Added `asyncio_mode = "auto"` to pytest config
- Added `--allow-unix-socket` for CDK jsii subprocess compatibility
- Set coverage threshold to 60% (CDK tests run separately due to slow jsii synth)

### Bugs Found & Fixed During Testing
1. `Rule.grant()` doesn't exist in CDK 2.245.0 — replaced with `add_to_role_policy(iam.PolicyStatement(...))`
2. CfnOutput construct IDs collided with resource construct IDs — added `"Output"` suffix to output names
3. Multiple ruff violations fixed: unused imports, datetime timezone, asyncio import placement, function complexity (extracted `_process_fixture` helper)

---

## 2026-03-27 — Node.js Lambda Tests & Linting

### Summary

Added Jest unit tests (21 passing, 100% coverage) and ESLint configuration for the Node.js SmartApp Lambda. Wired both into CI (separate GitHub Actions workflows) and pre-commit hooks.

### Actions Taken

- `feat:` Created `smartapp/eslint.config.js` — ESLint 9 flat config with `@eslint/js` recommended rules, Node and Jest globals
- `feat:` Created `smartapp/jest.config.js` — Jest config for ESM (`transform: {}`), 80% coverage threshold, excludes `smartapp.js` (SDK wiring, no business logic)
- `chore:` Updated `smartapp/package.json` test script to use `--experimental-vm-modules` for ESM compatibility; installed `@eslint/js@^9` devDependency
- `test:` Added `smartapp/src/__tests__/teams.test.js` — validates shape, uniqueness, and count (42 teams) for `SCOTTISH_TEAMS`
- `test:` Added `smartapp/src/__tests__/dynamodb-context-store.test.js` — mocks AWS SDK via `jest.unstable_mockModule`, covers get/put/update/delete including null return and merge behaviour
- `test:` Added `smartapp/src/__tests__/index.test.js` — mocks `smartapp.js`, tests JSON string/object body parsing and all response paths (`res.status().json()`, `res.status().send()`, `res.json()`)
- `fix:` Renamed unused `reject` → `_reject` in `smartapp/src/index.js` (caught by ESLint `no-unused-vars`)
- `feat:` Created `.github/workflows/node-lint.yml` — runs ESLint on push/PR to main
- `feat:` Created `.github/workflows/node-test.yml` — runs Jest with coverage on push/PR to main
- `chore:` Added local ESLint pre-commit hook to `.pre-commit-config.yaml` scoped to `smartapp/src/**/*.js`

### Commits

- (pending commit)

---



### Deployment
- [ ] Create a SmartThings developer account at [developer.smartthings.com](https://developer.smartthings.com/)
- [ ] Register a new SmartApp project (Automation, WebHook Endpoint)
- [ ] Bootstrap CDK: `cdk bootstrap`
- [ ] Deploy the stack: `cdk deploy GoalWatcherStack`
- [ ] Paste the API Gateway URL into SmartThings Developer Workspace as the webhook endpoint
- [ ] Set app permissions: `r:devices:*`, `x:devices:*`
- [ ] Install the SmartApp on phone → select St Johnstone → pick lights/switches → select competitions

### Testing & Validation
- [ ] Integration test: invoke fixture checker Lambda manually with a live Scottish match day
- [ ] Integration test: invoke goal poller Lambda during a live match to verify goal detection
- [ ] End-to-end test: verify SmartThings devices respond to a detected goal
- [ ] Test SmartApp installation lifecycle on a real SmartThings hub
- [ ] Verify OAuth token storage and retrieval between Node.js SmartApp and Python poller

### Enhancements
- [ ] Add push notifications via SmartThings notification capability (in addition to device commands)
- [ ] Add colour support for smart bulbs (flash in team colours — St Johnstone blue)
- [ ] Add match start/end notifications (not just goals)
- [ ] Add opponent goal alerts (optional — "the other team scored against you")
- [ ] Implement OAuth token refresh in the Python poller (currently relies on Node.js SDK context store)
- [ ] Add a Lambda dependency layer (built from `uv.lock`) instead of bundling deps in Lambda zip
- [ ] Consider EventBridge Scheduler instead of enable/disable pattern for cleaner poller control
- [ ] Add match-day awareness to fixture checker (skip polling on non-match days using ESPN calendar)

### Code Quality
- [ ] Increase test coverage to 80%+ (add Lambda handler tests, DynamoDB helper tests)
- [x] Add Jest tests for the Node.js SmartApp
- [ ] Run mypy strict on all code and fix any type errors
- [ ] Add pre-commit hooks validation to CI
- [ ] Add `taplo` TOML formatting
