# Repository Guidelines

## Project Structure & Module Organization
- Place runnable Kafka examples in `src/` grouped by role: `src/producers`, `src/consumers`, `src/streams`.
- Keep shared utilities in `src/common` and configuration defaults in `config/` (include `.env.example` for connection settings).
- Store Docker/infra assets in `docker/` (e.g., `docker-compose.yml`, broker configs); helper scripts live in `scripts/`.
- Tests belong in `tests/`, mirroring `src/` paths; shared fixtures go under `tests/fixtures`.
- Put docs and diagrams in `docs/`; avoid cluttering the repo root with ad hoc files.

## Build, Test, and Development Commands
- Prefer `make` (or `just`) targets to wrap common tasks; baseline targets to add:
  - `make up`: `docker compose up -d` to start the local Kafka stack.
  - `make down`: tear down the stack and volumes to reset state.
  - `make run-producer NAME=...`: run a producer example by name.
  - `make test`: run the test suite; use language-specific runners inside containers if needed.
- When no Makefile exists, bring up Kafka with `docker compose up -d` and run example entrypoints directly.

## Coding Style & Naming Conventions
- Use 4 spaces for Python/Scala/Java code; 2 spaces for YAML/JSON.
- File names: `snake_case` for scripts/modules, `PascalCase` for classes/types, `kebab-case` for directories and topic-specific folders.
- Run formatters/linters before committing: Python (`black`, `ruff`), JS/TS (`prettier`, `eslint`), Java/Scala (`spotless`/`scalafmt`) as applicable. Keep configs versioned (`pyproject.toml`, `.prettierrc`, etc.).

## Testing Guidelines
- Place unit and integration tests under `tests/` with names like `test_*.py` or `*_test.js`.
- Favor integration tests that cover producer → topic → consumer flows using the local `docker compose` cluster.
- Use fixtures to seed/clean topics; avoid relying on already-running brokers.
- Add coverage for error handling (retries, dead-letter topics) before merging feature work.

## Commit & Pull Request Guidelines
- Write imperative, scope-prefixed commits (e.g., `feat: add producer retry config`, `fix: close consumer on shutdown`).
- Keep PRs small and focused; include what changed, why, and how to validate (commands/output).
- Link issues when relevant; attach screenshots or logs for operational changes.
- Update docs (`README.md`, `docs/`) when adding new topics, configs, or commands.

## Security & Configuration Tips
- Never commit secrets; store broker credentials in `.env` and provide `.env.example` with safe defaults.
- Document required ports and network settings in `docker/` configs; prefer localhost-only bindings for local dev.
- If adding ACLs or auth, include steps to provision users and permissions in setup scripts.
