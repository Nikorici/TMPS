import mailbox
import os
import shutil
import tempfile
import unittest
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser

from ticketing.services.payments import PaymentGateway

SENDER = "Test Conf <tickets@conf.example>"


def temp_outbox(test: unittest.TestCase) -> mailbox.Maildir:
    folder = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, folder)
    return mailbox.Maildir(os.path.join(folder, "outbox"))


def read_emails(outbox: mailbox.Maildir) -> list[EmailMessage]:
    return [BytesParser(policy=policy.default).parsebytes(outbox.get_bytes(key)) for key in outbox.keys()]


class CountingGateway(PaymentGateway):
    def __init__(self):
        self.charges = 0

    def charge(self, customer, amount):
        self.charges += 1
        return f"TEST-{self.charges}"
