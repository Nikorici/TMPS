from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from ticketing.behavioral.state.order_states import OrderState, PendingPaymentState


@dataclass(frozen=True)
class Event:
    name: str
    date: date
    base_price: Decimal
    venue: str
    capacity: int

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("An event needs a name")
        if self.base_price < 0:
            raise ValueError("Ticket price cannot be negative")
        if self.capacity < 1:
            raise ValueError("An event needs at least one seat")

    def clone(self, **changes) -> "Event":
        return replace(self, **changes)


@dataclass(frozen=True)
class Customer:
    name: str
    email: str
    phone: str
    is_student: bool = False


@dataclass
class TicketOrder:
    event: Event
    customer: Customer
    quantity: int
    ordered_on: date
    total: Decimal = Decimal("0.00")
    payment_reference: str | None = None
    id: int | None = None
    state: OrderState = field(default_factory=PendingPaymentState, compare=False)

    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("An order needs at least one ticket")
        if self.ordered_on > self.event.date:
            raise ValueError("Tickets cannot be ordered after the event")

    @property
    def status(self) -> str:
        return self.state.name

    def mark_paid(self) -> None:
        self._move_to(self.state.mark_paid(self))

    def check_in(self) -> None:
        self._move_to(self.state.check_in(self))

    def undo_check_in(self) -> None:
        self._move_to(self.state.undo_check_in(self))

    def refund(self) -> None:
        self._move_to(self.state.refund(self))

    def reinstate(self) -> None:
        self._move_to(self.state.reinstate(self))

    def _move_to(self, new_state: OrderState) -> None:
        self.state = new_state
