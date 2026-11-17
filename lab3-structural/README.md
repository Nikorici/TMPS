# Ticketing System — Structural Design Patterns

A console ticket booking system for the "Moldova Tech Summit" tour. It continues the project from
[Lab 1 (SOLID)](../lab1-solid) and [Lab 2 (creational patterns)](../lab2-creational) and adds three
structural patterns: **Adapter**, **Decorator** and **Proxy**.

The design, UML diagrams, code snippets and test evidence are in **[REPORT.md](REPORT.md)**.

## Requirements

- Node.js **23.6 or newer** (it runs TypeScript files directly; developed on Node 26.12)
- npm

## Install

```bash
npm install
```

## Run the demo

```bash
npm start
```

The demo runs 7 numbered scenarios, each labelled with the pattern it shows: online and box-office
sales, an order blocked by the card spending limit, a sold-out edition, a cashier blocked from the
customer list, the organizer report and the payment audit log.

## Run the tests

```bash
npm test
```

One command type-checks the whole project with `tsc` (strict mode) and runs all 17 unit tests with
Node's built-in test runner (`node:test`).

## Project structure

```
src/
├── domain/                 models (Event, TicketOrder, Customer), money helpers, errors
├── services/               BookingService, pricing, receipts and the interfaces
│                           PaymentGateway, Notifier, OrderRepository + their basic implementations
├── creational/             reused from Lab 2: EventBuilder, EventCatalog (Prototype), SalesChannel factories
├── structural/
│   ├── adapter/            NodemailerNotifier
│   ├── decorator/          PaymentDecorator, AuditedPayment, SpendingLimitPayment, AuditLog
│   └── proxy/              ProtectedOrderRepository, StaffMember
└── client/main.ts          the demo (composition root)
tests/                      one test file per pattern + interaction, core and creational tests
```

## Where each pattern lives

| Pattern | Files | What it does here |
|---|---|---|
| Adapter | `src/structural/adapter/` | Lets the third-party `nodemailer` library work as our `Notifier` |
| Decorator | `src/structural/decorator/` | Adds an audit log and a card spending limit to any `PaymentGateway` |
| Proxy | `src/structural/proxy/` | Stands in for `OrderRepository` and blocks sellers from exporting customer data |

## Sending real email

The demo uses nodemailer's offline `jsonTransport`, so nothing is actually sent. To send real email,
replace that one line in `src/client/main.ts` with an SMTP transport:

```ts
const mailer = nodemailer.createTransport({ host: "smtp.example.com", port: 587, auth: { user, pass } });
```

No other code changes, because the rest of the system only sees the `Notifier` interface.
