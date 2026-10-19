from datetime import date
from decimal import Decimal

from ticketing.models import Customer, Event
from ticketing.notifications import EmailNotifier, SmsNotifier
from ticketing.payments import CardPayment, PaymentDeclined, WalletPayment
from ticketing.pricing import EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount
from ticketing.receipts import ReceiptFormatter
from ticketing.repository import InMemoryOrderRepository
from ticketing.service import BookingService


def main():
    summit = Event("Moldova Tech Summit", date(2026, 12, 5), Decimal("450.00"))
    calculator = PriceCalculator([EarlyBirdDiscount(), StudentDiscount(), GroupDiscount()])
    repository = InMemoryOrderRepository()
    receipts = ReceiptFormatter()

    card_desk = BookingService(calculator, CardPayment("4111111111111111"), repository, [EmailNotifier(), SmsNotifier()], receipts)
    wallet_desk = BookingService(calculator, WalletPayment(Decimal("500.00")), repository, [EmailNotifier()], receipts)

    student = Customer("Ana Rusu", "ana.rusu@example.com", "+37360000001", is_student=True)
    team_lead = Customer("Ion Ceban", "ion.ceban@example.com", "+37360000002")

    print("=== Early-bird student, 2 tickets, card ===")
    card_desk.book(summit, student, 2, date(2026, 10, 19))

    print("=== Late group order, 6 tickets, card ===")
    card_desk.book(summit, team_lead, 6, date(2026, 11, 28))

    print("=== Wallet order with insufficient balance ===")
    try:
        wallet_desk.book(summit, team_lead, 3, date(2026, 11, 28))
    except PaymentDeclined as declined:
        print(f"Payment declined: {declined}\n")

    print(f"Orders stored: {len(repository.all())}")


if __name__ == "__main__":
    main()
