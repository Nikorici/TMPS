from decimal import Decimal

from ticketing.domain.models import Customer
from ticketing.services.payments import PaymentGateway
from ticketing.structural.decorator.audit_log import AuditEntry, AuditLog
from ticketing.structural.decorator.payment_decorator import PaymentDecorator


class AuditedPayment(PaymentDecorator):
    def __init__(self, wrapped: PaymentGateway, log: AuditLog):
        super().__init__(wrapped)
        self._log = log

    def charge(self, customer: Customer, amount: Decimal) -> str:
        reference = super().charge(customer, amount)
        self._log.record(AuditEntry(reference, customer.name, amount))
        return reference
