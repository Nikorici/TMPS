from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ticketing.domain.errors import InvalidTransition

if TYPE_CHECKING:
    from ticketing.domain.models import TicketOrder


class OrderState(ABC):
    holds_seats = True

    @property
    @abstractmethod
    def name(self) -> str: ...

    def mark_paid(self, order: TicketOrder) -> OrderState:
        return self._refuse(order, "mark it as paid")

    def check_in(self, order: TicketOrder) -> OrderState:
        return self._refuse(order, "check it in")

    def undo_check_in(self, order: TicketOrder) -> OrderState:
        return self._refuse(order, "undo a check-in")

    def refund(self, order: TicketOrder) -> OrderState:
        return self._refuse(order, "refund it")

    def reinstate(self, order: TicketOrder) -> OrderState:
        return self._refuse(order, "reinstate it")

    def _refuse(self, order: TicketOrder, action: str) -> OrderState:
        raise InvalidTransition(f"Order #{order.id} is {self.name}: cannot {action}")


class PendingPaymentState(OrderState):
    name = "pending payment"

    def mark_paid(self, order):
        return PaidState()


class PaidState(OrderState):
    name = "paid"

    def check_in(self, order):
        return CheckedInState()

    def refund(self, order):
        return RefundedState()


class CheckedInState(OrderState):
    name = "checked in"

    def undo_check_in(self, order):
        return PaidState()


class RefundedState(OrderState):
    name = "refunded"
    holds_seats = False

    def reinstate(self, order):
        return PaidState()
