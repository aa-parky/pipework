"""Comprehensive tests for the Pipework engine.

This test suite covers all functionality of the core Pipework engine including:
- Data structure creation (Action, Outcome, LedgerEntry)
- Engine initialization and pipe registration
- Action processing through pipes
- Exception handling and error outcomes
- Ledger recording and history
- Pipe ordering and short-circuit evaluation
- Edge cases and boundary conditions
"""

from datetime import datetime, timezone

import pytest

from pipework.core import Action, Outcome, PipeworkEngine
from pipework.core.engine import LedgerEntry

# ---- Fixtures ----


@pytest.fixture
def engine() -> PipeworkEngine:
	"""Provide a fresh PipeworkEngine instance for each test.

	Returns:
		A new PipeworkEngine with no pipes registered and an empty ledger.
	"""
	return PipeworkEngine()


@pytest.fixture
def simple_action() -> Action:
	"""Provide a basic action for testing.

	Returns:
		An Action with name="test_action" and minimal context.
	"""
	return Action(name="test_action", actor="test_actor")


@pytest.fixture
def action_with_payload() -> Action:
	"""Provide an action with payload data.

	Returns:
		An Action containing payload data for testing pipe processing.
	"""
	return Action(
		name="complex_action",
		actor="test_actor",
		payload={"item_id": 42, "quantity": 5, "urgent": True},
	)


# ---- Tests: Data Structures ----


class TestAction:
	"""Test Action dataclass creation and attributes."""

	def test_create_minimal_action(self) -> None:
		"""Test creating an action with only required fields."""
		action = Action(name="ping")

		assert action.name == "ping"
		assert action.payload == {}
		assert action.actor is None

	def test_create_action_with_actor(self) -> None:
		"""Test creating an action with an actor."""
		action = Action(name="mine", actor="dwarf_42")

		assert action.name == "mine"
		assert action.actor == "dwarf_42"
		assert action.payload == {}

	def test_create_action_with_payload(self) -> None:
		"""Test creating an action with payload data."""
		payload = {"x": 10, "y": 20, "tool": "pickaxe"}
		action = Action(name="mine", actor="dwarf_42", payload=payload)

		assert action.name == "mine"
		assert action.actor == "dwarf_42"
		assert action.payload == payload
		assert action.payload["x"] == 10

	def test_action_payload_defaults_to_empty_dict(self) -> None:
		"""Test that payload defaults to an empty dict, not None."""
		action = Action(name="test")

		assert action.payload is not None
		assert action.payload == {}
		assert isinstance(action.payload, dict)


class TestOutcome:
	"""Test Outcome dataclass creation and attributes."""

	def test_create_minimal_outcome(self) -> None:
		"""Test creating an outcome with only status."""
		outcome = Outcome(status="success")

		assert outcome.status == "success"
		assert outcome.details == {}
		assert outcome.notes is None
		assert isinstance(outcome.timestamp, datetime)

	def test_create_outcome_with_details(self) -> None:
		"""Test creating an outcome with details dictionary."""
		details = {"ore_mined": 5, "durability_lost": 2}
		outcome = Outcome(status="success", details=details)

		assert outcome.status == "success"
		assert outcome.details == details
		assert outcome.details["ore_mined"] == 5

	def test_create_outcome_with_notes(self) -> None:
		"""Test creating an outcome with narrative notes."""
		outcome = Outcome(
			status="partial",
			notes="Mining interrupted by cave-in",
		)

		assert outcome.status == "partial"
		assert outcome.notes == "Mining interrupted by cave-in"

	def test_outcome_timestamp_is_set_automatically(self) -> None:
		"""Test that timestamp is automatically set to current UTC time."""
		before = datetime.now(timezone.utc)
		outcome = Outcome(status="success")
		after = datetime.now(timezone.utc)

		assert before <= outcome.timestamp <= after

	def test_outcome_details_defaults_to_empty_dict(self) -> None:
		"""Test that details defaults to an empty dict, not None."""
		outcome = Outcome(status="success")

		assert outcome.details is not None
		assert outcome.details == {}
		assert isinstance(outcome.details, dict)


