from datetime import date
from decimal import Decimal

from ticketing.catalog import EventCatalog
from ticketing.channels import BoxOfficeChannel, OnlineChannel, SalesChannel
from ticketing.event_builder import EventBuilder
from ticketing.models import Customer
from ticketing.pricing import EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount
from ticketing.receipts import ReceiptFormatter
from ticketing.repository import InMemoryOrderRepository
from ticketing.service import BookingService, SoldOut


def main():
    summit = (
        EventBuilder()
        .named("Moldova Tech Summit")
        .on(date(2026, 12, 5))
        .at("Chișinău Arena")
        .priced_at("450.00")
        .with_capacity(300)
        .build()
    )

    catalog = EventCatalog()
    catalog.register("tech-summit", summit)
    balti = catalog.edition(
        "tech-summit",
        date=date(2027, 3, 12),
        venue="Bălți Palace of Culture",
        base_price=Decimal("350.00"),
        capacity=8,
    )

    calculator = PriceCalculator([EarlyBirdDiscount(), StudentDiscount(), GroupDiscount()])
    repository = InMemoryOrderRepository()
    receipts = ReceiptFormatter()

    def open_desk(channel: SalesChannel) -> BookingService:
        return BookingService(calculator, channel.create_payment(), repository, channel.create_notifiers(), receipts)

    online = open_desk(OnlineChannel())
    box_office = open_desk(BoxOfficeChannel())

    student = Customer("Ana Rusu", "ana.rusu@example.com", "+37360000001", is_student=True)
    team_lead = Customer("Ion Ceban", "ion.ceban@example.com", "+37360000002")
    late_buyer = Customer("Maria Lungu", "maria.lungu@example.com", "+37360000003")

    print("=== Online: early-bird student, 2 tickets, Chișinău ===")
    online.book(summit, student, 2, date(2026, 10, 27))

    print("=== Box office: group of 6, Bălți edition ===")
    box_office.book(balti, team_lead, 6, date(2027, 3, 1))

    print("=== Online: 3 more tickets for Bălți (8 seats) ===")
    try:
        online.book(balti, late_buyer, 3, date(2027, 3, 2))
    except SoldOut as sold_out:
        print(f"Sold out: {sold_out}\n")

    for event in (summit, balti):
        print(f"{event.venue}: {repository.tickets_sold(event)}/{event.capacity} seats sold")


if __name__ == "__main__":
    main()
