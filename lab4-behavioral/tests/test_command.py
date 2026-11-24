import unittest
from datetime import date
from decimal import Decimal

from ticketing.behavioral.command.order_commands import CheckInCommand, RefundCommand
from ticketing.behavioral.command.staff_console import StaffConsole
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import InvalidTransition
from ticketing.domain.models import Customer, TicketOrder

BUYER = Customer("Buyer", "buyer@example.com", "+1")


def paid_order(order_id):
    event = EventBuilder().named("Test Conf").on(date(2026, 12, 1)).priced_at("100.00").build()
    order = TicketOrder(event, BUYER, 2, date(2026, 11, 25), total=Decimal("200.00"), id=order_id)
    order.mark_paid()
    return order


class CommandTests(unittest.TestCase):
    def test_executing_and_undoing_a_command_restores_the_original_state(self):
        for command_class, executed_status in [(CheckInCommand, "checked in"), (RefundCommand, "refunded")]:
            order = paid_order(1)
            console = StaffConsole("Door")
            console.run(command_class(order))
            self.assertEqual(order.status, executed_status)
            console.undo_last()
            self.assertEqual(order.status, "paid")

    def test_history_keeps_only_executed_commands_and_undo_is_last_in_first_out(self):
        first, second = paid_order(1), paid_order(2)
        console = StaffConsole("Support")
        console.run(CheckInCommand(first))
        console.run(RefundCommand(second))
        with self.assertRaises(InvalidTransition):
            console.run(RefundCommand(first))

        self.assertEqual(console.history(), ["check in order #1", "refund order #2 (200.00 MDL)"])
        self.assertEqual(console.undo_last().description, "refund order #2 (200.00 MDL)")
        self.assertEqual((first.status, second.status), ("checked in", "paid"))
        self.assertEqual(console.history(), ["check in order #1"])

    def test_undo_with_an_empty_history_does_nothing(self):
        self.assertIsNone(StaffConsole("Door").undo_last())


if __name__ == "__main__":
    unittest.main()
