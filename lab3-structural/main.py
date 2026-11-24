import mailbox
from datetime import date
from decimal import Decimal
from pathlib import Path

from ticketing.creational.catalog import EventCatalog
from ticketing.creational.channels import BoxOfficeChannel, OnlineChannel, SalesChannel
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import PaymentDeclined, SoldOut
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.pricing import EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.decorator.audit_log import AuditLog


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
    audit_log = AuditLog()

    def open_desk(channel: SalesChannel) -> BookingService:
        return BookingService(calculator, channel.create_payment(), repository, channel.create_notifiers(), receipts)

    outbox = mailbox.Maildir(Path(__file__).parent / "outbox")
    online = open_desk(OnlineChannel(outbox, "Moldova Tech Summit <tickets@techsummit.example>", audit_log))
    box_office = open_desk(BoxOfficeChannel(audit_log))

    student = Customer("Ana Rusu", "ana.rusu@example.com", "+37360000001", is_student=True)
    team_lead = Customer("Ion Ceban", "ion.ceban@example.com", "+37360000002")
    company = Customer("Mihai Popa", "mihai.popa@example.com", "+37360000004")
    late_buyer = Customer("Maria Lungu", "maria.lungu@example.com", "+37360000003")

    print("=== Online: early-bird student, 2 tickets, Chișinău ===")
    online.book(summit, student, 2, date(2026, 10, 27))

    print("=== Box office: group of 6, Bălți edition ===")
    box_office.book(balti, team_lead, 6, date(2027, 3, 1))

    print("=== Online: 30 tickets, over the 10,000 MDL online card limit ===")
    try:
        online.book(summit, company, 30, date(2026, 11, 20))
    except PaymentDeclined as declined:
        print(f"Payment declined: {declined}\n")

    print("=== Online: 3 more tickets for Bălți (8 seats) ===")
    try:
        online.book(balti, late_buyer, 3, date(2027, 3, 2))
    except SoldOut as sold_out:
        print(f"Sold out: {sold_out}\n")

    for event in (summit, balti):
        print(f"{event.venue}: {repository.tickets_sold(event)}/{event.capacity} seats sold")

    print("\n=== Payment audit log ===")
    for entry in audit_log.entries():
        print(f"{entry.reference}  {entry.amount:>9} MDL  {entry.customer}")


if __name__ == "__main__":
    main()
