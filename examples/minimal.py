"""Minimal Pipework Example - Basic action processing demonstration.

This example demonstrates the fundamental workflow of the Pipework engine:
1. Creating a PipeworkEngine instance
2. Defining and registering a pipe function
3. Creating an Action
4. Processing the action through the engine
5. Examining the resulting Outcome
6. Reviewing the ledger history

This is the simplest possible Pipework application. It shows a bureaucratic
world where goblins file reports that get accepted by the records department.

Usage:
    $ python examples/minimal.py
    Action: file_report
    Outcome: accepted
    Ledger entries: 1

To extend this example:
    - Add more pipe functions for different action types
    - Add validation or permission checking pipes
    - Add payload processing logic
    - Add error handling for invalid actions
    - Query and analyze the ledger after processing multiple actions
"""

from pipework.core import Action, Outcome, PipeworkEngine


def accept_reports(action: Action) -> Outcome | None:
	"""Process report filing actions.

	This is a simple pipe that handles the "file_report" action type.
	It accepts any report filing request and marks it as accepted by
	the records department.

	Args:
		action: The action to potentially handle. This pipe only processes
			actions with name="file_report". All other actions are passed
			to the next pipe by returning None.

	Returns:
		An Outcome with status="accepted" if the action is a report filing,
		or None to pass the action to the next pipe in the chain.

	Example:
		>>> action = Action(name="file_report", payload={"form": "PW-12"})
		>>> result = accept_reports(action)
		>>> print(result.status)  # "accepted"
		>>>
		>>> # Different action type - returns None
		>>> action = Action(name="mine_ore")
		>>> result = accept_reports(action)
		>>> print(result)  # None

	Note:
		In a real system, this pipe might:
		- Validate the payload contains required form data
		- Check that the actor has permission to file reports
		- Assign a tracking number to the report
		- Queue the report for processing
		- Return failure outcomes for invalid reports
	"""
	# Check if this pipe handles this action type
	if action.name == "file_report":
		# This pipe handles report filing - return an outcome
		return Outcome(
			status="accepted",
			details={"department": "records"},
			notes="Filed with minor annotations.",
		)

	# This pipe doesn't handle other action types - pass to next pipe
	return None


def main() -> None:
	"""Demonstrate basic Pipework engine usage.

	Creates an engine, registers a pipe, processes an action, and displays
	the results. This is the minimal example of a working Pipework application.
	"""
	# Step 1: Create the engine
	# The engine manages pipes and maintains the ledger
	engine = PipeworkEngine()

	# Step 2: Register pipe(s) that will process actions
	# Pipes are evaluated in registration order
	engine.register_pipe(accept_reports)

	# Step 3: Create an action to process
	# Actions describe what is being attempted
	action = Action(
		name="file_report",  # What type of action
		actor="goblin_127",  # Who is doing it
		payload={"form": "PW-12"},  # Additional context data
	)

	# Step 4: Process the action through the engine
	# The engine will run the action through pipes and return an outcome
	outcome = engine.process(action)

	# Step 5: Examine the outcome
	# The outcome tells us what happened (not what was intended)
	print("Action:", action.name)
	print("Outcome:", outcome.status)
	print("Ledger entries:", len(engine.ledger()))

	# Step 6 (optional): Review the ledger for audit/narrative purposes
	# The ledger contains the full history of all processed actions
	for entry in engine.ledger():
		print("\nLedger Entry:")
		print(f"  Actor: {entry.action.actor}")
		print(f"  Action: {entry.action.name}")
		print(f"  Result: {entry.outcome.status}")
		print(f"  Notes: {entry.outcome.notes}")


if __name__ == "__main__":
	main()
