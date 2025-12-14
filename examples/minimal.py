from pipework.core import PipeworkEngine, Action, Outcome


def accept_reports(action: Action) -> Outcome | None:
	if action.name == "file_report":
		return Outcome(
			status="accepted",
			details={"department": "records"},
			notes="Filed with minor annotations.",
		)


def main():
	engine = PipeworkEngine()
	engine.register_pipe(accept_reports)

	action = Action(
		name="file_report",
		actor="goblin_127",
		payload={"form": "PW-12"},
	)

	outcome = engine.process(action)

	print("Action:", action.name)
	print("Outcome:", outcome.status)
	print("Ledger entries:", len(engine.ledger()))


if __name__ == "__main__":
	main()