# Copilot Instructions — Node.js

Node.js development conventions for this project. Follow these unless the project or prompt explicitly says otherwise.

---

## Language & Modules

- **Use ES modules (`"type": "module"` in `package.json`).** Always use `import`/`export` syntax — never `require()` or `module.exports`.
- Target **Node.js LTS**. Use modern JS: optional chaining (`?.`), nullish coalescing (`??`), `async`/`await`, destructuring.
- Prefer `const` over `let`; never use `var`.
- Prefix intentionally unused function parameters with `_` (e.g., `_context`, `_reject`).

## Package Management

- **npm** is the package manager for the `smartapp/` directory. Use `npm install`, `npm ci`, `npm run`.
- Keep `package-lock.json` committed and use `npm ci` in CI.
- Separate runtime `dependencies` from `devDependencies` — lint tools, test runners, and type tools are always dev-only.

## Linting

- **ESLint 9** with flat config (`eslint.config.js`). Use `@eslint/js` recommended rules as the base.
- Define separate config blocks for source files and test files (test globals: `describe`, `it`, `expect`, `jest`, etc.).
- Key rules to enforce:
  - `no-unused-vars` with `argsIgnorePattern: "^_"`
  - `eqeqeq: ["error", "always"]`
  - `curly: ["error", "all"]`
- Run via `npm run lint`. Wire into pre-commit (local `language: system` hook) and CI.

## Testing

- **Jest** as the test framework.
- Because the project uses ES modules, Jest requires:
  - `transform: {}` in `jest.config.js` to disable the default CJS transform
  - Test script: `node --experimental-vm-modules node_modules/.bin/jest`
- Test files live in `src/__tests__/` alongside the source they test.
- **Mocking in ESM:** use `jest.unstable_mockModule()` (not `jest.mock()`) and import `jest` explicitly:
  ```js
  import { jest } from '@jest/globals';
  jest.unstable_mockModule('../some-module.js', () => ({ ... }));
  // dynamic import MUST come after unstable_mockModule calls
  const { myExport } = await import('../module-under-test.js');
  ```
- Coverage: 80% threshold on statements, branches, functions, and lines. Exclude pure SDK wiring / config entry points from `collectCoverageFrom`.
- Run via `npm test -- --coverage`.

## CI

- Separate GitHub Actions workflows for lint and tests, matching the Python workflow pattern:
  - `.github/workflows/node-lint.yml` — runs `npm run lint`
  - `.github/workflows/node-test.yml` — runs `npm test -- --coverage`
- Both workflows use `actions/setup-node@v4` with `node-version: lts/*` and `cache: npm`.
- Use `working-directory: smartapp` for all `run` steps.
