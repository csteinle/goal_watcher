# Copilot Instructions — Python

General Python development conventions. Follow these unless the project or prompt explicitly says otherwise.

---

## Language

- **Target Python 3.14**. Use modern syntax: `type` statements, `X | Y` unions, `dict` / `list` / `tuple` lowercase generics.
- **Strict type hints everywhere.** Every function signature and variable where the type isn't obvious from context.
- **mypy strict mode** with the `pydantic.mypy` plugin if pydantic is in use. All code must pass `mypy --strict`.
- **Pydantic models** for all structured data — event payloads, database items, API request/response bodies, configuration. Prefer `BaseModel` subclasses over plain dicts or dataclasses.
- Clean `__init__.py` files with explicit `__all__` exports for public modules.
- Use `StrEnum` for string constant groups.
- Use `@cache` from `functools` for singleton resources.

## Package Management

- **uv is the primary tool.** Use `uv sync`, `uv run`, `uv add`, `uv lock` for all dependency operations.
- Only use **Poetry** when there's a specific compatibility issue (e.g., a dependency that doesn't build with uv). When Poetry is needed, keep both `uv.lock` and `poetry.lock` in sync.
- Use **dependency groups** in `pyproject.toml` to separate runtime deps, dev deps, and context-specific deps.

## Linting & Formatting

- **Ruff** for both linting and formatting. Use this rule set unless the project overrides it:
  ```
  select = ["A", "B", "C", "C4", "DTZ", "E", "F", "FURB", "G", "I", "LOG", "N",
            "PERF", "PL", "PT", "PTH", "Q", "RET", "RSE", "RUF", "S", "T", "TID",
            "TRY", "UP", "W"]
  ignore = ["E501", "TRY003"]
  ```
- Allow `assert` in tests: `[tool.ruff.lint.per-file-ignores] "**/tests/*" = ["S101"]`
- Use `combine-as-imports = true` for isort.
- **yamllint** (strict + parsable) for YAML files.
- **taplo** for TOML formatting and linting.
- **cspell** for spell checking code and commit messages. Maintain a `cspell.config.yaml` with project-specific words.

## Pre-commit

- Always use **pre-commit** with hooks for: ruff (check + format), uv-lock, yamllint, yamlfmt, taplo, cspell, and standard pre-commit-hooks (trailing whitespace, end-of-file-fixer, detect-private-key, no-commit-to-branch on main).
- When adding new files or tools, check if a pre-commit hook should be added.

## Testing

### General
- **pytest** as the test framework. Use `--disable-socket` (pytest-socket) by default to block network calls in unit tests.
- Coverage: `--cov`, `--cov-branch`, 80% threshold minimum.

### Test Data
- **polyfactory** + **faker** for generating test data from Pydantic models. Always seed factories for reproducibility:
  ```python
  @pytest.fixture(autouse=True)
  def faker_seed() -> int:
      return <project_specific_int>

  @pytest.fixture(autouse=True)
  def seed_factories(faker: Faker, faker_seed: int) -> None:
      ModelFactory.__faker__ = faker
      ModelFactory.__random__.seed(faker_seed)
  ```
- Use `@register_fixture` to expose polyfactory factories as pytest fixtures.

### Unit Tests
- Mock dependencies manually with `unittest.mock.patch` and `MagicMock`. Do not use moto.
- Use `patch.object` targeting the module under test (e.g., `patch.object(app, "some_dependency")`).
- Use `patch.dict(os.environ, {...})` for environment variable fixtures.
