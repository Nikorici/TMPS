from datetime import date
from decimal import Decimal

from ticketing.models import Event


class EventBuilder:
    def __init__(self):
        self._name = None
        self._date = None
        self._base_price = None
        self._venue = "To be announced"
        self._capacity = 100

    def named(self, name: str) -> "EventBuilder":
        self._name = name
        return self

    def on(self, day: date) -> "EventBuilder":
        self._date = day
        return self

    def priced_at(self, amount: str) -> "EventBuilder":
        self._base_price = Decimal(amount)
        return self

    def at(self, venue: str) -> "EventBuilder":
        self._venue = venue
        return self

    def with_capacity(self, seats: int) -> "EventBuilder":
        self._capacity = seats
        return self

    def build(self) -> Event:
        required = {"name": self._name, "date": self._date, "price": self._base_price}
        missing = [step for step, value in required.items() if value is None]
        if missing:
            raise ValueError(f"Event is missing: {', '.join(missing)}")
        return Event(self._name, self._date, self._base_price, self._venue, self._capacity)
