import unittest
from datetime import date

from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import InvalidTransition
from ticketing.domain.models import Customer, TicketOrder
from ticketing.services.repository import InMemoryOrderRepository

BUYER = Customer("Buyer", "buyer@example.com", "+1")


def paid_order(quantity=2, event=None):
    event = event or EventBuilder().named("Test Conf").on(date(2026, 12, 1)).priced_at("100.00").build()
    order = TicketOrder(event, BUYER, quantity, date(2026, 11, 25))
    order.mark_paid()
    return order


class StateTests(unittest.TestCase):
    def test_valid_transitions_follow_the_lifecycle(self):
        order = TicketOrder(paid_order().event, BUYER, 1, date(2026, 11, 25))
        self.assertEqual(order.status, "pending payment")
        steps = [
            (order.mark_paid, "paid"),
            (order.check_in, "checked in"),
            (order.undo_check_in, "paid"),
            (order.refund, "refunded"),
            (order.reinstate, "paid"),
        ]
        for move, expected in steps:
            move()
            self.assertEqual(order.status, expected)

    def test_forbidden_transitions_are_rejected_and_leave_the_state_unchanged(self):
        pending = TicketOrder(paid_order().event, BUYER, 1, date(2026, 11, 25))
        checked_in = paid_order()
        checked_in.check_in()
        refunded = paid_order()
        refunded.refund()

        for order, move, status in [
            (pending, pending.check_in, "pending payment"),
            (checked_in, checked_in.check_in, "checked in"),
            (checked_in, checked_in.refund, "checked in"),
            (refunded, refunded.check_in, "refunded"),
        ]:
            with self.assertRaises(InvalidTransition):
                move()
            self.assertEqual(order.status, status)

    def test_a_refunded_order_releases_its_seats(self):
        repository = InMemoryOrderRepository()
        kept = paid_order(quantity=2)
        refunded = paid_order(quantity=3, event=kept.event)
        repository.save(kept)
        repository.save(refunded)
        self.assertEqual(repository.tickets_sold(kept.event), 5)

        refunded.refund()
        self.assertEqual(repository.tickets_sold(kept.event), 2)


if __name__ == "__main__":
    unittest.main()
