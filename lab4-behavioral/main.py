import mailbox
from datetime import date
from decimal import Decimal
from pathlib import Path

from ticketing.behavioral.command.order_commands import CheckInCommand, RefundCommand
from ticketing.behavioral.command.staff_console import StaffConsole
from ticketing.behavioral.observer.order_observers import AttendanceBoard, CustomerUpdates, RefundLedger
from ticketing.behavioral.observer.order_status_feed import OrderStatusFeed
from ticketing.creational.catalog import EventCatalog
from ticketing.creational.channels import BoxOfficeChannel, OnlineChannel, SalesChannel
from ticketing.creational.event_builder import EventBuilder
from ticketing.domain.errors import AccessDenied, InvalidTransition, PaymentDeclined, SoldOut
from ticketing.domain.models import Customer
from ticketing.services.booking import BookingService
from ticketing.services.notifications import SmsNotifier
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
    status_feed = OrderStatusFeed()
    customer_updates, refund_ledger, attendance = CustomerUpdates(SmsNotifier()), RefundLedger(), AttendanceBoard()
    for observer in (customer_updates, refund_ledger, attendance):
        status_feed.subscribe(observer)

    online_shop = StaffMember("Online shop", Role.SELLER)
    cashier = StaffMember("Victor Rotaru", Role.SELLER)
    organizer = StaffMember("Elena Moraru", Role.ORGANIZER)

    def open_desk(channel: SalesChannel, staff: StaffMember) -> BookingService:
        orders = ProtectedOrderRepository(repository, staff)
        return BookingService(calculator, channel.create_payment(), orders, channel.create_notifiers(), receipts, status_feed)

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

    door, support = StaffConsole("Door scanner"), StaffConsole("Support desk")
    door_orders = ProtectedOrderRepository(repository, StaffMember("Door scanner", Role.SELLER))
    ana_order, ion_order = door_orders.find(1), door_orders.find(2)

    print("\n=== 8. Door scans Ana's ticket  [Command -> State -> Observers] ===")
    door.run(CheckInCommand(ana_order))
    print(f"Order #1 is now {ana_order.status}; present in {summit.venue}: {attendance.present(summit)}\n")

    print("=== 9. The same ticket is scanned again  [State rejects the transition] ===")
    try:
        door.run(CheckInCommand(ana_order))
    except InvalidTransition as rejected:
        print(f"Rejected: {rejected}\n")

    print("=== 10. It was the wrong ticket: undo  [Command undo -> State -> Observers] ===")
    undone = door.undo_last()
    print(f"Undone: {undone.description}; order #1 is {ana_order.status}; present: {attendance.present(summit)}\n")

    print("=== 11. Support refunds Ion's Bălți order  [Command -> State -> Observers] ===")
    support.run(RefundCommand(ion_order))
    print(f"Order #2 is now {ion_order.status}; Bălți seats sold: {door_orders.tickets_sold(balti)}/{balti.capacity}")
    print(f"Refund ledger total: {refund_ledger.total_refunded()} MDL\n")

    print("=== 12. Maria retries the Bălți purchase  [the refund freed the seats] ===")
    maria_order = online.book(balti, late_buyer, 3, date(2027, 3, 2))
    print(f"Order #{maria_order.id} is {maria_order.status}; Bălți seats sold: {door_orders.tickets_sold(balti)}/{balti.capacity}\n")

    print("=== 13. Organizer mutes customer SMS updates  [Observer unsubscribed at runtime] ===")
    status_feed.unsubscribe(customer_updates)
    door.run(CheckInCommand(ana_order))
    print(f"Ana checked in with no SMS; present in {summit.venue}: {attendance.present(summit)}\n")

    print("=== 14. Console history  [Command log] ===")
    for console in (door, support):
        print(f"{console.operator}: {console.history()}")


if __name__ == "__main__":
    main()
