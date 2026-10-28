from abc import ABC, abstractmethod

from ticketing.notifications import EmailNotifier, Notifier, ReceiptPrinter, SmsNotifier
from ticketing.payments import CardPayment, CashPayment, PaymentGateway


class SalesChannel(ABC):
    @abstractmethod
    def create_payment(self) -> PaymentGateway: ...

    @abstractmethod
    def create_notifiers(self) -> list[Notifier]: ...


class OnlineChannel(SalesChannel):
    def create_payment(self):
        return CardPayment()

    def create_notifiers(self):
        return [EmailNotifier(), SmsNotifier()]


class BoxOfficeChannel(SalesChannel):
    def create_payment(self):
        return CashPayment()

    def create_notifiers(self):
        return [ReceiptPrinter()]
