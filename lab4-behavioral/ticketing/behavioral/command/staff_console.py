from ticketing.behavioral.command.order_commands import OrderCommand


class StaffConsole:
    def __init__(self, operator: str):
        self.operator = operator
        self._history: list[OrderCommand] = []

    def run(self, command: OrderCommand) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> OrderCommand | None:
        if not self._history:
            return None
        command = self._history[-1]
        command.undo()
        self._history.pop()
        return command

    def history(self) -> list[str]:
        return [command.description for command in self._history]
