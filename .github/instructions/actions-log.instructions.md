# Copilot Instructions — Actions Log

Maintain the `ACTIONS.md` file at the project root as a living record of all development activity.

---

## Rules

- **Update `ACTIONS.md` after every session** that makes changes to the codebase.
- Each session entry should include:
  - **Date** as a heading (e.g., `## 2026-03-28 — Feature Name`)
  - **Summary** — one or two sentences describing what was done
  - **Actions Taken** — bullet list of specific changes, grouped by phase or component
  - **Bugs Found & Fixed** — if any were discovered and resolved
  - **Commits** — list the git commit hashes and messages created during the session
- **Keep the TODO section current** — check off completed items, add new ones as they arise.
- When completing a TODO item, move it from the TODO section into the relevant session's "Actions Taken" with a note that it was completed.
- Use conventional commit prefixes in action descriptions where applicable (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).

## Format

```markdown
## YYYY-MM-DD — Brief Title

### Summary
One or two sentences.

### Actions Taken
- thing 1
- thing 2

### Commits
- `abc1234` feat: description
- `def5678` fix: description

---
```

## TODO Section

- Keep the `## TODO — Next Steps` section at the bottom of the file.
- Group items under clear category headings (Deployment, Enhancements, Code Quality, etc.).
- Use `- [ ]` for pending items and `- [x]` for completed items.
- When all items in a category are done, remove the category.
