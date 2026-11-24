import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from unittest import mock

from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.notifications import Notifier
from ticketing.services.payments import CardPayment
from ticketing.services.pricing import PriceCalculator
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.adapter.mailbox_email_notifier import MailboxEmailNotifier
from tests.fixtures import SENDER, read_emails, temp_outbox

BUYER = Customer("Buyer", "buyer@example.com", "+1")


class AdapterTests(unittest.TestCase):
    def test_translates_customer_and_receipt_into_an_email(self):
        outbox = temp_outbox(self)
        with redirect_stdout(io.StringIO()):
            MailboxEmailNotifier(outbox, SENDER).send(BUYER, "Order #7 confirmed\n  Total paid: 100.00 MDL")

        [email] = read_emails(outbox)
        self.assertEqual(email["From"], SENDER)
        self.assertEqual(email["To"], "Buyer <buyer@example.com>")
        self.assertEqual(email["Subject"], "Order #7 confirmed")
        self.assertEqual(email.get_content().rstrip("\n"), "Order #7 confirmed\n  Total paid: 100.00 MDL")

    def test_works_wherever_a_notifier_is_expected(self):
        outbox = temp_outbox(self)
        notifiers: list[Notifier] = [MailboxEmailNotifier(outbox, SENDER)]
        service = BookingService(PriceCalculator([]), CardPayment(), InMemoryOrderRepository(), notifiers, ReceiptFormatter())
        event = EventBuilder().named("Test Conf").on(date(2026, 12, 1)).at("Hall").priced_at("100.00").build()

        with redirect_stdout(io.StringIO()):
            service.book(event, BUYER, 2, date(2026, 11, 25))

        [email] = read_emails(outbox)
        self.assertTrue(email["Subject"].startswith("Order #1 confirmed: 2 x Test Conf"))
        self.assertIn(f"Total paid: {Decimal('200.00')} MDL", email.get_content())

    def test_passes_library_failures_back_to_the_caller(self):
        outbox = temp_outbox(self)
        with mock.patch.object(outbox, "add", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                MailboxEmailNotifier(outbox, SENDER).send(BUYER, "Order #1")
        self.assertEqual(read_emails(outbox), [])


if __name__ == "__main__":
    unittest.main()
