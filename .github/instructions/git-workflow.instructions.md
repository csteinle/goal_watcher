# Copilot Instructions — Git Workflow

Conventions for branching, committing, and raising pull requests. Follow these on every task.

---

## Branching

- **Never commit directly to `main`.** All work — including small fixes, documentation updates, and refactors — must be done on a feature branch.
- Branch names should use kebab-case with a short conventional prefix:
  - `feat/` — new features
  - `fix/` — bug fixes
  - `chore/` — dependency updates, tooling, config
  - `docs/` — documentation only
  - `test/` — adding or updating tests
  - `refactor/` — restructuring without behaviour change
- Base feature branches off the current `main` (or the relevant base branch if working from an open PR).
- After the PR is merged, the feature branch should be deleted.

## Committing

- **Commit regularly** as logical units of work are completed — not just once at the end of a session.
  Good checkpoints: after a config file is wired up, after a module is written, after tests pass for a module.
- **Commit messages must be moderately verbose:**
  - First line: conventional commit prefix + short imperative summary (≤72 chars), e.g. `feat: add DynamoDB context store for SmartApp`.
  - Body (required when the change is non-trivial): 2–5 bullet points or short sentences explaining *what* changed and *why*. Wrap at 72 characters.
  - Footer: always include the `Co-authored-by` trailer for Copilot commits (see below).
- Use conventional commit prefixes: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`, `perf:`.
- One logical concern per commit. Don't bundle unrelated changes.

### Example commit message

```
feat: add Jest config and ESM test infrastructure

- Configure jest.config.js with transform: {} for native ESM support
- Update test script to use --experimental-vm-modules
- Install @eslint/js@^9 devDependency for flat config support
- Exclude smartapp.js from coverage (SDK wiring, no business logic)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## Pull Requests

- **Every feature branch must be raised as a pull request** before merging. Do not push directly to `main`.
- PR titles follow the same conventional commit format as the primary commit: `feat: short description`.
- PR descriptions must include:
  - **Summary** — one or two sentences on what this PR does and why.
  - **Changes** — grouped bullet list of what was added/modified/deleted.
  - **Testing** — how the changes were verified (test output, manual steps, etc.).
- Target `main` unless the work builds on another open branch.
- Keep PRs focused — one feature or fix per PR where practical.

## Copilot Co-author Trailer

Always append this trailer to every commit message created during a Copilot session:

```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```