class TestLedgerEntry:
	"""Test LedgerEntry dataclass creation and attributes."""

	def test_create_ledger_entry(self) -> None:
		"""Test creating a ledger entry with action and outcome."""
		action = Action(name="test", actor="actor_1")
		outcome = Outcome(status="success", details={"result": 42})

		entry = LedgerEntry(action=action, outcome=outcome)

		assert entry.action == action
		assert entry.outcome == outcome
		assert isinstance(entry.recorded_at, datetime)

	def test_ledger_entry_timestamp_is_automatic(self) -> None:
		"""Test that recorded_at is automatically set."""
		action = Action(name="test")
		outcome = Outcome(status="success")

		before = datetime.now(timezone.utc)
		entry = LedgerEntry(action=action, outcome=outcome)
		after = datetime.now(timezone.utc)

		assert before <= entry.recorded_at <= after


# ---- Tests: Engine Initialization ----


class TestEngineInitialization:
	"""Test PipeworkEngine initialization."""

	def test_engine_initializes_with_empty_pipes(self, engine: PipeworkEngine) -> None:
		"""Test that new engine has no registered pipes."""
		# Process an action - should get "unhandled" since no pipes
		action = Action(name="test")
		outcome = engine.process(action)

		assert outcome.status == "unhandled"

	def test_engine_initializes_with_empty_ledger(self, engine: PipeworkEngine) -> None:
		"""Test that new engine has an empty ledger."""
		ledger = engine.ledger()

		assert ledger == []
		assert len(ledger) == 0


# ---- Tests: Pipe Registration ----


class TestPipeRegistration:
	"""Test registering pipes with the engine."""

	def test_register_single_pipe(self, engine: PipeworkEngine) -> None:
		"""Test registering a single pipe function."""

		def test_pipe(action: Action) -> Outcome | None:
			if action.name == "handled":
				return Outcome(status="success")
			return None

		engine.register_pipe(test_pipe)

		# Test that pipe handles its action
		result = engine.process(Action(name="handled"))
		assert result.status == "success"

	def test_register_multiple_pipes(self, engine: PipeworkEngine) -> None:
		"""Test registering multiple pipes."""

		def pipe_1(action: Action) -> Outcome | None:
			if action.name == "action_1":
				return Outcome(status="handled_by_pipe_1")
			return None

		def pipe_2(action: Action) -> Outcome | None:
			if action.name == "action_2":
				return Outcome(status="handled_by_pipe_2")
			return None

		engine.register_pipe(pipe_1)
		engine.register_pipe(pipe_2)

		# Both pipes should work
		result_1 = engine.process(Action(name="action_1"))
		assert result_1.status == "handled_by_pipe_1"

		result_2 = engine.process(Action(name="action_2"))
		assert result_2.status == "handled_by_pipe_2"


# ---- Tests: Action Processing ----


