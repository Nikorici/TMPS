import mailbox
from datetime import date
from decimal import Decimal
from pathlib import Path

from ticketing.creational.catalog import EventCatalog
from ticketing.creational.channels import BoxOfficeChannel, OnlineChannel, SalesChannel
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import AccessDenied, PaymentDeclined, SoldOut
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.pricing import EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount
from ticketing.services.receipts import ReceiptFormatter
from ticketing.services.repository import InMemoryOrderRepository
from ticketing.structural.decorator.audit_log import AuditLog
from ticketing.structural.proxy.protected_order_repository import ProtectedOrderRepository
from ticketing.structural.proxy.staff import Role, StaffMember


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

    online_shop = StaffMember("Online shop", Role.SELLER)
    cashier = StaffMember("Victor Rotaru", Role.SELLER)
    organizer = StaffMember("Elena Moraru", Role.ORGANIZER)

    def open_desk(channel: SalesChannel, staff: StaffMember) -> BookingService:
        orders = ProtectedOrderRepository(repository, staff)
        return BookingService(calculator, channel.create_payment(), orders, channel.create_notifiers(), receipts)

    outbox = mailbox.Maildir(Path(__file__).parent / "outbox")
    online = open_desk(OnlineChannel(outbox, "Moldova Tech Summit <tickets@techsummit.example>", audit_log), online_shop)
    box_office = open_desk(BoxOfficeChannel(audit_log), cashier)

    student = Customer("Ana Rusu", "ana.rusu@example.com", "+37360000001", is_student=True)
    team_lead = Customer("Ion Ceban", "ion.ceban@example.com", "+37360000002")
    company = Customer("Mihai Popa", "mihai.popa@example.com", "+37360000004")
    late_buyer = Customer("Maria Lungu", "maria.lungu@example.com", "+37360000003")

    print("=== 1. Online sale, early-bird student, 2 tickets  [Proxy -> Decorators -> Adapter] ===")
    online.book(summit, student, 2, date(2026, 10, 27))

    print("=== 2. Box office sale, group of 6, Bălți edition  [Prototype event, Proxy -> Decorator] ===")
    box_office.book(balti, team_lead, 6, date(2027, 3, 1))

    print("=== 3. Online sale, 30 tickets over the 10,000 MDL card limit  [SpendingLimitPayment decorator] ===")
    try:
        online.book(summit, company, 30, date(2026, 11, 20))
    except PaymentDeclined as declined:
        print(f"Payment declined: {declined}\n")

    print("=== 4. Online sale, 3 more tickets for Bălți (8 seats)  [seats counted through the Proxy] ===")
    try:
        online.book(balti, late_buyer, 3, date(2027, 3, 2))
    except SoldOut as sold_out:
        print(f"Sold out: {sold_out}\n")

    print("=== 5. Cashier tries to export the customer list  [Proxy blocks] ===")
    try:
        ProtectedOrderRepository(repository, cashier).all()
    except AccessDenied as denied:
        print(f"Access denied: {denied}\n")

    print("=== 6. Organizer report  [Proxy allows] ===")
    organizer_view = ProtectedOrderRepository(repository, organizer)
    for order in organizer_view.all():
        print(
            f"#{order.id}  {order.customer.name:<10}  {order.customer.email:<22}  "
            f"{order.quantity} x {order.event.venue:<23}  {order.total:>8} MDL"
        )
    for event in (summit, balti):
        print(f"{event.venue}: {organizer_view.tickets_sold(event)}/{event.capacity} seats sold")

    print("\n=== 7. Payment audit log  [AuditedPayment decorator] ===")
    for entry in audit_log.entries():
        print(f"{entry.reference}  {entry.amount:>9} MDL  {entry.customer}")


if __name__ == "__main__":
    main()
