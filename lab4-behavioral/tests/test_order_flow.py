import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal

from tests.fixtures import RecordingNotifier
from ticketing.behavioral.command.order_commands import CheckInCommand, RefundCommand
from ticketing.behavioral.command.staff_console import StaffConsole
from ticketing.behavioral.observer.order_observers import CustomerUpdates, RefundLedger
from ticketing.behavioral.observer.order_status_feed import OrderStatusFeed
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import InvalidTransition
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.payments import CashPayment
from ticketing.services.pricing import PriceCalculator
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.proxy.protected_order_repository import ProtectedOrderRepository
from ticketing.structural.proxy.staff import Role, StaffMember

BUYER = Customer("Buyer", "buyer@example.com", "+1")


class OrderFlowTests(unittest.TestCase):
    def setUp(self):
        self.feed, self.ledger, self.notifier = OrderStatusFeed(), RefundLedger(), RecordingNotifier()
        self.feed.subscribe(self.ledger)
        self.feed.subscribe(CustomerUpdates(self.notifier))
        self.repository = InMemoryOrderRepository()
        self.orders = ProtectedOrderRepository(self.repository, StaffMember("Support", Role.SELLER))
        desk = BookingService(PriceCalculator([]), CashPayment(), self.orders, [], ReceiptFormatter(), self.feed)
        self.event = EventBuilder().named("Test Conf").on(date(2026, 12, 1)).at("Hall").priced_at("100.00").with_capacity(4).build()
        with redirect_stdout(io.StringIO()):
            self.order = desk.book(self.event, BUYER, 3, date(2026, 11, 25))

    def test_a_refund_command_changes_the_state_and_every_observer_hears_it(self):
        console = StaffConsole("Support")
        console.run(RefundCommand(self.orders.find(self.order.id)))

        self.assertEqual(self.order.status, "refunded")
        self.assertEqual(self.ledger.total_refunded(), Decimal("300.00"))
        self.assertEqual(self.notifier.messages[-1][1], "Order #1 (Test Conf, Hall): paid -> refunded")
        self.assertEqual(self.orders.tickets_sold(self.event), 0)

        console.undo_last()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.ledger.total_refunded(), Decimal("0.00"))
        self.assertEqual(self.orders.tickets_sold(self.event), 3)

    def test_a_rejected_command_changes_nothing_and_notifies_nobody(self):
        console = StaffConsole("Door")
        self.order.refund()
        messages_before = len(self.notifier.messages)

        with self.assertRaises(InvalidTransition):
            console.run(CheckInCommand(self.order))

        self.assertEqual(self.order.status, "refunded")
        self.assertEqual(len(self.notifier.messages), messages_before)
        self.assertEqual(console.history(), [])


if __name__ == "__main__":
    unittest.main()
