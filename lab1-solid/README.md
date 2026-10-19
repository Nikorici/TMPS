# Laboratory Work 1 — SOLID Principles

**Author:** Daniel Nicorici, FAF-243
**Language:** Python 3.10+ (standard library only)

## Objectives

1. Study the SOLID principles of object-oriented design.
2. Implement three of them — **S**, **O** and **D** — in a small working project.
3. Show, with tests, that the design actually delivers what each principle promises.

## The project

A small **event ticket booking** system. A customer books tickets to an event, the price is computed
from a set of discount rules, the payment is charged, the order is saved and the customer receives a
receipt by email and SMS.

```
lab1-solid/
├── main.py                  composition root + demo scenarios
├── ticketing/
│   ├── models.py            Event, Customer, TicketOrder
│   ├── pricing.py           DiscountPolicy + EarlyBird/Student/Group, PriceCalculator, PriceQuote
│   ├── payments.py          PaymentGateway + CardPayment, WalletPayment, PaymentDeclined
│   ├── notifications.py     Notifier + EmailNotifier, SmsNotifier
│   ├── repository.py        OrderRepository + InMemoryOrderRepository
│   ├── receipts.py          ReceiptFormatter
│   └── service.py           BookingService (the high-level use case)
└── tests/test_solid.py      one test class per principle
```

## Theory

| Letter | Principle | Statement |
|---|---|---|
| **S** | Single Responsibility | A class should have one, and only one, reason to change. |
| **O** | Open/Closed | Software entities should be open for extension, but closed for modification. |
| **L** | Liskov Substitution | Subtypes must be substitutable for their base types. |
| **I** | Interface Segregation | Clients should not be forced to depend on methods they do not use. |
| **D** | Dependency Inversion | High-level modules should not depend on low-level modules; both should depend on abstractions. |

This lab implements **S**, **O** and **D**.

## Implementation

### S — Single Responsibility Principle

The obvious "god class" version of this program would be one `TicketShop.book()` method that computes
prices, talks to the card processor, writes to storage, formats the email and sends it. Any change to
discounts, payments, storage or the receipt layout would touch that same class.

Instead, every job lives in its own class, so each has exactly one reason to change:

| Class | Its only responsibility | Changes when… |
|---|---|---|
| `TicketOrder` | hold and validate order data | the order's shape changes |
| `PriceCalculator` | turn an order into a `PriceQuote` | the pricing rules change |
| `PaymentGateway` subclasses | charge money | a payment provider changes |
| `OrderRepository` subclasses | store and find orders | the storage changes |
| `ReceiptFormatter` | build the receipt text | the receipt layout changes |
| `Notifier` subclasses | deliver a message over one channel | a channel changes |
| `BookingService` | orchestrate the steps of a booking | the booking workflow changes |

The receipt formatter, for example, knows nothing about how money is charged or how messages are sent:

```python
class ReceiptFormatter:
    def format(self, order: TicketOrder, quote: PriceQuote) -> str:
        lines = [
            f"Order #{order.id} confirmed: {order.quantity} x {order.event.name} on {order.event.date:%d.%m.%Y}",
            f"  Subtotal: {quote.subtotal} MDL",
        ]
        lines += [f"  {name} discount: -{amount} MDL" for name, amount in quote.discounts]
        ...
```

### O — Open/Closed Principle

Discounts are the part of a ticketing system that changes most often (early bird, student, group,
promo codes, partner deals…). Writing them as an `if/elif` chain inside the calculator would mean
editing and re-testing the calculator for every new campaign.

Each discount is instead a subclass of one abstraction:

```python
class DiscountPolicy(ABC):
    name: str

    @abstractmethod
    def discount(self, order: TicketOrder, subtotal: Decimal) -> Decimal: ...


class StudentDiscount(DiscountPolicy):
    name = "Student"

    def discount(self, order, subtotal):
        return subtotal * self.rate if order.customer.is_student else ZERO
```

`PriceCalculator` only iterates over whatever policies it was given and applies a global cap (30%), so
it is **closed for modification** but **open for extension**:

```python
for policy in self.policies:
    amount = policy.discount(order, subtotal).quantize(CENT)
    if amount > ZERO:
        applied.append((policy.name, amount))
```

The test `test_new_policy_needs_no_change_to_calculator` proves it: it declares a brand-new
`PromoCodeDiscount` inside the test and the existing calculator applies it without a single line of
`pricing.py` being edited. The same idea applies to `PaymentGateway` (new providers) and `Notifier`
(new channels).

### D — Dependency Inversion Principle

`BookingService` is the high-level policy of the application. It depends only on abstractions —
`PaymentGateway`, `OrderRepository` and `Notifier` — and receives the concrete objects through its
constructor:

```python
class BookingService:
    def __init__(self, calculator, payments: PaymentGateway, repository: OrderRepository,
                 notifiers: list[Notifier], receipts: ReceiptFormatter): ...

    def book(self, event, customer, quantity, ordered_on):
        order = TicketOrder(event, customer, quantity, ordered_on)
        quote = self._calculator.quote(order)
        order.payment_reference = self._payments.charge(customer, quote.total)
        order.total = quote.total
        saved = self._repository.save(order)
        receipt = self._receipts.format(saved, quote)
        for notifier in self._notifiers:
            notifier.send(customer, receipt)
        return saved
```

It never imports `CardPayment`, `EmailNotifier` or `InMemoryOrderRepository`. The only place where
concrete classes are chosen is the composition root, `main.py`:

```python
card_desk = BookingService(calculator, CardPayment("4111111111111111"), repository,
                           [EmailNotifier(), SmsNotifier()], receipts)
wallet_desk = BookingService(calculator, WalletPayment(Decimal("500.00")), repository,
                             [EmailNotifier()], receipts)
```

Two booking desks with different payment methods and channels reuse the exact same service. In the
tests, the service runs with a fake `FixedGateway` and a `RecordingNotifier`: no real money, no
console output, and the test can check exactly what was charged and sent. Replacing the in-memory
repository with a PostgreSQL one would also leave `BookingService` untouched.

## Running

```bash
python3 main.py              # demo: early-bird student, late group order, declined wallet payment
python3 -m unittest -v       # 9 tests, grouped by principle
```

Demo output (abridged):

```
=== Early-bird student, 2 tickets, card ===
[email -> ana.rusu@example.com]
Order #1 confirmed: 2 x Moldova Tech Summit on 05.12.2026
  Subtotal: 900.00 MDL
  Early bird discount: -180.00 MDL
  Student discount: -135.00 MDL
  Discounts capped at -270.00 MDL
  Total paid: 630.00 MDL
  Payment reference: CARD-1111-0001
...
=== Wallet order with insufficient balance ===
Payment declined: Wallet balance 500.00 MDL is below 1350.00 MDL

Orders stored: 2
```

## Conclusions

Applying SRP split the booking flow into small classes that each have a single reason to change. That
made every piece easy to read and to test on its own. OCP, implemented through the `DiscountPolicy`
abstraction, means a new discount is a new class rather than an edit to working code. The test suite
shows this by adding a promo code without touching the calculator. DIP made `BookingService` depend
only on abstractions, with the concrete payment, storage and notification classes injected from
`main.py`. That allowed two differently configured booking desks in the demo and fake collaborators in
the tests, with no change to the service. Together, the three principles give a design where changes
stay local, new behaviour is added by extension and the core logic can be tested in isolation.
