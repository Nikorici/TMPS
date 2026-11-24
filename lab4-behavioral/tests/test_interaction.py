import io
import unittest
from contextlib import redirect_stdout
from datetime import date

from tests.fixtures import SENDER, read_emails, temp_outbox
from ticketing.creational.channels import OnlineChannel
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import PaymentDeclined
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.pricing import PriceCalculator
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.decorator.audit_log import AuditEntry, AuditLog
from ticketing.structural.proxy.protected_order_repository import ProtectedOrderRepository
from ticketing.structural.proxy.staff import Role, StaffMember

BUYER = Customer("Buyer", "buyer@example.com", "+1")


def conference(capacity=100):
    return EventBuilder().named("Test Conf").on(date(2026, 12, 1)).at("Hall").priced_at("100.00").with_capacity(capacity).build()


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryOrderRepository()
        self.audit_log = AuditLog()
        self.outbox = temp_outbox(self)
        channel = OnlineChannel(self.outbox, SENDER, self.audit_log)
        self.desk = BookingService(
            PriceCalculator([]),
            channel.create_payment(),
            ProtectedOrderRepository(self.repository, StaffMember("Online shop", Role.SELLER)),
            channel.create_notifiers(),
            ReceiptFormatter(),
        )

    def test_an_online_booking_goes_through_the_proxy_the_decorators_and_the_adapter(self):
        with redirect_stdout(io.StringIO()):
            placed = self.desk.book(conference(), BUYER, 2, date(2026, 11, 25))

        self.assertEqual(self.repository.all(), [placed])
        self.assertEqual(self.audit_log.entries(), [AuditEntry("CARD-0001", "Buyer", placed.total)])
        self.assertEqual(len(read_emails(self.outbox)), 1)

    def test_an_over_limit_booking_stops_in_the_decorator(self):
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(PaymentDeclined):
                self.desk.book(conference(200), BUYER, 150, date(2026, 11, 25))

        self.assertEqual(self.repository.all(), [])
        self.assertEqual(self.audit_log.entries(), [])
        self.assertEqual(read_emails(self.outbox), [])


if __name__ == "__main__":
    unittest.main()
