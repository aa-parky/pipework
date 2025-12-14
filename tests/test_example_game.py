"""Comprehensive test suite for the example_game.py demonstration.

This test suite validates the goblin mining game example, covering:
- Individual pipe function behavior
- Pipe ordering and interaction
- State management
- Ledger recording
- Edge cases and error conditions
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add examples directory to path so we can import the game
examples_dir = Path(__file__).parent.parent / "examples"
sys.path.insert(0, str(examples_dir))

# Import the game module - this must come after path manipulation
# ruff: noqa: E402
from example_game import fatigue_pipe, goblin_state, mining_pipe, rest_pipe

from pipework.core import Action, PipeworkEngine

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def reset_goblin_state() -> None:
	"""Reset goblin state before each test to ensure test isolation.

	This fixture prevents test pollution by resetting the global state
	to its initial values before each test runs.
	"""
	goblin_state["ore"] = 0
	goblin_state["tired"] = False


@pytest.fixture
def fresh_engine() -> PipeworkEngine:
	"""Create a fresh PipeworkEngine instance for testing.

	Returns:
		New PipeworkEngine instance with no pipes registered.
	"""
	return PipeworkEngine()


@pytest.fixture
def game_engine(fresh_engine: PipeworkEngine) -> PipeworkEngine:
	"""Create a game engine with all pipes registered in correct order.

	Args:
		fresh_engine: Empty PipeworkEngine instance.

	Returns:
		PipeworkEngine with fatigue, mining, and rest pipes registered.
	"""
	fresh_engine.register_pipe(fatigue_pipe)
	fresh_engine.register_pipe(mining_pipe)
	fresh_engine.register_pipe(rest_pipe)
	return fresh_engine


# ============================================================================
# Fatigue Pipe Tests
# ============================================================================


def test_fatigue_pipe_blocks_tired_mining(reset_goblin_state: None) -> None:
	"""Test that fatigue_pipe prevents mining when goblin is tired."""
	# Arrange
	goblin_state["tired"] = True
	action = Action(name="mine", actor="goblin_1")

	# Act
	outcome = fatigue_pipe(action)

	# Assert
	assert outcome is not None
	assert outcome.status == "failure"
	assert "too tired" in outcome.notes.lower()


def test_fatigue_pipe_allows_fresh_mining(reset_goblin_state: None) -> None:
	"""Test that fatigue_pipe allows mining when goblin is not tired."""
	# Arrange
	goblin_state["tired"] = False
	action = Action(name="mine", actor="goblin_1")

	# Act
	outcome = fatigue_pipe(action)

	# Assert - returns None to pass to next pipe
	assert outcome is None


def test_fatigue_pipe_ignores_non_mining_actions(reset_goblin_state: None) -> None:
	"""Test that fatigue_pipe ignores actions other than mining."""
	# Arrange
	goblin_state["tired"] = True
	actions = [
		Action(name="rest", actor="goblin_1"),
		Action(name="dance", actor="goblin_1"),
		Action(name="sleep", actor="goblin_1"),
	]

	# Act & Assert
	for action in actions:
		outcome = fatigue_pipe(action)
		assert outcome is None, f"fatigue_pipe should ignore {action.name}"


def test_fatigue_pipe_with_different_actors(reset_goblin_state: None) -> None:
	"""Test that fatigue_pipe works with different actor identifiers."""
	# Arrange
	goblin_state["tired"] = True
	actors = ["goblin_1", "goblin_2", "player_1", None]

	# Act & Assert
	for actor in actors:
		action = Action(name="mine", actor=actor)
		outcome = fatigue_pipe(action)
		assert outcome is not None
		assert outcome.status == "failure"


# ============================================================================
# Mining Pipe Tests
# ============================================================================


def test_mining_pipe_generates_ore(reset_goblin_state: None) -> None:
	"""Test that mining_pipe generates ore and updates state."""
	# Arrange
	initial_ore = goblin_state["ore"]
	action = Action(name="mine", actor="goblin_1")

	# Act
	outcome = mining_pipe(action)

	# Assert
	assert outcome is not None
	assert outcome.status == "success"
	assert "ore_gained" in outcome.details
	assert 1 <= outcome.details["ore_gained"] <= 3
	assert goblin_state["ore"] == initial_ore + outcome.details["ore_gained"]
	assert goblin_state["tired"] is True


def test_mining_pipe_makes_goblin_tired(reset_goblin_state: None) -> None:
	"""Test that mining_pipe sets goblin to tired state."""
	# Arrange
	goblin_state["tired"] = False
	action = Action(name="mine", actor="goblin_1")

	# Act
	mining_pipe(action)

	# Assert
	assert goblin_state["tired"] is True


@patch("example_game.random.randint")
def test_mining_pipe_ore_amounts(mock_randint: Any, reset_goblin_state: None) -> None:
	"""Test that mining_pipe correctly handles different ore amounts."""
	# Test with each possible ore value
	for expected_ore in [1, 2, 3]:
		# Arrange
		mock_randint.return_value = expected_ore
		goblin_state["ore"] = 0
		action = Action(name="mine", actor="goblin_1")

		# Act
		outcome = mining_pipe(action)

		# Assert
		assert outcome.details["ore_gained"] == expected_ore
		assert goblin_state["ore"] == expected_ore
		assert f"mined {expected_ore} ore" in outcome.notes.lower()


def test_mining_pipe_ignores_non_mining_actions(reset_goblin_state: None) -> None:
	"""Test that mining_pipe ignores actions other than mining."""
	# Arrange
	actions = [
		Action(name="rest", actor="goblin_1"),
		Action(name="dance", actor="goblin_1"),
		Action(name="walk", actor="goblin_1"),
	]

	# Act & Assert
	for action in actions:
		outcome = mining_pipe(action)
		assert outcome is None, f"mining_pipe should ignore {action.name}"


def test_mining_pipe_accumulates_ore(reset_goblin_state: None) -> None:
	"""Test that multiple mining actions accumulate ore."""
	# Arrange
	action = Action(name="mine", actor="goblin_1")
	goblin_state["ore"] = 10

	# Act
	outcome1 = mining_pipe(action)
	ore_after_first = goblin_state["ore"]
	goblin_state["tired"] = False  # Reset so we can mine again
	outcome2 = mining_pipe(action)

	# Assert
	assert (
		goblin_state["ore"]
		== 10 + outcome1.details["ore_gained"] + outcome2.details["ore_gained"]
	)
	assert goblin_state["ore"] > ore_after_first


# ============================================================================
# Rest Pipe Tests
# ============================================================================


def test_rest_pipe_clears_tiredness(reset_goblin_state: None) -> None:
	"""Test that rest_pipe clears the tired state."""
	# Arrange
	goblin_state["tired"] = True
	action = Action(name="rest", actor="goblin_1")

	# Act
	outcome = rest_pipe(action)

	# Assert
	assert outcome is not None
	assert outcome.status == "success"
	assert goblin_state["tired"] is False
	assert "refreshed" in outcome.notes.lower()


def test_rest_pipe_when_not_tired(reset_goblin_state: None) -> None:
	"""Test that rest_pipe works even when goblin is not tired."""
	# Arrange
	goblin_state["tired"] = False
	action = Action(name="rest", actor="goblin_1")

	# Act
	outcome = rest_pipe(action)

	# Assert
	assert outcome is not None
	assert outcome.status == "success"
	assert goblin_state["tired"] is False


def test_rest_pipe_ignores_non_rest_actions(reset_goblin_state: None) -> None:
	"""Test that rest_pipe ignores actions other than resting."""
	# Arrange
	actions = [
		Action(name="mine", actor="goblin_1"),
		Action(name="dance", actor="goblin_1"),
		Action(name="eat", actor="goblin_1"),
	]

	# Act & Assert
	for action in actions:
		outcome = rest_pipe(action)
		assert outcome is None, f"rest_pipe should ignore {action.name}"


def test_rest_pipe_does_not_affect_ore(reset_goblin_state: None) -> None:
	"""Test that resting does not change ore count."""
	# Arrange
	goblin_state["ore"] = 42
	action = Action(name="rest", actor="goblin_1")

	# Act
	rest_pipe(action)

	# Assert
	assert goblin_state["ore"] == 42


# ============================================================================
# Pipe Ordering and Integration Tests
# ============================================================================


def test_pipe_ordering_fatigue_before_mining(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that fatigue check happens before mining logic.

	This verifies that pipe ordering is correct: fatigue_pipe must be
	registered before mining_pipe to prevent tired goblins from mining.
	"""
	# Arrange
	goblin_state["tired"] = True
	action = Action(name="mine", actor="goblin_1")

	# Act
	outcome = game_engine.process(action)

	# Assert - fatigue_pipe should catch this before mining_pipe
	assert outcome.status == "failure"
	assert "too tired" in outcome.notes.lower()
	assert goblin_state["ore"] == 0  # No ore should be gained


