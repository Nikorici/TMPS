from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Event:
    name: str
    date: date
    base_price: Decimal


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

    def __post_init__(self):
        if self.quantity < 1:
            raise ValueError("An order needs at least one ticket")
        if self.ordered_on > self.event.date:
            raise ValueError("Tickets cannot be ordered after the event")
