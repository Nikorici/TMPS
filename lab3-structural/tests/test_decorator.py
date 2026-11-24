import unittest
from decimal import Decimal

from tests.fixtures import CountingGateway
from ticketing.domain.errors import PaymentDeclined
from ticketing.domain.models import Customer
from ticketing.structural.decorator.audit_log import AuditEntry, AuditLog
from ticketing.structural.decorator.audited_payment import AuditedPayment
from ticketing.structural.decorator.payment_decorator import PaymentDecorator
from ticketing.structural.decorator.spending_limit_payment import SpendingLimitPayment

BUYER = Customer("Buyer", "buyer@example.com", "+1")
LIMIT = Decimal("1000.00")


class DecoratorTests(unittest.TestCase):
    def test_audited_payment_records_the_charge_and_returns_the_reference_unchanged(self):
        log = AuditLog()
        reference = AuditedPayment(CountingGateway(), log).charge(BUYER, Decimal("250.00"))
        self.assertEqual(reference, "TEST-1")
        self.assertEqual(log.entries(), [AuditEntry("TEST-1", "Buyer", Decimal("250.00"))])

    def test_spending_limit_declines_over_limit_without_calling_the_wrapped_gateway(self):
        card = CountingGateway()
        limited = SpendingLimitPayment(card, LIMIT)
        with self.assertRaises(PaymentDeclined):
            limited.charge(BUYER, LIMIT + Decimal("0.01"))
        self.assertEqual(card.charges, 0)
        self.assertEqual(limited.charge(BUYER, LIMIT), "TEST-1")

    def test_decorators_stacked_in_either_order_give_the_same_result(self):
        stacks = [
            lambda card, log: SpendingLimitPayment(AuditedPayment(card, log), LIMIT),
            lambda card, log: AuditedPayment(SpendingLimitPayment(card, LIMIT), log),
        ]
        for stack in stacks:
            card, log = CountingGateway(), AuditLog()
            payment = stack(card, log)
            self.assertEqual(payment.charge(BUYER, Decimal("300.00")), "TEST-1")
            with self.assertRaises(PaymentDeclined):
                payment.charge(BUYER, Decimal("5000.00"))
            self.assertEqual(card.charges, 1)
            self.assertEqual([entry.reference for entry in log.entries()], ["TEST-1"])

    def test_a_new_decorator_is_a_new_class_only_and_stacks_with_the_existing_ones(self):
        class PrefixedReferencePayment(PaymentDecorator):
            def charge(self, customer, amount):
                return f"SUMMIT-{super().charge(customer, amount)}"

        log = AuditLog()
        payment = PrefixedReferencePayment(AuditedPayment(SpendingLimitPayment(CountingGateway(), LIMIT), log))
        self.assertEqual(payment.charge(BUYER, Decimal("100.00")), "SUMMIT-TEST-1")
        self.assertEqual(len(log.entries()), 1)


if __name__ == "__main__":
    unittest.main()
