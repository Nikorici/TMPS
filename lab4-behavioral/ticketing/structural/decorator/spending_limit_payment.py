from decimal import Decimal

from ticketing.domain.errors import PaymentDeclined
from ticketing.domain.models import Customer
from ticketing.services.payments import PaymentGateway
from ticketing.structural.decorator.payment_decorator import PaymentDecorator


class SpendingLimitPayment(PaymentDecorator):
    def __init__(self, wrapped: PaymentGateway, limit: Decimal):
        super().__init__(wrapped)
        self._limit = limit

    def charge(self, customer: Customer, amount: Decimal) -> str:
        if amount > self._limit:
            raise PaymentDeclined(f"card payments are limited to {self._limit} MDL per order, got {amount} MDL")
        return super().charge(customer, amount)
