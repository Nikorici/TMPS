import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal

from ticketing.catalog import EventCatalog
from ticketing.channels import BoxOfficeChannel, OnlineChannel
from ticketing.event_builder import EventBuilder
from ticketing.models import Customer
from ticketing.notifications import EmailNotifier, ReceiptPrinter, SmsNotifier
from ticketing.payments import CardPayment, CashPayment, PaymentGateway
from ticketing.pricing import PriceCalculator
from ticketing.receipts import ReceiptFormatter
from ticketing.repository import InMemoryOrderRepository
from ticketing.service import BookingService, SoldOut

BUYER = Customer("Buyer", "buyer@example.com", "+1")
ORDERED_ON = date(2026, 11, 1)


def summit(capacity=100):
    return EventBuilder().named("Summit").on(date(2026, 12, 5)).priced_at("450.00").with_capacity(capacity).build()


class CountingGateway(PaymentGateway):
    def __init__(self):
        self.charges = 0

    def charge(self, customer, amount):
        self.charges += 1
        return f"TEST-{self.charges}"


class BuilderTests(unittest.TestCase):
    def test_every_step_reaches_the_event(self):
        event = (
            EventBuilder()
            .named("Summit")
            .on(date(2026, 12, 5))
            .at("Arena")
            .priced_at("450.00")
            .with_capacity(300)
            .build()
        )
        self.assertEqual(
            (event.name, event.date, event.venue, event.base_price, event.capacity),
            ("Summit", date(2026, 12, 5), "Arena", Decimal("450.00"), 300),
        )

    def test_optional_steps_have_defaults(self):
        event = EventBuilder().named("Summit").on(date(2026, 12, 5)).priced_at("450.00").build()
        self.assertEqual((event.venue, event.capacity), ("To be announced", 100))

    def test_missing_required_steps_are_named(self):
        with self.assertRaisesRegex(ValueError, "missing: date, price"):
            EventBuilder().named("Summit").build()

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            summit(capacity=0)
        with self.assertRaises(ValueError):
            EventBuilder().named("Summit").on(date(2026, 12, 5)).priced_at("-1").build()


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.template = summit()
        self.catalog = EventCatalog()
        self.catalog.register("summit", self.template)

    def test_edition_copies_the_template_and_applies_changes(self):
        edition = self.catalog.edition("summit", venue="Bălți", capacity=8)
        self.assertIsNot(edition, self.template)
        self.assertEqual((edition.name, edition.date, edition.base_price), ("Summit", date(2026, 12, 5), Decimal("450.00")))
        self.assertEqual((edition.venue, edition.capacity), ("Bălți", 8))

    def test_template_is_left_unchanged(self):
        self.catalog.edition("summit", venue="Bălți", capacity=8)
        self.assertEqual((self.template.venue, self.template.capacity), ("To be announced", 100))

    def test_clones_are_validated_too(self):
        with self.assertRaises(ValueError):
            self.catalog.edition("summit", capacity=0)

    def test_unknown_template_fails(self):
        with self.assertRaises(KeyError):
            self.catalog.edition("concert")


class AbstractFactoryTests(unittest.TestCase):
    def test_online_family(self):
        channel = OnlineChannel()
        self.assertIsInstance(channel.create_payment(), CardPayment)
        self.assertEqual([type(n) for n in channel.create_notifiers()], [EmailNotifier, SmsNotifier])

    def test_box_office_family(self):
        channel = BoxOfficeChannel()
        self.assertIsInstance(channel.create_payment(), CashPayment)
        self.assertEqual([type(n) for n in channel.create_notifiers()], [ReceiptPrinter])

    def test_same_service_runs_on_either_family(self):
        for channel, reference, output in (
            (OnlineChannel(), "CARD-0001", "[email -> buyer@example.com]"),
            (BoxOfficeChannel(), "CASH-0001", "[printer -> Buyer]"),
        ):
            service = BookingService(
                PriceCalculator([]),
                channel.create_payment(),
                InMemoryOrderRepository(),
                channel.create_notifiers(),
                ReceiptFormatter(),
            )
            printed = io.StringIO()
            with redirect_stdout(printed):
                order = service.book(summit(), BUYER, 1, ORDERED_ON)
            self.assertEqual(order.payment_reference, reference)
            self.assertIn(output, printed.getvalue())


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.gateway = CountingGateway()
        self.repository = InMemoryOrderRepository()
        self.service = BookingService(PriceCalculator([]), self.gateway, self.repository, [], ReceiptFormatter())
        self.event = summit(capacity=3)

    def test_last_seats_can_be_sold(self):
        self.service.book(self.event, BUYER, 2, ORDERED_ON)
        self.service.book(self.event, BUYER, 1, ORDERED_ON)
        self.assertEqual(self.repository.tickets_sold(self.event), 3)

    def test_sold_out_is_refused_before_payment(self):
        self.service.book(self.event, BUYER, 2, ORDERED_ON)
        with self.assertRaisesRegex(SoldOut, "1 seats left, 2 requested"):
            self.service.book(self.event, BUYER, 2, ORDERED_ON)
        self.assertEqual(self.gateway.charges, 1)
        self.assertEqual(self.repository.tickets_sold(self.event), 2)

    def test_each_edition_has_its_own_seats(self):
        self.service.book(self.event, BUYER, 3, ORDERED_ON)
        self.assertEqual(self.repository.tickets_sold(self.event.clone(venue="Bălți")), 0)


if __name__ == "__main__":
    unittest.main()
