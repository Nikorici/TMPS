import mailbox
from abc import ABC, abstractmethod
from decimal import Decimal

from ticketing.services.notifications import Notifier, ReceiptPrinter, SmsNotifier
from ticketing.services.payments import CardPayment, CashPayment, PaymentGateway
from ticketing.structural.adapter.mailbox_email_notifier import MailboxEmailNotifier
from ticketing.structural.decorator.audit_log import AuditLog
from ticketing.structural.decorator.audited_payment import AuditedPayment
from ticketing.structural.decorator.spending_limit_payment import SpendingLimitPayment

ONLINE_CARD_LIMIT = Decimal("10000.00")


class SalesChannel(ABC):
    @abstractmethod
    def create_payment(self) -> PaymentGateway: ...

    @abstractmethod
    def create_notifiers(self) -> list[Notifier]: ...


class OnlineChannel(SalesChannel):
    def __init__(self, outbox: mailbox.Maildir, sender: str, audit_log: AuditLog):
        self._outbox = outbox
        self._sender = sender
        self._audit_log = audit_log

    def create_payment(self):
        return SpendingLimitPayment(AuditedPayment(CardPayment(), self._audit_log), ONLINE_CARD_LIMIT)

    def create_notifiers(self):
        return [MailboxEmailNotifier(self._outbox, self._sender), SmsNotifier()]


class BoxOfficeChannel(SalesChannel):
    def __init__(self, audit_log: AuditLog):
        self._audit_log = audit_log

    def create_payment(self):
        return AuditedPayment(CashPayment(), self._audit_log)

    def create_notifiers(self):
        return [ReceiptPrinter()]