class TestActionProcessing:
	"""Test processing actions through pipes."""

	def test_process_action_with_matching_pipe(self, engine: PipeworkEngine) -> None:
		"""Test processing an action that a pipe handles."""

		def accept_reports(action: Action) -> Outcome | None:
			if action.name == "file_report":
				return Outcome(
					status="accepted",
					details={"department": "records"},
					notes="Report filed successfully.",
				)
			return None

		engine.register_pipe(accept_reports)

		action = Action(name="file_report", actor="clerk_5")
		outcome = engine.process(action)

		assert outcome.status == "accepted"
		assert outcome.details["department"] == "records"
		assert outcome.notes == "Report filed successfully."

	def test_process_action_with_no_matching_pipe(self, engine: PipeworkEngine) -> None:
		"""Test processing an action when no pipe handles it."""

		def specific_pipe(action: Action) -> Outcome | None:
			if action.name == "specific_action":
				return Outcome(status="success")
			return None

		engine.register_pipe(specific_pipe)

		# Action that no pipe handles
		action = Action(name="unknown_action")
		outcome = engine.process(action)

		assert outcome.status == "unhandled"
		assert outcome.details["action"] == "unknown_action"
		assert "No pipe accepted" in outcome.notes

	def test_process_action_with_no_pipes_registered(
		self, engine: PipeworkEngine
	) -> None:
		"""Test processing an action when no pipes are registered."""
		action = Action(name="any_action")
		outcome = engine.process(action)

		assert outcome.status == "unhandled"
		assert outcome.details["action"] == "any_action"

	def test_pipe_can_access_action_payload(self, engine: PipeworkEngine) -> None:
		"""Test that pipes can access and process action payload."""

		def calculate_total(action: Action) -> Outcome | None:
			if action.name == "add":
				numbers = action.payload.get("numbers", [])
				total = sum(numbers)
				return Outcome(
					status="success",
					details={"total": total, "count": len(numbers)},
				)
			return None

		engine.register_pipe(calculate_total)

		action = Action(name="add", payload={"numbers": [1, 2, 3, 4, 5]})
		outcome = engine.process(action)

		assert outcome.status == "success"
		assert outcome.details["total"] == 15
		assert outcome.details["count"] == 5

	def test_pipe_can_access_action_actor(self, engine: PipeworkEngine) -> None:
		"""Test that pipes can access action.actor for authorization."""

		def check_permissions(action: Action) -> Outcome | None:
			if action.actor in ["banned_user_1", "banned_user_2"]:
				return Outcome(
					status="rejected",
					notes=f"Actor {action.actor} is banned",
				)
			return None

		engine.register_pipe(check_permissions)

		# Banned user
		action = Action(name="test", actor="banned_user_1")
		outcome = engine.process(action)
		assert outcome.status == "rejected"

		# Non-banned user (no pipe handles it after permission check)
		action = Action(name="test", actor="normal_user")
		outcome = engine.process(action)
		assert outcome.status == "unhandled"  # Permission check passed, but no handler


# ---- Tests: Pipe Ordering ----


class TestPipeOrdering:
	"""Test that pipes are evaluated in registration order."""

	def test_pipes_evaluated_in_order(self, engine: PipeworkEngine) -> None:
		"""Test that pipes are called in the order they were registered."""
		call_order: list[int] = []

		def pipe_1(action: Action) -> Outcome | None:
			call_order.append(1)
			return None

		def pipe_2(action: Action) -> Outcome | None:
			call_order.append(2)
			return None

		def pipe_3(action: Action) -> Outcome | None:
			call_order.append(3)
			return Outcome(status="handled_by_pipe_3")

		engine.register_pipe(pipe_1)
		engine.register_pipe(pipe_2)
		engine.register_pipe(pipe_3)

		engine.process(Action(name="test"))

		assert call_order == [1, 2, 3]

	def test_first_pipe_to_return_outcome_wins(self, engine: PipeworkEngine) -> None:
		"""Test that processing stops at first pipe that returns an Outcome."""

		def pipe_1(action: Action) -> Outcome | None:
			return None  # Pass to next pipe

		def pipe_2(action: Action) -> Outcome | None:
			return Outcome(status="handled_by_pipe_2")

		def pipe_3(action: Action) -> Outcome | None:
			# This should never be called
			return Outcome(status="handled_by_pipe_3")

		engine.register_pipe(pipe_1)
		engine.register_pipe(pipe_2)
		engine.register_pipe(pipe_3)

		outcome = engine.process(Action(name="test"))

		# pipe_2 handled it, pipe_3 never called
		assert outcome.status == "handled_by_pipe_2"

	def test_validation_pipe_before_handler_pipe(self, engine: PipeworkEngine) -> None:
		"""Test typical pattern: validation pipes before handler pipes."""

		def validate_actor(action: Action) -> Outcome | None:
			"""Validation pipe - runs first."""
			if action.actor is None:
				return Outcome(status="rejected", notes="Actor required")
			return None

		def handle_action(action: Action) -> Outcome | None:
			"""Handler pipe - runs second."""
			if action.name == "process":
				return Outcome(status="success")
			return None

		# Order matters: validation first, then handler
		engine.register_pipe(validate_actor)
		engine.register_pipe(handle_action)

		# Invalid: no actor
		outcome = engine.process(Action(name="process", actor=None))
		assert outcome.status == "rejected"

		# Valid: has actor
		outcome = engine.process(Action(name="process", actor="user_1"))
		assert outcome.status == "success"


# ---- Tests: Exception Handling ----


