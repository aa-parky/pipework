# Pipework Test Suite

Comprehensive test coverage for the Pipework narrative engine.

## Overview

This test suite provides thorough coverage of all Pipework engine functionality with 53 tests achieving 100% code coverage.

## Running Tests

### Basic test run
```bash
pytest tests/
```

### With coverage report
```bash
pytest tests/ --cov=pipework --cov-report=term-missing
```

### Verbose output
```bash
pytest tests/ -v
```

### Run specific test class
```bash
pytest tests/test_engine.py::TestActionProcessing -v
```

### Run specific test
```bash
pytest tests/test_engine.py::TestActionProcessing::test_process_action_with_matching_pipe -v
```

## Test Organization

Tests are organized into logical groups using test classes:

### Core Data Structure Tests
- **TestAction**: Tests for Action dataclass creation and attributes
- **TestOutcome**: Tests for Outcome dataclass creation and attributes
- **TestLedgerEntry**: Tests for LedgerEntry dataclass creation and attributes

### Engine Tests
- **TestEngineInitialization**: Tests for PipeworkEngine initialization
- **TestPipeRegistration**: Tests for registering pipes with the engine
- **TestActionProcessing**: Tests for processing actions through pipes
- **TestPipeOrdering**: Tests for pipe evaluation order and short-circuiting
- **TestExceptionHandling**: Tests for exception handling and error outcomes
- **TestLedgerRecording**: Tests for ledger recording and history

### Edge Cases and Integration
- **TestEdgeCases**: Boundary conditions and edge cases
- **TestIntegrationScenarios**: Multi-pipe realistic scenarios
- **TestParametrized**: Parametrized tests for multiple similar cases

## Test Coverage

Current coverage: **100%**

- All public APIs are tested
- All private methods are tested indirectly through public API
- All error paths are tested
- All edge cases are tested

Coverage breakdown:
```
pipework/__init__.py          100%
pipework/core/__init__.py     100%
pipework/core/engine.py       100%
```

## Key Test Scenarios

### Basic Functionality
- Action, Outcome, and LedgerEntry creation
- Engine initialization with empty state
- Single and multiple pipe registration
- Action processing through pipes

### Pipe Behavior
- Pipe ordering and evaluation
- Short-circuit evaluation (first outcome wins)
- Pipes returning None to pass control
- Access to action payload and actor

### Error Handling
- Exceptions caught and converted to error outcomes
- Different exception types properly recorded
- Engine continues after exceptions
- Error outcomes recorded in ledger

### Ledger Recording
- All outcomes recorded (success, failure, unhandled, error)
- Chronological order preserved
- Ledger returns copy, not reference
- Multiple actions create multiple entries

### Integration Scenarios
- Validation → Handler pipelines
- Multiple specialized handlers
- Permission checking before processing
- Payload transformation patterns

## Test Fixtures

Shared fixtures defined in `conftest.py` and test files:

- `engine`: Fresh PipeworkEngine instance for each test
- `simple_action`: Basic action with minimal context
- `action_with_payload`: Action with payload data for testing

## Dependencies

- pytest >= 8.0.0
- pytest-cov >= 4.1.0

Install with:
```bash
pip install -e ".[dev]"
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. See `.github/workflows/python-ci.yml` for GitHub Actions configuration (when available).

## Writing New Tests

When adding new tests:

1. **Use descriptive names**: `test_<what>_<condition>_<expected_result>`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures**: For reusable test setup
4. **Document tests**: Clear docstrings explaining what is tested
5. **Group related tests**: Use test classes to organize
6. **Parametrize when appropriate**: For testing multiple similar cases
7. **Test edge cases**: Empty inputs, None values, large payloads, etc.

Example:
```python
def test_pipe_handles_specific_action(self, engine: PipeworkEngine) -> None:
    """Test that pipe correctly processes its target action type."""
    # Arrange
    def my_pipe(action: Action) -> Outcome | None:
        if action.name == "my_action":
            return Outcome(status="success")
        return None

    engine.register_pipe(my_pipe)

    # Act
    outcome = engine.process(Action(name="my_action"))

    # Assert
    assert outcome.status == "success"
```

## Continuous Improvement

Test suite goals:
- Maintain 100% code coverage
- Add tests for all new features
- Update tests when behavior changes
- Keep tests fast (< 1 second total runtime)
- Keep tests independent (no shared state)
