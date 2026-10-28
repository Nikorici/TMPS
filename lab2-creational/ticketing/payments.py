from abc import ABC, abstractmethod
from decimal import Decimal
from itertools import count

from ticketing.models import Customer


class PaymentDeclined(Exception):
    pass


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, customer: Customer, amount: Decimal) -> str: ...


class CardPayment(PaymentGateway):
    def __init__(self):
        self._sequence = count(1)

    def charge(self, customer, amount):
        return f"CARD-{next(self._sequence):04d}"


class CashPayment(PaymentGateway):
    def __init__(self):
        self._sequence = count(1)

    def charge(self, customer, amount):
        return f"CASH-{next(self._sequence):04d}"


class WalletPayment(PaymentGateway):
    def __init__(self, balance: Decimal):
        self.balance = balance
        self._sequence = count(1)

    def charge(self, customer, amount):
        if amount > self.balance:
            raise PaymentDeclined(f"Wallet balance {self.balance} MDL is below {amount} MDL")
        self.balance -= amount
        return f"WALLET-{next(self._sequence):04d}"
