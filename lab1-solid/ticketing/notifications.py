from abc import ABC, abstractmethod

from ticketing.models import Customer


class Notifier(ABC):
    @abstractmethod
    def send(self, customer: Customer, message: str) -> None: ...


class EmailNotifier(Notifier):
    def send(self, customer, message):
        print(f"[email -> {customer.email}]\n{message}\n")


class SmsNotifier(Notifier):
    def send(self, customer, message):
        first_line = message.splitlines()[0]
        print(f"[sms -> {customer.phone}] {first_line}\n")
