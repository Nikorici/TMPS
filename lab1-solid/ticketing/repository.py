from abc import ABC, abstractmethod
from itertools import count

from ticketing.models import TicketOrder


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: TicketOrder) -> TicketOrder: ...

    @abstractmethod
    def find(self, order_id: int) -> TicketOrder | None: ...

    @abstractmethod
    def all(self) -> list[TicketOrder]: ...


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