def test_successful_mine_rest_mine_cycle(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test a complete mine-rest-mine cycle."""
	# Mine first time (should succeed)
	outcome1 = game_engine.process(Action(name="mine", actor="goblin_1"))
	assert outcome1.status == "success"
	assert goblin_state["tired"] is True
	ore_after_first_mine = goblin_state["ore"]

	# Try to mine again (should fail - tired)
	outcome2 = game_engine.process(Action(name="mine", actor="goblin_1"))
	assert outcome2.status == "failure"
	assert goblin_state["ore"] == ore_after_first_mine  # No new ore

	# Rest (should succeed and clear tiredness)
	outcome3 = game_engine.process(Action(name="rest", actor="goblin_1"))
	assert outcome3.status == "success"
	assert goblin_state["tired"] is False

	# Mine again (should succeed now)
	outcome4 = game_engine.process(Action(name="mine", actor="goblin_1"))
	assert outcome4.status == "success"
	assert goblin_state["ore"] > ore_after_first_mine


def test_unhandled_action(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that unrecognized actions result in unhandled status."""
	# Arrange
	action = Action(name="dance", actor="goblin_1")

	# Act
	outcome = game_engine.process(action)

	# Assert
	assert outcome.status == "unhandled"
	# State should not change
	assert goblin_state["ore"] == 0
	assert goblin_state["tired"] is False


# ============================================================================
# Ledger and History Tests
# ============================================================================


def test_ledger_records_all_actions(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that all actions are recorded in the ledger."""
	# Arrange
	actions = [
		Action(name="mine", actor="goblin_1"),
		Action(name="mine", actor="goblin_1"),  # Will fail (tired)
		Action(name="rest", actor="goblin_1"),
		Action(name="dance", actor="goblin_1"),  # Unhandled
	]

	# Act
	for action in actions:
		game_engine.process(action)

	# Assert
	ledger = list(game_engine.ledger())
	assert len(ledger) == 4

	# Verify each entry
	assert ledger[0].action.name == "mine"
	assert ledger[0].outcome.status == "success"

	assert ledger[1].action.name == "mine"
	assert ledger[1].outcome.status == "failure"

	assert ledger[2].action.name == "rest"
	assert ledger[2].outcome.status == "success"

	assert ledger[3].action.name == "dance"
	assert ledger[3].outcome.status == "unhandled"


def test_ledger_entries_have_timestamps(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that ledger entries include timestamps."""
	# Arrange & Act
	game_engine.process(Action(name="mine", actor="goblin_1"))

	# Assert
	ledger = list(game_engine.ledger())
	assert len(ledger) == 1
	assert ledger[0].recorded_at is not None
	assert hasattr(ledger[0].recorded_at, "isoformat")


def test_ledger_preserves_action_details(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that ledger preserves all action details."""
	# Arrange
	action = Action(name="mine", actor="goblin_1", payload={"location": "deep_cavern"})

	# Act
	game_engine.process(action)

	# Assert
	ledger = list(game_engine.ledger())
	assert ledger[0].action.name == "mine"
	assert ledger[0].action.actor == "goblin_1"
	assert ledger[0].action.payload == {"location": "deep_cavern"}


def test_ledger_includes_outcome_details(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that ledger includes outcome details like ore_gained."""
	# Arrange & Act
	game_engine.process(Action(name="mine", actor="goblin_1"))

	# Assert
	ledger = list(game_engine.ledger())
	assert "ore_gained" in ledger[0].outcome.details
	assert 1 <= ledger[0].outcome.details["ore_gained"] <= 3


# ============================================================================
# Edge Cases and Error Conditions
# ============================================================================


def test_empty_actor_name(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that pipes handle actions with None or empty actor."""
	# Arrange & Act
	outcome1 = game_engine.process(Action(name="mine", actor=None))

	# Reset tiredness so second mine can succeed
	goblin_state["tired"] = False
	outcome2 = game_engine.process(Action(name="mine", actor=""))

	# Assert - should still work
	assert outcome1.status == "success"
	assert outcome2.status == "success"


def test_action_with_payload(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that actions with payloads are handled correctly."""
	# Arrange
	action = Action(
		name="mine",
		actor="goblin_1",
		payload={"tool": "pickaxe", "depth": 100},
	)

	# Act
	outcome = game_engine.process(action)

	# Assert
	assert outcome.status == "success"
	# Payload is preserved but not used by pipes
	assert action.payload["tool"] == "pickaxe"


@pytest.mark.parametrize(
	"action_name",
	["Mine", "MINE", "mInE", "  mine  "],
)
def test_action_name_case_sensitivity(
	action_name: str, reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that action names are case-sensitive and trimming matters.

	This test documents that pipes do exact string matching on action names.
	"""
	# Arrange & Act
	outcome = game_engine.process(Action(name=action_name, actor="goblin_1"))

	# Assert - should be unhandled unless exact match "mine"
	if action_name == "mine":
		assert outcome.status == "success"
	else:
		assert outcome.status == "unhandled"


def test_multiple_sequential_rests(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that multiple rest actions work correctly."""
	# Arrange
	goblin_state["tired"] = True

	# Act - rest multiple times
	outcome1 = game_engine.process(Action(name="rest", actor="goblin_1"))
	outcome2 = game_engine.process(Action(name="rest", actor="goblin_1"))
	outcome3 = game_engine.process(Action(name="rest", actor="goblin_1"))

	# Assert - all should succeed
	assert outcome1.status == "success"
	assert outcome2.status == "success"
	assert outcome3.status == "success"
	assert goblin_state["tired"] is False


def test_ore_accumulation_across_many_mines(reset_goblin_state: None) -> None:
	"""Test that ore correctly accumulates over many mining operations."""
	# Arrange
	action = Action(name="mine", actor="goblin_1")
	total_expected = 0

	# Act - mine 10 times
	for _ in range(10):
		goblin_state["tired"] = False  # Reset tiredness each time
		outcome = mining_pipe(action)
		total_expected += outcome.details["ore_gained"]

	# Assert
	assert goblin_state["ore"] == total_expected
	assert 10 <= goblin_state["ore"] <= 30  # 10 mines * (1-3 ore)


# ============================================================================
# State Management Tests
# ============================================================================


def test_state_isolation_between_actions(
	reset_goblin_state: None, game_engine: PipeworkEngine
) -> None:
	"""Test that state changes from one action affect subsequent actions."""
	# This test verifies that the global state is shared correctly
	# Arrange & Act
	game_engine.process(Action(name="mine", actor="goblin_1"))
	assert goblin_state["tired"] is True

	# This mine should fail because previous one made goblin tired
	outcome = game_engine.process(Action(name="mine", actor="goblin_2"))

	# Assert
	assert outcome.status == "failure"


def test_state_persists_across_engine_operations(reset_goblin_state: None) -> None:
	"""Test that goblin_state persists across multiple engine instances.

	This documents that goblin_state is global, not engine-scoped.
	"""
	# Arrange
	engine1 = PipeworkEngine()
	engine1.register_pipe(mining_pipe)

	engine2 = PipeworkEngine()
	engine2.register_pipe(mining_pipe)

	# Act
	engine1.process(Action(name="mine", actor="goblin_1"))
	initial_ore = goblin_state["ore"]

	goblin_state["tired"] = False  # Allow second mine
	engine2.process(Action(name="mine", actor="goblin_1"))

	# Assert - ore accumulates across both engines
	assert goblin_state["ore"] > initial_ore
