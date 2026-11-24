from decimal import Decimal

from ticketing.domain.models import Customer
from ticketing.services.payments import PaymentGateway


class PaymentDecorator(PaymentGateway):
    def __init__(self, wrapped: PaymentGateway):
        self._wrapped = wrapped

    def charge(self, customer: Customer, amount: Decimal) -> str:
        return self._wrapped.charge(customer, amount)
