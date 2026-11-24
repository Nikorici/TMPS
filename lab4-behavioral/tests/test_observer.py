import unittest
from datetime import date
from decimal import Decimal

from tests.fixtures import RecordingNotifier
from ticketing.behavioral.observer.order_observers import AttendanceBoard, CustomerUpdates, RefundLedger
from ticketing.behavioral.observer.order_status_feed import OrderObserver, OrderStatusFeed
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.models import Customer, TicketOrder

BUYER = Customer("Buyer", "buyer@example.com", "+1")


class RecordingObserver(OrderObserver):
    def __init__(self):
        self.changes = []

    def order_changed(self, order, old_state, new_state):
        self.changes.append((order.id, old_state.name, new_state.name))


def followed_order(feed, quantity=2, total="200.00"):
    event = EventBuilder().named("Test Conf").on(date(2026, 12, 1)).at("Hall").priced_at("100.00").build()
    order = TicketOrder(event, BUYER, quantity, date(2026, 11, 25), total=Decimal(total), id=1)
    order.mark_paid()
    order.status_feed = feed
    return order


class ObserverTests(unittest.TestCase):
    def test_all_subscribed_observers_are_notified_and_unsubscribed_ones_are_not(self):
        feed = OrderStatusFeed()
        first, second = RecordingObserver(), RecordingObserver()
        feed.subscribe(first)
        feed.subscribe(second)
        order = followed_order(feed)

        order.check_in()
        feed.unsubscribe(second)
        order.undo_check_in()

        self.assertEqual(first.changes, [(1, "paid", "checked in"), (1, "checked in", "paid")])
        self.assertEqual(second.changes, [(1, "paid", "checked in")])

    def test_customer_updates_send_each_change_through_the_notifier(self):
        feed, notifier = OrderStatusFeed(), RecordingNotifier()
        feed.subscribe(CustomerUpdates(notifier))
        order = followed_order(feed)

        order.refund()

        [(customer, message)] = notifier.messages
        self.assertEqual(customer, BUYER)
        self.assertEqual(message, "Order #1 (Test Conf, Hall): paid -> refunded")

    def test_ledger_and_attendance_board_track_their_own_changes(self):
        feed, ledger, board = OrderStatusFeed(), RefundLedger(), AttendanceBoard()
        feed.subscribe(ledger)
        feed.subscribe(board)
        order = followed_order(feed, quantity=3)

        order.check_in()
        self.assertEqual(board.present(order.event), 3)
        order.undo_check_in()
        order.refund()
        order.reinstate()

        self.assertEqual(board.present(order.event), 0)
        self.assertEqual(ledger.entries(), [(1, Decimal("200.00")), (1, Decimal("-200.00"))])
        self.assertEqual(ledger.total_refunded(), Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
