import unittest
from datetime import date
from decimal import Decimal

from ticketing.models import Customer, Event, TicketOrder
from ticketing.notifications import Notifier
from ticketing.payments import PaymentDeclined, PaymentGateway, WalletPayment
from ticketing.pricing import (
    DiscountPolicy,
    EarlyBirdDiscount,
    GroupDiscount,
    PriceCalculator,
    StudentDiscount,
    ZERO,
)
from ticketing.receipts import ReceiptFormatter
from ticketing.repository import InMemoryOrderRepository
from ticketing.service import BookingService

EVENT = Event("Test Conf", date(2026, 12, 1), Decimal("100.00"))
REGULAR = Customer("Regular", "r@example.com", "+1")
STUDENT = Customer("Student", "s@example.com", "+2", is_student=True)
EARLY = date(2026, 10, 1)
LATE = date(2026, 11, 25)


def order(customer=REGULAR, quantity=1, ordered_on=LATE):
    return TicketOrder(EVENT, customer, quantity, ordered_on)


class SingleResponsibilityTests(unittest.TestCase):
    def test_order_validates_its_own_data(self):
        with self.assertRaises(ValueError):
            order(quantity=0)
        with self.assertRaises(ValueError):
            order(ordered_on=date(2026, 12, 2))

    def test_repository_only_stores_and_assigns_ids(self):
        repository = InMemoryOrderRepository()
        saved = repository.save(order())
        self.assertEqual(saved.id, 1)
        self.assertIs(repository.find(1), saved)
        self.assertIsNone(repository.find(99))

    def test_receipt_formatter_only_builds_text(self):
        placed = order(STUDENT, 2, EARLY)
        placed.id, placed.payment_reference = 7, "REF-1"
        quote = PriceCalculator([EarlyBirdDiscount(), StudentDiscount()]).quote(placed)
        text = ReceiptFormatter().format(placed, quote)
        self.assertIn("Order #7", text)
        self.assertIn("Early bird discount: -40.00 MDL", text)
        self.assertIn("Student discount: -30.00 MDL", text)
        self.assertIn("Total paid: 140.00 MDL", text)
        self.assertIn("REF-1", text)


class OpenClosedTests(unittest.TestCase):
    def test_each_policy_applies_only_to_its_case(self):
        subtotal = Decimal("100.00")
        self.assertEqual(EarlyBirdDiscount().discount(order(ordered_on=EARLY), subtotal), Decimal("20.00"))
        self.assertEqual(EarlyBirdDiscount().discount(order(ordered_on=LATE), subtotal), ZERO)
        self.assertEqual(StudentDiscount().discount(order(STUDENT), subtotal), Decimal("15.00"))
        self.assertEqual(StudentDiscount().discount(order(REGULAR), subtotal), ZERO)
        self.assertEqual(GroupDiscount().discount(order(quantity=5), subtotal), Decimal("10.00"))
        self.assertEqual(GroupDiscount().discount(order(quantity=4), subtotal), ZERO)

    def test_no_policies_means_full_price(self):
        quote = PriceCalculator([]).quote(order(quantity=3))
        self.assertEqual(quote.total, Decimal("300.00"))
        self.assertEqual(quote.discounts, [])

    def test_combined_discounts_are_capped(self):
        quote = PriceCalculator([EarlyBirdDiscount(), StudentDiscount(), GroupDiscount()]).quote(
            order(STUDENT, 5, EARLY)
        )
        self.assertEqual(quote.subtotal, Decimal("500.00"))
        self.assertEqual(quote.total, Decimal("350.00"))
        self.assertTrue(quote.capped)

    def test_new_policy_needs_no_change_to_calculator(self):
        class PromoCodeDiscount(DiscountPolicy):
            name = "Promo FAF"

            def discount(self, order, subtotal):
                return Decimal("25.00")

        quote = PriceCalculator([PromoCodeDiscount()]).quote(order(quantity=2))
        self.assertEqual(quote.discounts, [("Promo FAF", Decimal("25.00"))])
        self.assertEqual(quote.total, Decimal("175.00"))


class FixedGateway(PaymentGateway):
    def __init__(self):
        self.charged = []

    def charge(self, customer, amount):
        self.charged.append((customer, amount))
        return "FAKE-1"


class RecordingNotifier(Notifier):
    def __init__(self):
        self.messages = []

    def send(self, customer, message):
        self.messages.append((customer, message))


class DependencyInversionTests(unittest.TestCase):
    def build(self, gateway):
        self.repository = InMemoryOrderRepository()
        self.notifier = RecordingNotifier()
        return BookingService(
            PriceCalculator([StudentDiscount()]), gateway, self.repository, [self.notifier], ReceiptFormatter()
        )

    def test_service_works_with_any_gateway_and_notifier(self):
        gateway = FixedGateway()
        booked = self.build(gateway).book(EVENT, STUDENT, 2, LATE)
        self.assertEqual(gateway.charged, [(STUDENT, Decimal("170.00"))])
        self.assertEqual(booked.total, Decimal("170.00"))
        self.assertEqual(booked.payment_reference, "FAKE-1")
        self.assertIs(self.repository.find(booked.id), booked)
        self.assertEqual(len(self.notifier.messages), 1)
        self.assertIn("Total paid: 170.00 MDL", self.notifier.messages[0][1])

    def test_declined_payment_saves_and_sends_nothing(self):
        service = self.build(WalletPayment(Decimal("50.00")))
        with self.assertRaises(PaymentDeclined):
            service.book(EVENT, REGULAR, 1, LATE)
        self.assertEqual(self.repository.all(), [])
        self.assertEqual(self.notifier.messages, [])


if __name__ == "__main__":
    unittest.main()
