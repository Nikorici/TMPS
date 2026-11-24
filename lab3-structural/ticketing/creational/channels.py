import mailbox
from abc import ABC, abstractmethod

from ticketing.services.notifications import Notifier, ReceiptPrinter, SmsNotifier
from ticketing.services.payments import CardPayment, CashPayment, PaymentGateway
from ticketing.structural.adapter.mailbox_email_notifier import MailboxEmailNotifier


class SalesChannel(ABC):
    @abstractmethod
    def create_payment(self) -> PaymentGateway: ...

    @abstractmethod
    def create_notifiers(self) -> list[Notifier]: ...


class OnlineChannel(SalesChannel):
    def __init__(self, outbox: mailbox.Maildir, sender: str):
        self._outbox = outbox
        self._sender = sender

    def create_payment(self):
        return CardPayment()

    def create_notifiers(self):
        return [MailboxEmailNotifier(self._outbox, self._sender), SmsNotifier()]


class BoxOfficeChannel(SalesChannel):
    def create_payment(self):
        return CashPayment()

    def create_notifiers(self):
        return [ReceiptPrinter()]
