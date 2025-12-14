"""Example game demonstrating Pipework engine usage.

This module implements a simple mining game where a goblin can mine ore and rest.
It demonstrates core Pipework concepts:
- Actions: Things attempted (mine, rest, dance)
- Pipes: Rules that process actions (fatigue checks, mining logic, rest logic)
- Outcomes: What actually happened (success, failure, unhandled)
- Ledger: Complete record of all game events

The game showcases pipe ordering, state management, and outcome recording.
"""

import random
from typing import TypeAlias

from pipework.core import Action, Outcome, PipeworkEngine

# -------------------------
# World state (VERY simple)
# -------------------------

# Type alias for clearer code
GoblinState: TypeAlias = dict[str, int | bool]

goblin_state: GoblinState = {
	"ore": 0,
	"tired": False,
}

# -------------------------
# Pipes (the rules)
# -------------------------


def fatigue_pipe(action: Action) -> Outcome | None:
	"""Prevent tired goblins from mining.

	This pipe enforces the fatigue mechanic by blocking mining actions when
	the goblin is tired. It demonstrates conditional failure outcomes.

	Pipe ordering matters: This MUST come before mining_pipe to check fatigue
	before allowing mining.

	Args:
		action: The action being attempted by the actor.

	Returns:
		Outcome with status="failure" if goblin is tired and trying to mine,
		None otherwise to pass control to next pipe.

	Example:
		>>> action = Action(name="mine", actor="goblin_1")
		>>> goblin_state["tired"] = True
		>>> outcome = fatigue_pipe(action)
		>>> outcome.status
		'failure'
	"""
	if action.name == "mine" and goblin_state["tired"]:
		return Outcome(status="failure", notes="The goblin is too tired to mine.")
	return None


def mining_pipe(action: Action) -> Outcome | None:
	"""Process mining actions and update game state.

	This pipe handles mining by:
	1. Generating random ore (1-3 units)
	2. Adding ore to goblin's inventory
	3. Setting goblin to tired state
	4. Recording outcome with ore gained

	Args:
		action: The action being attempted by the actor.

	Returns:
		Outcome with status="success" and ore details if action is "mine",
		None otherwise to pass control to next pipe.

	Note:
		This pipe mutates global goblin_state. In production code, consider
		passing state explicitly or using a state management pattern.

	Example:
		>>> action = Action(name="mine", actor="goblin_1")
		>>> goblin_state["tired"] = False
		>>> outcome = mining_pipe(action)
		>>> outcome.status
		'success'
		>>> goblin_state["tired"]
		True
	"""
	if action.name != "mine":
		return None

	# Generate random ore yield (1-3 units)
	gained = random.randint(1, 3)

	# Update game state
	goblin_state["ore"] += gained
	goblin_state["tired"] = True

	return Outcome(
		status="success",
		details={"ore_gained": gained},
		notes=f"The goblin mined {gained} ore.",
	)


def rest_pipe(action: Action) -> Outcome | None:
	"""Process rest actions to recover from fatigue.

	This pipe handles resting by clearing the tired state, allowing the
	goblin to mine again.

	Args:
		action: The action being attempted by the actor.

	Returns:
		Outcome with status="success" if action is "rest",
		None otherwise to pass control to next pipe.

	Example:
		>>> action = Action(name="rest", actor="goblin_1")
		>>> goblin_state["tired"] = True
		>>> outcome = rest_pipe(action)
		>>> outcome.status
		'success'
		>>> goblin_state["tired"]
		False
	"""
	if action.name != "rest":
		return None

	# Clear fatigue state
	goblin_state["tired"] = False

	return Outcome(status="success", notes="The goblin feels refreshed.")


# -------------------------
# Set up the engine
# -------------------------

# Create the engine instance that will process all actions
engine = PipeworkEngine()

# Register pipes in order - ORDER MATTERS!
# fatigue_pipe must come before mining_pipe to check tiredness first
engine.register_pipe(fatigue_pipe)  # Check if goblin is too tired
engine.register_pipe(mining_pipe)  # Handle mining actions
engine.register_pipe(rest_pipe)  # Handle rest actions
# Any unhandled action (like "dance") will get status="unhandled" automatically

# -------------------------
# Play the game
# -------------------------

# Define a sequence of actions to demonstrate the game mechanics:
# 1. mine -> success (goblin mines, becomes tired)
# 2. mine -> failure (goblin is tired, can't mine)
# 3. rest -> success (goblin rests, no longer tired)
# 4. mine -> success (goblin can mine again)
# 5. dance -> unhandled (no pipe handles this action)
actions = [
	Action(name="mine", actor="goblin_1"),  # Will succeed, goblin gets tired
	Action(name="mine", actor="goblin_1"),  # Will fail (too tired)
	Action(name="rest", actor="goblin_1"),  # Will succeed, clears tiredness
	Action(name="mine", actor="goblin_1"),  # Will succeed again
	Action(name="dance", actor="goblin_1"),  # Will be unhandled (no pipe for this)
]

# Process each action and display results
for action in actions:
	# Engine processes the action through all registered pipes
	outcome = engine.process(action)

	# Display what happened in a human-readable format
	print(f"> {action.actor} tries to {action.name}")
	print(f"  Result: {outcome.status}")
	if outcome.notes:
		print(f"  Notes: {outcome.notes}")
	print()

# -------------------------
# Review the ledger
# -------------------------

# The ledger contains a complete, immutable record of all events
# This is useful for debugging, analytics, or replay functionality
print("=== LEDGER ===")
for entry in engine.ledger():
	# Each entry contains the action, outcome, and timestamp
	print(
		f"{entry.recorded_at.isoformat()} | "
		f"{entry.action.actor} | "
		f"{entry.action.name} -> "
		f"{entry.outcome.status}"
	)

# Display final game state
print("\n=== FINAL STATE ===")
print(f"Total ore collected: {goblin_state['ore']}")
print(f"Goblin is tired: {goblin_state['tired']}")