class TestExceptionHandling:
	"""Test that exceptions in pipes are caught and converted to error outcomes."""

	def test_exception_in_pipe_produces_error_outcome(
		self, engine: PipeworkEngine
	) -> None:
		"""Test that exceptions are caught and converted to error outcomes."""

		def buggy_pipe(action: Action) -> Outcome | None:
			if action.name == "crash":
				raise ValueError("Something went wrong!")
			return None

		engine.register_pipe(buggy_pipe)

		action = Action(name="crash")
		outcome = engine.process(action)

		assert outcome.status == "error"
		assert outcome.details["exception"] == "ValueError"
		assert "Something went wrong!" in outcome.notes

	def test_different_exception_types_are_captured(
		self, engine: PipeworkEngine
	) -> None:
		"""Test that different exception types are properly recorded."""

		def pipe_with_exceptions(action: Action) -> Outcome | None:
			if action.name == "value_error":
				raise ValueError("Bad value")
			elif action.name == "type_error":
				raise TypeError("Wrong type")
			elif action.name == "key_error":
				raise KeyError("Missing key")
			return None

		engine.register_pipe(pipe_with_exceptions)

		# Test ValueError
		outcome = engine.process(Action(name="value_error"))
		assert outcome.status == "error"
		assert outcome.details["exception"] == "ValueError"

		# Test TypeError
		outcome = engine.process(Action(name="type_error"))
		assert outcome.status == "error"
		assert outcome.details["exception"] == "TypeError"

		# Test KeyError
		outcome = engine.process(Action(name="key_error"))
		assert outcome.status == "error"
		assert outcome.details["exception"] == "KeyError"

	def test_exception_does_not_crash_engine(self, engine: PipeworkEngine) -> None:
		"""Test that exceptions don't prevent the engine from continuing."""

		def sometimes_crashes(action: Action) -> Outcome | None:
			if action.name == "crash":
				raise RuntimeError("Boom!")
			elif action.name == "success":
				return Outcome(status="success")
			return None

		engine.register_pipe(sometimes_crashes)

		# First action crashes
		outcome1 = engine.process(Action(name="crash"))
		assert outcome1.status == "error"

		# Engine still works for next action
		outcome2 = engine.process(Action(name="success"))
		assert outcome2.status == "success"

		# Both are in ledger
		assert len(engine.ledger()) == 2


# ---- Tests: Ledger Recording ----


class TestLedgerRecording:
	"""Test that all actions and outcomes are recorded in the ledger."""

	def test_successful_action_is_recorded(self, engine: PipeworkEngine) -> None:
		"""Test that successful outcomes are recorded in ledger."""

		def success_pipe(action: Action) -> Outcome | None:
			return Outcome(status="success")

		engine.register_pipe(success_pipe)

		action = Action(name="test", actor="user_1")
		_outcome = engine.process(action)

		ledger = engine.ledger()
		assert len(ledger) == 1
		assert ledger[0].action.name == "test"
		assert ledger[0].action.actor == "user_1"
		assert ledger[0].outcome.status == "success"

	def test_unhandled_action_is_recorded(self, engine: PipeworkEngine) -> None:
		"""Test that unhandled outcomes are recorded in ledger."""
		action = Action(name="unhandled")
		_outcome = engine.process(action)

		ledger = engine.ledger()
		assert len(ledger) == 1
		assert ledger[0].action.name == "unhandled"
		assert ledger[0].outcome.status == "unhandled"

	def test_error_action_is_recorded(self, engine: PipeworkEngine) -> None:
		"""Test that error outcomes are recorded in ledger."""

		def crash_pipe(action: Action) -> Outcome | None:
			raise RuntimeError("Test error")

		engine.register_pipe(crash_pipe)

		action = Action(name="test")
		_outcome = engine.process(action)

		ledger = engine.ledger()
		assert len(ledger) == 1
		assert ledger[0].action.name == "test"
		assert ledger[0].outcome.status == "error"

	def test_multiple_actions_create_multiple_entries(
		self, engine: PipeworkEngine
	) -> None:
		"""Test that each processed action creates a ledger entry."""

		def handler(action: Action) -> Outcome | None:
			return Outcome(status="handled")

		engine.register_pipe(handler)

		# Process multiple actions
		engine.process(Action(name="action_1"))
		engine.process(Action(name="action_2"))
		engine.process(Action(name="action_3"))

		ledger = engine.ledger()
		assert len(ledger) == 3
		assert ledger[0].action.name == "action_1"
		assert ledger[1].action.name == "action_2"
		assert ledger[2].action.name == "action_3"

	def test_ledger_preserves_chronological_order(self, engine: PipeworkEngine) -> None:
		"""Test that ledger entries maintain chronological order."""

		def handler(action: Action) -> Outcome | None:
			return Outcome(status="success")

		engine.register_pipe(handler)

		# Process actions in specific order
		actions = ["first", "second", "third", "fourth"]
		for name in actions:
			engine.process(Action(name=name))

		ledger = engine.ledger()
		recorded_names = [entry.action.name for entry in ledger]

		assert recorded_names == actions

	def test_ledger_returns_copy_not_reference(self, engine: PipeworkEngine) -> None:
		"""Test that ledger() returns a copy, not the internal list."""

		def handler(action: Action) -> Outcome | None:
			return Outcome(status="success")

		engine.register_pipe(handler)

		# Get ledger
		ledger1 = engine.ledger()

		# Process another action
		engine.process(Action(name="new_action"))

		# Get ledger again
		ledger2 = engine.ledger()

		# ledger1 should not have been modified (it's a copy)
		assert len(ledger1) == 0
		assert len(ledger2) == 1
		assert ledger1 is not ledger2


