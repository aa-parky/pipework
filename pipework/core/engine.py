"""
Pipework Engine

The engine is responsible for:
- accepting actions
- passing them through rules (pipes)
- producing outcomes
- ensuring outcomes are recorded

The engine does not care about story, UI, or intent.
Only about what was attempted and what happened.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, Any, List


# ---- Core Data Structures ----

@dataclass
class Action:
	"""Something that is attempted."""
	name: str
	payload: Dict[str, Any] = field(default_factory=dict)
	actor: str | None = None


@dataclass
class Outcome:
	"""What actually happened."""
	status: str
	details: Dict[str, Any] = field(default_factory=dict)
	notes: str | None = None
	timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LedgerEntry:
	"""Authoritative record of an event."""
	action: Action
	outcome: Outcome
	recorded_at: datetime = field(default_factory=datetime.utcnow)


# ---- Engine ----

class PipeworkEngine:
	"""
	The Pipework engine.

	Actions enter here.
	Outcomes leave here.
	Everything is recorded.
	"""

	def __init__(self):
		self._pipes: List[Callable[[Action], Outcome]] = []
		self._ledger: List[LedgerEntry] = []

	# ---- Public API ----

	def register_pipe(self, pipe: Callable[[Action], Outcome]) -> None:
		"""
		Register a pipe (rule, transformer, or handler).

		Pipes are evaluated in order.
		The first pipe to return an Outcome ends the flow.
		"""
		self._pipes.append(pipe)

	def process(self, action: Action) -> Outcome:
		"""
		Process an action through the pipework.

		Guarantees:
		- an Outcome is always produced
		- the Outcome is always recorded
		"""
		try:
			outcome = self._run_pipes(action)
		except Exception as exc:
			# Failure is data
			outcome = Outcome(
				status="error",
				details={"exception": type(exc).__name__},
				notes=str(exc),
			)

		self._record(action, outcome)
		return outcome

	def ledger(self) -> List[LedgerEntry]:
		"""Return the full ledger."""
		return list(self._ledger)

	# ---- Internal Mechanics ----

	def _run_pipes(self, action: Action) -> Outcome:
		for pipe in self._pipes:
			result = pipe(action)
			if isinstance(result, Outcome):
				return result

		# No pipe handled the action
		return Outcome(
			status="unhandled",
			details={"action": action.name},
			notes="No pipe accepted the action.",
		)

	def _record(self, action: Action, outcome: Outcome) -> None:
		entry = LedgerEntry(action=action, outcome=outcome)
		self._ledger.append(entry)