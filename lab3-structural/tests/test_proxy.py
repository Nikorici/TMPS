import unittest
from datetime import date
from unittest import mock

from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import AccessDenied
from ticketing.domain.models import Customer, TicketOrder
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.proxy.protected_order_repository import ProtectedOrderRepository
from ticketing.structural.proxy.staff import Role, StaffMember

BUYER = Customer("Buyer", "buyer@example.com", "+1")
CASHIER = StaffMember("Cashier", Role.SELLER)
ORGANIZER = StaffMember("Organizer", Role.ORGANIZER)


def conference():
    return EventBuilder().named("Test Conf").on(date(2026, 12, 1)).at("Hall").priced_at("100.00").build()


def order(event):
    return TicketOrder(event, BUYER, 3, date(2026, 11, 25))


class ProxyTests(unittest.TestCase):
    def test_passes_a_sellers_allowed_calls_through_unchanged(self):
        real = InMemoryOrderRepository()
        proxy = ProtectedOrderRepository(real, CASHIER)
        event = conference()
        placed = order(event)

        self.assertIs(proxy.save(placed), placed)
        self.assertIs(real.find(placed.id), placed)
        self.assertIs(proxy.find(placed.id), placed)
        self.assertEqual(proxy.tickets_sold(event), real.tickets_sold(event))

    def test_blocks_a_seller_from_exporting_customers_without_reaching_the_real_repository(self):
        real = InMemoryOrderRepository()
        proxy = ProtectedOrderRepository(real, CASHIER)
        with mock.patch.object(real, "all", wraps=real.all) as real_all:
            with self.assertRaises(AccessDenied):
                proxy.all()
        real_all.assert_not_called()

    def test_gives_an_organizer_exactly_what_the_real_repository_returns(self):
        real = InMemoryOrderRepository()
        real.save(order(conference()))
        self.assertEqual(ProtectedOrderRepository(real, ORGANIZER).all(), real.all())


if __name__ == "__main__":
    unittest.main()
