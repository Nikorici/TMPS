from abc import ABC, abstractmethod

from ticketing.domain.models import TicketOrder


class OrderCommand(ABC):
    def __init__(self, order: TicketOrder):
        self._order = order

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


class CheckInCommand(OrderCommand):
    @property
    def description(self) -> str:
        return f"check in order #{self._order.id}"

    def execute(self) -> None:
        self._order.check_in()

    def undo(self) -> None:
        self._order.undo_check_in()


class RefundCommand(OrderCommand):
    @property
    def description(self) -> str:
        return f"refund order #{self._order.id} ({self._order.total} MDL)"

    def execute(self) -> None:
        self._order.refund()

    def undo(self) -> None:
        self._order.reinstate()
