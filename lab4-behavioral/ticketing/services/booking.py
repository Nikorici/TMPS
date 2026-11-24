from datetime import date

from ticketing.domain.errors import SoldOut
from ticketing.domain.models import Customer, Event, TicketOrder
from ticketing.services.notifications import Notifier
from ticketing.services.payments import PaymentGateway
from ticketing.services.pricing import PriceCalculator
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import OrderRepository


class BookingService:
    def __init__(
        self,
        calculator: PriceCalculator,
        payments: PaymentGateway,
        repository: OrderRepository,
        notifiers: list[Notifier],
        receipts: ReceiptFormatter,
    ):
        self._calculator = calculator
        self._payments = payments
        self._repository = repository
        self._notifiers = notifiers
        self._receipts = receipts

    def book(self, event: Event, customer: Customer, quantity: int, ordered_on: date) -> TicketOrder:
        order = TicketOrder(event, customer, quantity, ordered_on)
        seats_left = event.capacity - self._repository.tickets_sold(event)
        if quantity > seats_left:
            raise SoldOut(f"{event.name}, {event.venue}: {seats_left} seats left, {quantity} requested")
        quote = self._calculator.quote(order)
        order.payment_reference = self._payments.charge(customer, quote.total)
        order.total = quote.total
        order.mark_paid()
        saved = self._repository.save(order)
        receipt = self._receipts.format(saved, quote)
        for notifier in self._notifiers:
            notifier.send(customer, receipt)
        return saved