# ---- Tests: Edge Cases ----


class TestEdgeCases:
	"""Test edge cases and boundary conditions."""

	def test_action_with_empty_name(self, engine: PipeworkEngine) -> None:
		"""Test processing an action with an empty name."""

		def handler(action: Action) -> Outcome | None:
			if action.name == "":
				return Outcome(status="handled_empty_name")
			return None

		engine.register_pipe(handler)

		action = Action(name="")
		outcome = engine.process(action)

		assert outcome.status == "handled_empty_name"

	def test_action_with_very_large_payload(self, engine: PipeworkEngine) -> None:
		"""Test processing an action with a large payload."""

		def handler(action: Action) -> Outcome | None:
			count = len(action.payload.get("items", []))
			return Outcome(status="success", details={"count": count})

		engine.register_pipe(handler)

		# Large payload
		large_payload = {"items": list(range(10000))}
		action = Action(name="test", payload=large_payload)
		outcome = engine.process(action)

		assert outcome.status == "success"
		assert outcome.details["count"] == 10000

	def test_nested_data_in_payload(self, engine: PipeworkEngine) -> None:
		"""Test processing actions with deeply nested payload data."""

		def handler(action: Action) -> Outcome | None:
			value = action.payload.get("level1", {}).get("level2", {}).get("value")
			return Outcome(status="success", details={"extracted": value})

		engine.register_pipe(handler)

		nested_payload = {"level1": {"level2": {"value": 42}}}
		action = Action(name="test", payload=nested_payload)
		outcome = engine.process(action)

		assert outcome.status == "success"
		assert outcome.details["extracted"] == 42

	def test_pipe_returning_none_explicitly(self, engine: PipeworkEngine) -> None:
		"""Test that pipes returning None pass to the next pipe."""

		def always_none(action: Action) -> Outcome | None:
			return None

		def final_handler(action: Action) -> Outcome | None:
			return Outcome(status="handled_by_final")

		engine.register_pipe(always_none)
		engine.register_pipe(final_handler)

		outcome = engine.process(Action(name="test"))

		assert outcome.status == "handled_by_final"

	def test_outcome_with_none_in_details(self, engine: PipeworkEngine) -> None:
		"""Test that outcomes can have None values in details dict."""

		def handler(action: Action) -> Outcome | None:
			return Outcome(
				status="success",
				details={"result": None, "error": None, "data": 42},
			)

		engine.register_pipe(handler)

		outcome = engine.process(Action(name="test"))

		assert outcome.status == "success"
		assert outcome.details["result"] is None
		assert outcome.details["error"] is None
		assert outcome.details["data"] == 42


# ---- Tests: Integration Scenarios ----


