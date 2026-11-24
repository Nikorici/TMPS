from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ticketing.behavioral.state.order_states import OrderState
    from ticketing.domain.models import TicketOrder


class OrderObserver(ABC):
    @abstractmethod
    def order_changed(self, order: TicketOrder, old_state: OrderState, new_state: OrderState) -> None: ...


class OrderStatusFeed:
    def __init__(self):
        self._observers: list[OrderObserver] = []

    def subscribe(self, observer: OrderObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: OrderObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, order: TicketOrder, old_state: OrderState, new_state: OrderState) -> None:
        for observer in list(self._observers):
            observer.order_changed(order, old_state, new_state)
