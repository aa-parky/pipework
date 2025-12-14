# Pipework

![Python CI](https://github.com/aa-parky/pipework/workflows/Python%20CI/badge.svg)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

**Pipework** is a terminal-first narrative engine for moving actions through constrained systems and recording what leaks out the other end.

It was originally developed to support _The Undertaking_, a goblin-led interactive fiction world, but Pipework is intentionally world-agnostic. It is an engine for **flow, consequence, and record-keeping**, not a game framework and not a UI toolkit.

Pipework assumes that:

- intent rarely survives contact with reality
- failures are informative
- and if something happens, someone will write it down

---

## What Pipework Is

At its core, Pipework:

- accepts **actions**
- moves them through **rules and constraints**
- produces **outcomes**
- and records those outcomes in a **ledger**

Everything else — story, UI, images, lore, humour — is downstream.

Pipework does not care _why_ an action was taken.
It only cares **what was attempted**, **what happened**, and **where the record lives**.

---

## Design Principles

Pipework is deliberately opinionated.

- **Terminal-first**  
  If it doesn’t work in a terminal, it doesn’t belong in the core.

- **Deterministic by default**  
  Randomness is allowed, but never hidden.

- **All outcomes are recorded**  
  Success, failure, partial completion, or quiet disaster.

- **Failure is data**  
  Errors are not exceptions to be erased; they are events to be logged.

- **Tools before worlds**  
  Pipework builds machinery. Worlds are configurations.

---

## What Pipework Is Not

Pipework is _not_:

- a game engine
- a real-time simulation
- a heroic narrative framework
- a replacement for UI tools like ComfyUI
- a content generator by itself

Pipework does not provide:

- quests
- characters
- art styles
- chat interfaces
- or opinions about genre

Those belong elsewhere.

---

## Architecture (High Level)

Pipework is structured around a small number of core concepts:

- **Actions**  
  Things that are attempted.

- **Pipes**  
  Paths actions travel through (rules, transformations, adapters).

- **Outcomes**  
  What actually happened.

- **Ledger**  
  The authoritative record of events.

If something breaks, the pipe must still record where it leaked.

---

## Installation

Install Pipework from source:

```bash
git clone https://github.com/aa-parky/pipework.git
cd pipework
pip install -e .
```

For development (includes testing and linting tools):

```bash
pip install -e ".[dev]"
```

---

## Running the Examples

Pipework includes example implementations that demonstrate how to use the engine. These examples are designed to run as **Python modules**, not standalone scripts.

### Quick Start

From the project root directory, run:

```bash
python -m examples.example_game
```

**Not** this:

```bash
cd examples
python example_game.py  # ❌ This may fail with import errors
```

### Why `python -m`?

Running examples as modules ensures that:

- **Python correctly resolves imports** from the `pipework` package, regardless of your current directory
- **Examples behave consistently** whether Pipework is installed system-wide or you're running from source
- **No path manipulation needed** — no `PYTHONPATH` hacks or relative import workarounds

This is a standard Python practice for projects structured as packages. The `-m` flag tells Python to run the code as a module within the package namespace, which handles all import resolution automatically.

### What You'll See

Running `example_game.py` demonstrates:

- **Action processing** through registered pipes
- **Pipe ordering** (fatigue checks before mining)
- **State management** (goblin tiredness and ore collection)
- **Outcome recording** in the ledger
- **Unhandled actions** (when no pipe accepts an action)

The example implements a simple mining game where a goblin can mine ore, become tired, rest, and attempt silly actions like dancing.

---

## Intended Use

Pipework is suitable for:

- interactive fiction engines
- narrative simulations
- profession-based or systems-driven games
- governance-heavy or paperwork-driven worlds
- experimental storytelling tools

Pipework is especially useful where:

- consequences are delayed
- outcomes are indirect
- and stories emerge _after the fact_

---

## License

Pipework is released under the **GNU General Public License v3 (GPL-3.0)**.

You are free to use, modify, and redistribute Pipework under the terms of the GPL.
If you build worlds, tools, or engines on top of Pipework, they should remain inspectable in the same spirit.

---

## Provenance

Pipework draws inspiration from maintenance engineers, civil servants, record clerks, and one goblin pipeline engineer who observed:

> _“Nothing truly breaks — it merely ends up somewhere inconvenient.”_
