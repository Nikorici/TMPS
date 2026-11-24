import mailbox
from email.message import EmailMessage
from email.utils import formataddr

from ticketing.domain.models import Customer
from ticketing.services.notifications import Notifier


class MailboxEmailNotifier(Notifier):
    def __init__(self, outbox: mailbox.Maildir, sender: str):
        self._outbox = outbox
        self._sender = sender

    def send(self, customer: Customer, message: str) -> None:
        email = EmailMessage()
        email["From"] = self._sender
        email["To"] = formataddr((customer.name, customer.email))
        email["Subject"] = message.splitlines()[0]
        email.set_content(message)
        key = self._outbox.add(email)
        print(f'[email -> {customer.email}] "{email["Subject"]}" saved to outbox as {key}\n')
