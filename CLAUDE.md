# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Pipework?

Pipework is a **terminal-first narrative engine** for moving actions through constrained systems and recording outcomes. It is world-agnostic machinery designed for flow, consequence, and record-keeping—not a game framework or UI toolkit.

**Core Philosophy:**
- Intent rarely survives contact with reality
- Failures are informative
- Everything that happens gets written down
- Failure is data, not an exception

## Architecture Overview

Pipework is structured around four fundamental concepts:

### 1. Actions
Things that are attempted (see `Action` class in `pipework/core/engine.py:22`). Actions contain:
- `name`: what is being attempted
- `payload`: arbitrary data dictionary
- `actor`: optional identifier for who/what initiated the action

### 2. Pipes
Functions that process actions and produce outcomes (`Callable[[Action], Outcome]`). Registered via `engine.register_pipe()`.

**Critical behavior:**
- Pipes are evaluated in registration order
- The **first pipe to return an Outcome ends the flow**
- If no pipe handles the action, the engine produces an "unhandled" outcome
- Pipes can return `None` to pass control to the next pipe

### 3. Outcomes
What actually happened (see `Outcome` class in `pipework/core/engine.py:30`). Contains:
- `status`: result classification (e.g., "accepted", "error", "unhandled")
- `details`: arbitrary data dictionary
- `notes`: optional human-readable information
- `timestamp`: when the outcome occurred

### 4. Ledger
The authoritative record of all events (see `LedgerEntry` class in `pipework/core/engine.py:39`). Every action processed through the engine is recorded with its outcome, even failures.

## Core Guarantees

The `PipeworkEngine.process()` method (line 72) provides two guarantees:
1. An Outcome is **always** produced (even if pipes raise exceptions)
2. The Outcome is **always** recorded in the ledger

If a pipe raises an exception, the engine catches it and produces an Outcome with `status="error"` containing exception details.

## Project Structure

```
pipework/
├── core/
│   ├── __init__.py       # Exports PipeworkEngine, Action, Outcome
│   └── engine.py         # Core engine implementation (~500 lines, fully documented)
├── __init__.py           # Package root
examples/
└── minimal.py            # Reference implementation showing basic usage
tests/
├── __init__.py
├── conftest.py           # Shared test fixtures
├── test_engine.py        # Comprehensive test suite (53 tests, 100% coverage)
└── README.md             # Test documentation
pyproject.toml            # Project config (pytest, mypy, ruff, coverage)
```

## Development Commands

**Install development dependencies:**
```bash
pip install -e ".[dev]"
```

**Run tests:**
```bash
pytest tests/                                        # Basic run
pytest tests/ -v                                     # Verbose
pytest tests/ --cov=pipework --cov-report=term-missing  # With coverage
```

**Run examples:**
```bash
PYTHONPATH=. python examples/minimal.py
```

**Run Python interactively with the engine:**
```bash
PYTHONPATH=. python
>>> from pipework.core import PipeworkEngine, Action, Outcome
>>> engine = PipeworkEngine()
```

**Code quality checks:**
```bash
ruff check .              # Linting
ruff format .             # Formatting
mypy pipework --strict    # Type checking
```

**Python version:**
The project uses Python 3.10+ as specified in `.python-version` and `pyproject.toml`.

## Design Constraints

When working with Pipework, respect these principles:

### Terminal-first
If it doesn't work in a terminal, it doesn't belong in the core. No GUI dependencies.

### Deterministic by default
Randomness is allowed but must be explicit and visible in the ledger.

### All outcomes are recorded
Success, failure, partial completion, or quiet disaster—everything goes in the ledger.

### Pipes must be pure handlers
A pipe should:
- Examine the action
- Decide if it handles it
- Return an Outcome or None

Avoid pipes with side effects beyond logging to the ledger.

### What Pipework is NOT
- Not a game engine or real-time simulation
- Does not provide quests, characters, or UI
- Does not generate content by itself
- Not opinionated about genre or narrative style

## Typical Usage Pattern

See `examples/minimal.py:13` for reference:

1. Create a `PipeworkEngine` instance
2. Define pipe functions that examine actions and return outcomes
3. Register pipes with `engine.register_pipe(pipe_function)`
4. Create `Action` instances
5. Call `engine.process(action)` to get an `Outcome`
6. Access the full history via `engine.ledger()`

## Testing

The project has a comprehensive test suite with 100% coverage:

- **53 tests** covering all engine functionality
- **Organized by category**: data structures, processing, ordering, exceptions, ledger, edge cases
- **Modern pytest practices**: fixtures, parametrized tests, descriptive names
- **Full documentation**: Every test has a docstring explaining what it tests

When adding new features:
1. Write tests first or alongside implementation
2. Maintain 100% code coverage
3. Test both success and failure paths
4. Include edge cases (empty values, None, large inputs)
5. Use fixtures for reusable test data
6. Run `pytest tests/ --cov=pipework` to verify coverage

See `tests/README.md` for detailed test documentation.

## License

GPL-3.0. Tools and engines built on Pipework should remain inspectable.
