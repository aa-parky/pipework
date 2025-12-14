"""Pipework Engine - Core action processing and outcome recording system.

This module provides the fundamental machinery for Pipework's narrative engine.
It implements a deterministic, terminal-first system for processing actions through
registered pipes and recording all outcomes in an authoritative ledger.

The engine guarantees that:
    - Every action processed produces an outcome (success or failure)
    - Every outcome is recorded in the ledger with full context
    - Failures are treated as data, not exceptions to be hidden
    - Pipes are evaluated in registration order until one produces an outcome

The engine is deliberately agnostic about:
    - Story, narrative, or genre
    - User interface or visualization
    - Intent or motivation behind actions
    - World-specific rules or constraints (these belong in pipes)

Typical Usage:
    >>> from pipework.core import PipeworkEngine, Action, Outcome
    >>>
    >>> # Create engine and register a pipe
    >>> engine = PipeworkEngine()
    >>>
    >>> def handle_mining(action: Action) -> Outcome | None:
    ...     if action.name == "mine_ore":
    ...         return Outcome(status="success", details={"ore": 5})
    ...     return None
    >>>
    >>> engine.register_pipe(handle_mining)
    >>>
    >>> # Process action and examine outcome
    >>> action = Action(name="mine_ore", actor="dwarf_42")
    >>> outcome = engine.process(action)
    >>> print(outcome.status)  # "success"
    >>>
    >>> # Review the ledger
    >>> history = engine.ledger()
    >>> print(len(history))  # 1

Architecture:
    The engine uses a simple pipeline architecture where:
    1. Actions are submitted to process()
    2. Each registered pipe examines the action in order
    3. The first pipe to return an Outcome halts the pipeline
    4. If no pipe handles it, an "unhandled" outcome is created
    5. All outcomes (including errors) are recorded in the ledger

See Also:
    - examples/minimal.py: Simple working example of the engine
    - CLAUDE.md: Architectural overview and design principles
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---- Core Data Structures ----


@dataclass
class Action:
	"""Represents an attempted action in the Pipework system.

	An Action is an intent or command submitted to the engine for processing.
	It contains the minimum information needed to describe what is being attempted,
	who is attempting it, and any additional context required for pipes to evaluate it.

	Actions are immutable descriptions of intent - they do not contain logic or behavior.
	All logic for handling actions belongs in pipes, not in the Action itself.

	Attributes:
		name: Identifier for the type of action being attempted.
			Examples: "file_report", "mine_ore", "craft_sword", "negotiate_contract"
			Should be descriptive and unique within your domain.
		payload: Arbitrary data associated with the action. Can contain any
			context needed by pipes to process the action (e.g., item IDs,
			quantities, coordinates, form data). Defaults to empty dict.
		actor: Optional identifier for who/what initiated the action.
			Can be a user ID, NPC identifier, system process name, or None
			for anonymous/system actions. Defaults to None.

	Example:
		>>> # Simple action with minimal context
		>>> action = Action(name="ping")
		>>>
		>>> # Action with payload and actor
		>>> action = Action(
		...     name="transfer_funds",
		...     actor="merchant_42",
		...     payload={"amount": 100, "currency": "gold", "to": "bank_vault"}
		... )

	Note:
		Actions are processed through pipes in registration order. The action
		itself does not determine the outcome - pipes do. The same action can
		produce different outcomes based on which pipes are registered and
		in what order.
	"""

	name: str
	payload: dict[str, Any] = field(default_factory=dict)
	actor: str | None = None


@dataclass
class Outcome:
	"""Represents the result of processing an action.

	An Outcome describes what actually happened when an action was processed,
	as opposed to what was intended. Outcomes are produced by pipes and record
	the result of applying world rules, constraints, and transformations to actions.

	Every action processed by the engine produces exactly one outcome, whether
	successful, failed, partially completed, or unhandled. Failures are treated
	as valid outcomes, not exceptions - this is a core Pipework principle.

	Attributes:
		status: Classification of the outcome. Common values include:
			- "success": Action completed as intended
			- "failure": Action failed for a known reason
			- "partial": Action partially completed
			- "error": Unexpected exception occurred
			- "unhandled": No pipe accepted the action
			Custom status values are encouraged for domain-specific semantics.
		details: Arbitrary data about what happened. Can contain results,
			side effects, state changes, resource modifications, etc.
			Structure is determined by the pipe that produced the outcome.
			Defaults to empty dict.
		notes: Optional human-readable description of what happened.
			Useful for logs, debugging, or generating narrative text.
			Should describe the outcome, not repeat the status. Defaults to None.
		timestamp: When the outcome was created. Automatically set to UTC
			time when the Outcome is instantiated.

	Example:
		>>> # Simple success outcome
		>>> outcome = Outcome(status="success")
		>>>
		>>> # Detailed outcome with results and narrative
		>>> outcome = Outcome(
		...     status="partial",
		...     details={
		...         "requested": 10,
		...         "delivered": 7,
		...         "missing": ["copper", "iron", "zinc"]
		...     },
		...     notes="Shipment arrived incomplete due to weather delays."
		... )
		>>>
		>>> # Error outcome (created by engine on exception)
		>>> outcome = Outcome(
		...     status="error",
		...     details={"exception": "ValueError"},
		...     notes="Invalid quantity: cannot mine negative ore"
		... )

	Note:
		Outcomes are immutable records. They should not be modified after creation.
		The timestamp is set at instantiation and represents when the outcome was
		determined, not when the action was initiated or when it was recorded in
		the ledger.
	"""

	status: str
	details: dict[str, Any] = field(default_factory=dict)
	notes: str | None = None
	timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LedgerEntry:
	"""Authoritative record of an action and its outcome.

	A LedgerEntry is the permanent record of an event in the Pipework system.
	It binds together what was attempted (Action) with what actually happened
	(Outcome) and when it was recorded.

	The ledger is append-only and immutable. Entries are never modified or deleted
	once created. This provides an authoritative history of all events that have
	occurred, which can be used for:
		- Auditing and debugging
		- Narrative generation after the fact
		- State reconstruction
		- Analytics and pattern detection
		- Undo/replay mechanisms

	Attributes:
		action: The action that was attempted. Contains the intent, actor,
			and any payload data submitted for processing.
		outcome: The result of processing the action. Contains the status,
			details about what happened, and optional notes.
		recorded_at: When this entry was added to the ledger. Automatically
			set to UTC time when the LedgerEntry is instantiated. Note that
			this may differ slightly from outcome.timestamp due to processing
			delays.

	Example:
		>>> action = Action(name="file_report", actor="clerk_5")
		>>> outcome = Outcome(status="accepted", details={"queue": "pending"})
		>>> entry = LedgerEntry(action=action, outcome=outcome)
		>>>
		>>> # Typical usage: entries are created automatically by the engine
		>>> engine = PipeworkEngine()
		>>> engine.process(action)
		>>> ledger = engine.ledger()
		>>> print(ledger[-1].action.name)  # "file_report"

	Note:
		LedgerEntry instances are created automatically by the engine during
		action processing. Users should not need to create them manually.
		The ledger can be accessed via PipeworkEngine.ledger() to review
		the full history of processed actions.
	"""

	action: Action
	outcome: Outcome
	recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---- Engine ----


class PipeworkEngine:
	"""Core engine for processing actions and recording outcomes.

	The PipeworkEngine is the central component of the Pipework system. It manages
	the flow of actions through registered pipes, ensures outcomes are always
	produced, and maintains an authoritative ledger of all events.

	The engine implements a simple but powerful pipeline architecture:
		1. Actions are submitted via process()
		2. Each registered pipe is called in order
		3. The first pipe to return an Outcome stops the pipeline
		4. If no pipe handles the action, an "unhandled" outcome is created
		5. The action and outcome are recorded in the ledger
		6. The outcome is returned to the caller

	Key Guarantees:
		- Every call to process() returns an Outcome (never None, never raises)
		- Every Outcome is recorded in the ledger before being returned
		- Exceptions in pipes are caught and converted to error outcomes
		- The ledger is append-only and preserves full event history

	Attributes:
		_pipes: Ordered list of pipe functions that process actions.
			Pipes are evaluated in registration order.
		_ledger: Chronological list of all action/outcome pairs that have
			been processed by this engine instance.

	Example:
		>>> # Create engine and register pipes
		>>> engine = PipeworkEngine()
		>>>
		>>> def handle_mining(action: Action) -> Outcome | None:
		...     if action.name == "mine":
		...         return Outcome(status="success", details={"ore": 3})
		...     return None  # Pass to next pipe
		>>>
		>>> def handle_smelting(action: Action) -> Outcome | None:
		...     if action.name == "smelt":
		...         return Outcome(status="success", details={"ingot": 1})
		...     return None
		>>>
		>>> engine.register_pipe(handle_mining)
		>>> engine.register_pipe(handle_smelting)
		>>>
		>>> # Process actions
		>>> result = engine.process(Action(name="mine", actor="dwarf"))
		>>> print(result.status)  # "success"
		>>> print(result.details["ore"])  # 3
		>>>
		>>> # Unhandled action
		>>> result = engine.process(Action(name="unknown"))
		>>> print(result.status)  # "unhandled"
		>>>
		>>> # Review history
		>>> print(len(engine.ledger()))  # 2

	Note:
		The engine is stateless except for the pipe registry and ledger.
		Pipes themselves should manage any world state or persistence they need.
		Multiple engines can coexist independently with separate ledgers.
	"""

	def __init__(self) -> None:
		"""Initialize a new PipeworkEngine with empty pipes and ledger."""
		self._pipes: list[Callable[[Action], Outcome | None]] = []
		self._ledger: list[LedgerEntry] = []

	# ---- Public API ----

	def register_pipe(self, pipe: Callable[[Action], Outcome | None]) -> None:
		"""Register a pipe function to process actions.

		Pipes are the core extensibility mechanism in Pipework. Each pipe is a
		function that examines an action and decides whether to handle it.

		Pipe Behavior:
			- Pipes are called in the order they were registered
			- Each pipe receives the original Action (not a copy)
			- If a pipe returns an Outcome, processing stops (short-circuit)
			- If a pipe returns None, the next pipe is tried
			- If all pipes return None, the engine creates an "unhandled" outcome

		A well-designed pipe should:
			1. Check if it handles the action (e.g., by action.name)
			2. Return an Outcome if it handles it
			3. Return None if it doesn't handle it (pass to next pipe)
			4. Not raise exceptions (return error Outcome instead)

		Args:
			pipe: A callable that takes an Action and returns either an Outcome
				(if it handled the action) or None (to pass to the next pipe).
				The pipe may examine action.name, action.payload, and action.actor
				to determine if it should handle the action.

		Example:
			>>> engine = PipeworkEngine()
			>>>
			>>> def validate_permissions(action: Action) -> Outcome | None:
			...     '''Reject actions from banned actors.'''
			...     if action.actor in ["banned_user_42"]:
			...         return Outcome(
			...             status="rejected",
			...             notes="Actor is banned"
			...         )
			...     return None  # Let other pipes handle it
			>>>
			>>> def handle_crafting(action: Action) -> Outcome | None:
			...     '''Handle crafting actions.'''
			...     if action.name == "craft":
			...         item = action.payload.get("item")
			...         return Outcome(
			...             status="success",
			...             details={"crafted": item}
			...         )
			...     return None
			>>>
			>>> # Validation runs first, then crafting
			>>> engine.register_pipe(validate_permissions)
			>>> engine.register_pipe(handle_crafting)

		Note:
			Pipe order matters! Pipes are evaluated in registration order, and
			the first pipe to return an Outcome stops the pipeline. Design your
			pipe ordering carefully - validation/auth pipes typically go first,
			followed by domain-specific handlers.
		"""
		self._pipes.append(pipe)

	def process(self, action: Action) -> Outcome:
		"""Process an action through registered pipes and record the outcome.

		This is the primary entry point for the Pipework engine. It takes an action,
		runs it through the registered pipes, handles any exceptions, records the
		result in the ledger, and returns the outcome.

		Processing Flow:
			1. Run the action through pipes in registration order
			2. Stop at the first pipe that returns an Outcome
			3. If no pipe handles it, create an "unhandled" outcome
			4. If any pipe raises an exception, create an "error" outcome
			5. Record the action and outcome in the ledger
			6. Return the outcome to the caller

		Guarantees:
			- An Outcome is ALWAYS returned (never None, never raises)
			- The Outcome is ALWAYS recorded in the ledger before returning
			- Exceptions are caught and converted to error outcomes
			- The ledger entry is created before the outcome is returned

		Args:
			action: The action to process. The action is passed to each pipe
				until one returns an outcome.

		Returns:
			The outcome produced by a pipe, or a system-generated outcome if
			no pipe handled the action or if an exception occurred. Possible
			system outcomes:
				- status="unhandled": No pipe returned an outcome
				- status="error": A pipe raised an exception

		Example:
			>>> engine = PipeworkEngine()
			>>>
			>>> def handle_ping(action: Action) -> Outcome | None:
			...     if action.name == "ping":
			...         return Outcome(status="success", notes="pong")
			...     return None
			>>>
			>>> engine.register_pipe(handle_ping)
			>>>
			>>> # Handled action
			>>> result = engine.process(Action(name="ping"))
			>>> print(result.status)  # "success"
			>>> print(result.notes)   # "pong"
			>>>
			>>> # Unhandled action
			>>> result = engine.process(Action(name="unknown"))
			>>> print(result.status)  # "unhandled"
			>>>
			>>> # Both are in the ledger
			>>> print(len(engine.ledger()))  # 2

		Note:
			This method is thread-safe for reading pipes, but concurrent calls
			may interleave ledger entries. If you need strict ordering, serialize
			calls to process() or use separate engine instances per thread.

			Pipes should not modify the action - treat it as immutable. If you
			need to transform an action, create a new one and process it separately.
		"""
		try:
			outcome = self._run_pipes(action)
		except Exception as exc:
			# Failure is data - convert exceptions to outcomes
			outcome = Outcome(
				status="error",
				details={"exception": type(exc).__name__},
				notes=str(exc),
			)

		# Record before returning to ensure ledger is updated even if caller crashes
		self._record(action, outcome)
		return outcome

	def ledger(self) -> list[LedgerEntry]:
		"""Return a copy of the full ledger history.

		The ledger contains all actions processed by this engine and their outcomes,
		in chronological order. This is the authoritative record of everything that
		has happened in this engine instance.

		Returns:
			A new list containing all ledger entries. The list is a copy, so
			modifying it won't affect the engine's internal ledger. However,
			the LedgerEntry objects themselves are shared references.

		Example:
			>>> engine = PipeworkEngine()
			>>> # ... register pipes and process actions ...
			>>>
			>>> # Get full history
			>>> history = engine.ledger()
			>>>
			>>> # Analyze outcomes
			>>> successes = [e for e in history if e.outcome.status == "success"]
			>>> print(f"{len(successes)} successful actions")
			>>>
			>>> # Find actions by a specific actor
			>>> clerk_actions = [e for e in history if e.action.actor == "clerk_5"]
			>>>
			>>> # Generate narrative from ledger
			>>> for entry in history:
			...     print(f"{entry.action.actor} tried to {entry.action.name}")
			...     print(f"Result: {entry.outcome.status}")

		Note:
			The ledger grows indefinitely. For long-running systems, consider
			periodically archiving old entries or implementing ledger rotation.
			The ledger is append-only - entries are never modified or deleted.
		"""
		return list(self._ledger)

	# ---- Internal Mechanics ----

	def _run_pipes(self, action: Action) -> Outcome:
		"""Run an action through registered pipes until one handles it.

		Iterates through pipes in registration order, calling each one with the action.
		Stops at the first pipe that returns an Outcome (short-circuit evaluation).
		If no pipe returns an Outcome, creates an "unhandled" outcome.

		Args:
			action: The action to process through pipes.

		Returns:
			The Outcome from the first pipe that handled the action, or an
			"unhandled" outcome if no pipe returned an Outcome.

		Note:
			This method may raise exceptions from pipes - the caller (process method)
			is responsible for catching and converting them to error outcomes.
		"""
		for pipe in self._pipes:
			result = pipe(action)
			# Only stop if pipe explicitly returned an Outcome
			# Pipes returning None indicate "I don't handle this, try next pipe"
			if isinstance(result, Outcome):
				return result

		# No pipe handled the action - create system outcome
		return Outcome(
			status="unhandled",
			details={"action": action.name},
			notes="No pipe accepted the action.",
		)

	def _record(self, action: Action, outcome: Outcome) -> None:
		"""Record an action and outcome in the ledger.

		Creates a LedgerEntry binding the action and outcome together and appends
		it to the ledger. The entry is timestamped with the current UTC time.

		Args:
			action: The action that was processed.
			outcome: The outcome that was produced.

		Note:
			This is an append-only operation. Entries are never modified or deleted
			once added to the ledger. The ledger is the authoritative history.
		"""
		entry = LedgerEntry(action=action, outcome=outcome)
		self._ledger.append(entry)
