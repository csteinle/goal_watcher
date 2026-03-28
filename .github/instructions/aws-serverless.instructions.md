# Copilot Instructions — AWS Serverless

AWS-specific conventions for serverless projects using CDK and Lambda. Follow these unless the project or prompt explicitly says otherwise.

---

## AWS CDK

- **AWS CDK with Python** for all infrastructure. CDK app entry point is `app/app.py`.
- Always apply **cdk-nag** `AwsSolutionsChecks` as an Aspect. Add targeted `NagSuppressions` with clear `reason` strings when suppressing — never blanket-suppress. Always obtain explicit permission when adding suppressions, and explain why when asking for this.
- Use **Lambda dependency layers** built from `uv.lock` using a custom `DependencyLayer` construct that exports requirements via `uv export`. See the **Lambda Dependency Layer** section below for full details.
- Default Lambda config: **ARM_64 architecture**, **JSON logging format**, **Lambda Insights** enabled, explicit **log group** with short retention (1 week) and `DESTROY` removal policy.
- Use `CfnOutput` for all stack outputs needed by tests or other consumers. Define output names as a `StrEnum` class (e.g., `class Outputs(StrEnum)`) on the Stack class.
- Use `RemovalPolicy.DESTROY` for scratch/dev resources. Enable point-in-time recovery for DynamoDB tables.
- Enforce SSL on SQS queues (`enforce_ssl=True`).

## Lambda Dependency Layer

The `DependencyLayer` construct (lives at `app/<project>/cdk/dependency_layer.py`) bundles Python runtime dependencies from `uv.lock` into a Lambda layer so they are not included in the function code asset.

### How it works

1. **Local step** — `DependencyLayer.Bundler.try_bundle()` runs `uv export --no-dev --frozen` to generate `build/requirements.txt` from `uv.lock`. Returns `False` so CDK continues to the Docker step.
2. **Docker step** — CDK runs `pip3 install -r requirements.txt -t /asset-output/python` inside the Lambda runtime image, producing an architecture-correct layer package.
3. The layer is fingerprinted against `uv.lock` so it is only rebuilt when dependencies change.

### pyproject.toml structure

Keep CDK and dev tooling in `[dependency-groups] dev`. Keep only Lambda runtime deps in `[project] dependencies` — these are what `uv export --no-dev` exports into the layer:

```toml
[project]
dependencies = [
    "aws-lambda-powertools>=...",
    "boto3>=...",
    "pydantic>=...",
    # any other runtime-only deps
]

[dependency-groups]
dev = [
    "aws-cdk-lib>=...",
    "cdk-nag>=...",
    "constructs>=...",
    "mypy>=...",
    "pytest>=...",
    # ...
]
```

If a Lambda needs a subset of deps, define a named group and pass `dependency_group="lambda"` to `DependencyLayer`.

### Usage in a stack

```python
from .dependency_layer import DependencyLayer

LAMBDA_RUNTIME = lambda_.Runtime.PYTHON_3_13
LAMBDA_ARCHITECTURE = lambda_.Architecture.ARM_64

dependency_layer = DependencyLayer(
    self,
    "MyDependencyLayer",
    runtime=LAMBDA_RUNTIME,
    architecture=LAMBDA_ARCHITECTURE,
    # dependency_group="lambda"  # omit to export all non-dev deps
)

fn = lambda_.Function(
    self, "MyFunction",
    runtime=LAMBDA_RUNTIME,
    architecture=LAMBDA_ARCHITECTURE,
    layers=[dependency_layer],
    code=lambda_.Code.from_asset("app", exclude=["**/cdk/**", "**/__pycache__"]),
    handler="my_project.my_lambda.app.handler",
    ...
)
```

### Stubbing in CDK unit tests

The real `DependencyLayer` requires Docker (for bundling). Stub it in test conftest so tests run without Docker:

