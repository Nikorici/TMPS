from decimal import Decimal

from ticketing.behavioral.observer.order_status_feed import OrderObserver
from ticketing.behavioral.state.order_states import CheckedInState, RefundedState
from ticketing.domain.models import Event
from ticketing.services.notifications import Notifier


class CustomerUpdates(OrderObserver):
    def __init__(self, notifier: Notifier):
        self._notifier = notifier

    def order_changed(self, order, old_state, new_state):
        message = f"Order #{order.id} ({order.event.name}, {order.event.venue}): {old_state.name} -> {new_state.name}"
        self._notifier.send(order.customer, message)


class RefundLedger(OrderObserver):
    def __init__(self):
        self._entries: list[tuple[int, Decimal]] = []

    def order_changed(self, order, old_state, new_state):
        if isinstance(new_state, RefundedState):
            self._entries.append((order.id, order.total))
        elif isinstance(old_state, RefundedState):
            self._entries.append((order.id, -order.total))

    def entries(self) -> list[tuple[int, Decimal]]:
        return list(self._entries)

    def total_refunded(self) -> Decimal:
        return sum((amount for _, amount in self._entries), Decimal("0.00"))


class AttendanceBoard(OrderObserver):
    def __init__(self):
        self._present: dict[Event, int] = {}

    def order_changed(self, order, old_state, new_state):
        if isinstance(new_state, CheckedInState):
            self._present[order.event] = self.present(order.event) + order.quantity
        elif isinstance(old_state, CheckedInState):
            self._present[order.event] = self.present(order.event) - order.quantity

    def present(self, event: Event) -> int:
        return self._present.get(event, 0)