class TestIntegrationScenarios:
	"""Test realistic multi-pipe scenarios."""

	def test_validation_transformation_handler_pipeline(
		self, engine: PipeworkEngine
	) -> None:
		"""Test a realistic pipeline with validation, transformation, and handling."""

		def validate(action: Action) -> Outcome | None:
			"""Validate action has required fields."""
			if action.name == "transfer":
				amount = action.payload.get("amount")
				if amount is None or amount <= 0:
					return Outcome(status="rejected", notes="Invalid amount")
			return None

		def transform(action: Action) -> Outcome | None:
			"""Transform/normalize data (in real system might modify payload)."""
			# In this test, just pass through
			return None

		def handle_transfer(action: Action) -> Outcome | None:
			"""Handle the actual transfer."""
			if action.name == "transfer":
				amount = action.payload.get("amount", 0)
				return Outcome(
					status="success",
					details={"transferred": amount},
					notes=f"Transferred {amount} units",
				)
			return None

		engine.register_pipe(validate)
		engine.register_pipe(transform)
		engine.register_pipe(handle_transfer)

		# Valid transfer
		valid_action = Action(
			name="transfer",
			actor="user_1",
			payload={"amount": 100},
		)
		outcome = engine.process(valid_action)
		assert outcome.status == "success"
		assert outcome.details["transferred"] == 100

		# Invalid transfer (caught by validation)
		invalid_action = Action(
			name="transfer",
			actor="user_1",
			payload={"amount": -50},
		)
		outcome = engine.process(invalid_action)
		assert outcome.status == "rejected"

	def test_multiple_specialized_handlers(self, engine: PipeworkEngine) -> None:
		"""Test engine with multiple domain-specific handlers."""

		def handle_mining(action: Action) -> Outcome | None:
			if action.name == "mine":
				return Outcome(status="success", details={"ore": 3})
			return None

		def handle_crafting(action: Action) -> Outcome | None:
			if action.name == "craft":
				item = action.payload.get("item", "unknown")
				return Outcome(status="success", details={"crafted": item})
			return None

		def handle_trading(action: Action) -> Outcome | None:
			if action.name == "trade":
				return Outcome(status="success", details={"gold": 100})
			return None

		engine.register_pipe(handle_mining)
		engine.register_pipe(handle_crafting)
		engine.register_pipe(handle_trading)

		# Test each handler
		mine_result = engine.process(Action(name="mine"))
		assert mine_result.status == "success"
		assert mine_result.details["ore"] == 3

		craft_result = engine.process(Action(name="craft", payload={"item": "sword"}))
		assert craft_result.status == "success"
		assert craft_result.details["crafted"] == "sword"

		trade_result = engine.process(Action(name="trade"))
		assert trade_result.status == "success"
		assert trade_result.details["gold"] == 100

		# All recorded
		assert len(engine.ledger()) == 3


# ---- Tests: Parametrized Tests ----


class TestParametrized:
	"""Parametrized tests for testing multiple cases efficiently."""

	@pytest.mark.parametrize(
		"status",
		["success", "failure", "partial", "pending", "rejected", "custom_status"],
	)
	def test_outcome_with_various_status_values(self, status: str) -> None:
		"""Test that outcomes can have any string status value."""
		outcome = Outcome(status=status)
		assert outcome.status == status

	@pytest.mark.parametrize(
		"actor",
		["user_1", "goblin_42", "system", "", None],
	)
	def test_action_with_various_actors(self, actor: str | None) -> None:
		"""Test that actions accept various actor values including None."""
		action = Action(name="test", actor=actor)
		assert action.actor == actor

	@pytest.mark.parametrize(
		"action_name,expected_status",
		[
			("handled_action", "success"),
			("unhandled_action", "unhandled"),
			("error_action", "error"),
		],
	)
	def test_different_action_types(
		self,
		engine: PipeworkEngine,
		action_name: str,
		expected_status: str,
	) -> None:
		"""Test processing different action types produces expected outcomes."""

		def test_pipe(action: Action) -> Outcome | None:
			if action.name == "handled_action":
				return Outcome(status="success")
			elif action.name == "error_action":
				raise ValueError("Intentional error")
			return None

		engine.register_pipe(test_pipe)

		outcome = engine.process(Action(name=action_name))
		assert outcome.status == expected_status