```python
import tempfile
from unittest.mock import patch
from aws_cdk import aws_lambda as lambda_

class _StubDependencyLayer(lambda_.LayerVersion):
    def __init__(self, scope, id, **_kwargs):
        super().__init__(scope, id, code=lambda_.Code.from_asset(tempfile.mkdtemp()))

@pytest.fixture
def template() -> Template:
    with patch("app.<project>.cdk.<stack_module>.DependencyLayer", _StubDependencyLayer):
        app = App()
        stack = MyStack(app, "TestStack")
    return Template.from_stack(stack)
```



- **Always use AWS Lambda Powertools:**
  - `Logger` with `@logger.inject_lambda_context(clear_state=True)` decorator.
  - `Tracer` with `@tracer.capture_lambda_handler` decorator.
  - `BatchProcessor` with `process_partial_response` for SQS batch processing.
  - Powertools `SqsRecordModel` subclasses with `Json[T]` for typed SQS record bodies.
- Handler signature: `def handler(event: dict[str, Any], context: LambdaContext) -> ReturnType`.
- Environment variables for runtime config (e.g., table names). Access via `os.environ["VAR_NAME"]`.
- Lambda handler code lives in `app/<project_name>/<lambda_function_name>/app.py`, with other modules in the same dir or in `app/<project_name>/shared` as appropriate . Exclude CDK, code from other lambdas, and test code from the Lambda bundle via `Code.from_asset("app", exclude: ['**', '!<project_name>/<lambda_function_name/**', '!<project_name>/shared/**', '**/__pycache__'], ignoreMode: cdk.IgnoreMode.DOCKER)`.
- Use `TYPE_CHECKING` guards for boto3 type stubs to keep them out of the Lambda runtime bundle:
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from types_boto3_dynamodb.service_resource import Table
  else:
      Table = object
  ```

## AWS Testing

### Unit Tests
- CDK unit tests: stub out the `DependencyLayer` and use `assertions.Template.from_stack()` for snapshot/property assertions.
- Mock AWS services manually with `unittest.mock.patch` and `MagicMock`. Do not use moto.
- For SQS record factories, override the `body()` classmethod to return serialized Pydantic model JSON.

### Integration Tests
- Mark integration tests with `@pytest.mark.enable_socket` to allow network access.
- Deploy real stacks via CDK in session-scoped fixtures. Extract outputs from the deployed CloudFormation stack.
- Use 1Password SDK for AWS credentials in integration tests.
- Invoke Lambdas directly via `boto3_lambda_client.invoke()` and assert on response payloads and logs.
- Pre-commit hook `detect-aws-credentials` with `--allow-missing-credentials` to avoid accidental credential commits.

## Project Layout

Follow this directory structure for new projects:
```
app/
  app.py                              # CDK app entrypoint
  <project_name>/
    __init__.py
    cdk/
      __init__.py                     # __all__ exports
      <project_name>_stack.py         # Main CDK stack
      constants.py                    # STACK_NAME, etc.
      dependency_layer.py             # Lambda dependency layer construct
    <lambda_function1_name>/
      __init__.py
      app.py                          # Lambda handler for lambda_function1
      ...
    <lambda_function2_name>/
      __init__.py
      app.py                          # Lambda handler for lambda_function2
      ...
    <shared>/
      __init__.py
      ...
    model/
      __init__.py                     # __all__ exports
      <model_name>.py                 # Pydantic models
  tests/
    __init__.py
    conftest.py                       # Shared fixtures, polyfactory setup
    unit/
      __init__.py
      cdk/
        conftest.py
        test_<stack>.py
      lambda_function/
        conftest.py
        test_app.py
    integration/
      __init__.py
      conftest.py                     # AWS session, deployed stack fixtures
      test_*.py
pyproject.toml
cdk.json
cdk.context.json
cspell.config.yaml
.pre-commit-config.yaml
.python-version
.gitignore
```

## CI/CD (GitHub Actions)

- Separate workflows for: **unit tests**, **ruff**, **mypy**, **spellcheck**. Keeps CI fast and failures easy to identify.
- All workflows use `astral-sh/setup-uv` with caching enabled.
- Install with `uv sync --locked --all-extras --dev`.
- Publish test results with `EnricoMi/publish-unit-test-result-action`.
- Publish coverage with `insightsengineering/coverage-action` (80% threshold, fail on miss).
