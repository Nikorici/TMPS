# Ticketing System — Behavioral Design Patterns

A console ticket booking system for the "Moldova Tech Summit" tour. It continues the project from
[Lab 1 (SOLID)](../lab1-solid), [Lab 2 (creational)](../lab2-creational) and
[Lab 3 (structural)](../lab3-structural), and adds three behavioral patterns: **State**, **Command**
and **Observer**.

The design, UML diagrams, code snippets and test evidence are in **[REPORT.md](REPORT.md)**.

## Requirements

- Python **3.10 or newer** (developed on 3.14)
- Nothing to install: the project uses only the standard library

## Run the demo

```bash
python3 main.py
```

Sections 1–7 are the sales flow from the previous labs. Sections 8–14 are new: a door scanner checks
a ticket in, the same ticket is rejected when scanned twice, the check-in is undone, support refunds
an order and frees its seats, a sold-out buyer gets in, the organizer turns off customer SMS while the
app runs, and the consoles print their command history. Each section names the pattern it shows.

## Run the tests

```bash
python3 -m unittest -v
```

One command runs all 46 tests: 35 from Labs 1–3 and 11 new ones for this lab.

## Project structure

```
ticketing/
├── domain/                  models (Event, Customer, TicketOrder) and errors
├── services/                BookingService, pricing, receipts, payments, notifications, repository
├── creational/              Lab 2: EventBuilder, EventCatalog (Prototype), SalesChannel factories
├── structural/              Lab 3: adapter/, decorator/, proxy/
└── behavioral/
    ├── state/               OrderState + PendingPayment, Paid, CheckedIn, Refunded states
    ├── observer/            OrderStatusFeed (subject), OrderObserver + CustomerUpdates, RefundLedger, AttendanceBoard
    └── command/             OrderCommand + CheckInCommand, RefundCommand, StaffConsole (invoker)
main.py                      the client: builds everything and runs the demo
tests/                       one test file per pattern + order flow, plus all earlier tests
```

## Where each pattern lives

| Pattern | Folder | What it does here |
|---|---|---|
| State | `ticketing/behavioral/state/` | An order behaves differently when pending, paid, checked in or refunded |
| Command | `ticketing/behavioral/command/` | Staff actions (check in, refund) become objects with history and undo |
| Observer | `ticketing/behavioral/observer/` | Every order status change is announced to subscribers that can join or leave at runtime |
