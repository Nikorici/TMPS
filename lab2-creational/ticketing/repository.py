from abc import ABC, abstractmethod
from itertools import count

from ticketing.models import Event, TicketOrder


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: TicketOrder) -> TicketOrder: ...

    @abstractmethod
    def find(self, order_id: int) -> TicketOrder | None: ...

    @abstractmethod
    def all(self) -> list[TicketOrder]: ...

    @abstractmethod
    def tickets_sold(self, event: Event) -> int: ...


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: dict[int, TicketOrder] = {}
        self._ids = count(1)

    def save(self, order):
        if order.id is None:
            order.id = next(self._ids)
        self._orders[order.id] = order
        return order

    def find(self, order_id):
        return self._orders.get(order_id)

    def all(self):
        return list(self._orders.values())

    def tickets_sold(self, event):
        return sum(order.quantity for order in self._orders.values() if order.event == event)
