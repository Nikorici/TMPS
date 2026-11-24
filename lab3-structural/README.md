# Ticketing System — Structural Design Patterns

A console ticket booking system for the "Moldova Tech Summit" tour. It continues the project from
[Lab 1 (SOLID)](../lab1-solid) and [Lab 2 (creational patterns)](../lab2-creational) and adds three
structural patterns: **Adapter**, **Decorator** and **Proxy**.

The design, UML diagrams, code snippets and test evidence are in **[REPORT.md](REPORT.md)**.

## Requirements

- Python **3.10 or newer** (developed on 3.14)
- Nothing to install: the project uses only the standard library

## Run the demo

```bash
python3 main.py
```

The demo runs 7 numbered scenarios, each labelled with the pattern it shows: online and box-office
sales, an order blocked by the card spending limit, a sold-out edition, a cashier blocked from the
customer list, the organizer report and the payment audit log.

Online receipts are delivered as real email files into `outbox/` (a Maildir: `outbox/new/*.eml`).
Any mail client can open them. The folder is git-ignored.

## Run the tests

```bash
python3 -m unittest -v
```

One command runs all 35 tests: 9 from Lab 1, 14 from Lab 2 and 12 new ones for this lab.

## Project structure

```
ticketing/
├── domain/                  models (Event, Customer, TicketOrder) and errors
├── services/                BookingService, pricing, receipts and the interfaces
│                            PaymentGateway, Notifier, OrderRepository + their basic implementations
├── creational/              from Lab 2: EventBuilder, EventCatalog (Prototype), SalesChannel factories
└── structural/
    ├── adapter/             MailboxEmailNotifier
    ├── decorator/           PaymentDecorator, AuditedPayment, SpendingLimitPayment, AuditLog
    └── proxy/               ProtectedOrderRepository, StaffMember, Role
main.py                      the client: builds everything and runs the demo
tests/                       one test file per pattern + interaction, plus the Lab 1 and Lab 2 tests
```

## Where each pattern lives

| Pattern | Folder | What it does here |
|---|---|---|
| Adapter | `ticketing/structural/adapter/` | Lets Python's `mailbox` / `email` library work as our `Notifier` |
| Decorator | `ticketing/structural/decorator/` | Adds an audit log and a card spending limit to any `PaymentGateway` |
| Proxy | `ticketing/structural/proxy/` | Stands in for `OrderRepository` and blocks sellers from exporting customer data |
