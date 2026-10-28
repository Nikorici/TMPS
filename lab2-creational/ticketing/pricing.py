from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from ticketing.models import TicketOrder

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


class DiscountPolicy(ABC):
    name: str

    @abstractmethod
    def discount(self, order: TicketOrder, subtotal: Decimal) -> Decimal: ...


class EarlyBirdDiscount(DiscountPolicy):
    name = "Early bird"

    def __init__(self, days_before: int = 30, rate: Decimal = Decimal("0.20")):
        self.days_before = days_before
        self.rate = rate

    def discount(self, order, subtotal):
        days_left = (order.event.date - order.ordered_on).days
        return subtotal * self.rate if days_left >= self.days_before else ZERO


class StudentDiscount(DiscountPolicy):
    name = "Student"

    def __init__(self, rate: Decimal = Decimal("0.15")):
        self.rate = rate

    def discount(self, order, subtotal):
        return subtotal * self.rate if order.customer.is_student else ZERO


class GroupDiscount(DiscountPolicy):
    name = "Group"

    def __init__(self, min_quantity: int = 5, rate: Decimal = Decimal("0.10")):
        self.min_quantity = min_quantity
        self.rate = rate

    def discount(self, order, subtotal):
        return subtotal * self.rate if order.quantity >= self.min_quantity else ZERO


@dataclass(frozen=True)
class PriceQuote:
    subtotal: Decimal
    discounts: list[tuple[str, Decimal]]
    total: Decimal

    @property
    def savings(self) -> Decimal:
        return self.subtotal - self.total

    @property
    def capped(self) -> bool:
        return self.savings < sum((amount for _, amount in self.discounts), ZERO)


class PriceCalculator:
    def __init__(self, policies: list[DiscountPolicy], max_discount_rate: Decimal = Decimal("0.30")):
        self.policies = policies
        self.max_discount_rate = max_discount_rate

    def quote(self, order: TicketOrder) -> PriceQuote:
        subtotal = (order.event.base_price * order.quantity).quantize(CENT)
        applied = []
        for policy in self.policies:
            amount = policy.discount(order, subtotal).quantize(CENT)
            if amount > ZERO:
                applied.append((policy.name, amount))
        cap = (subtotal * self.max_discount_rate).quantize(CENT)
        total_discount = min(sum((amount for _, amount in applied), ZERO), cap)
        return PriceQuote(subtotal, applied, subtotal - total_discount)
