# Agent Workflow Rules (Repo Root)

This repository expects disciplined changes that keep the simulator in a green state.

## Local validation
- Run unit tests: `python -m unittest discover -s tests -p "test_*.py" -v`
- Confirm CLI help: `python -m virtual_tdi --help`
- Confirm import: `python -c "import virtual_tdi"`

## Change management
- Prefer small, focused commits with clear messages.
- Avoid large refactors or domain-heavy changes unless required to fix failing tests.
- New tooling should be lightweight; use a separate `requirements-dev.txt` if needed.

## CI/Release expectations
- CI must remain green on Python 3.12.
- Releases are tagged from `main` (see `docs/WORKFLOW.md`).

## PR expectations
- Include: summary, testing commands/results, and follow-up tasks.
- Never include secrets; report only paths and issue type if found.
