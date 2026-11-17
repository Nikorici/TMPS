import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, it, mock } from "node:test";
import { BookingService } from "../src/services/booking-service.ts";
import type { Notifier } from "../src/services/notifications.ts";
import { InMemoryOrderRepository } from "../src/services/order-repository.ts";
import { CardPayment } from "../src/services/payments.ts";
import { PriceCalculator } from "../src/services/pricing.ts";
import { ReceiptFormatter } from "../src/services/receipts.ts";
import { NodemailerNotifier } from "../src/structural/adapter/nodemailer-notifier.ts";
import { BUYER, conference, offlineMailer, ORDERED_ON, SENDER } from "./fixtures.ts";

async function sentMessage(call: { result?: unknown }): Promise<Record<string, unknown>> {
  const info = (await call.result) as { message: string };
  return JSON.parse(info.message);
}

describe("Adapter: NodemailerNotifier adapts nodemailer to Notifier", () => {
  beforeEach(() => mock.method(console, "log", () => {}));
  afterEach(() => mock.restoreAll());

  it("translates customer + receipt into a nodemailer message", async () => {
    const mailer = offlineMailer();
    const sendMail = mock.method(mailer, "sendMail");
    await new NodemailerNotifier(mailer, SENDER).send(BUYER, "Order #7 confirmed\n  Total paid: 100.00 MDL");

    const sent = await sentMessage(sendMail.mock.calls[0]);
    assert.equal(sendMail.mock.callCount(), 1);
    assert.deepEqual(sent.to, [{ name: "Buyer", address: "buyer@example.com" }]);
    assert.deepEqual(sent.from, { name: "Test Conf", address: "tickets@conf.example" });
    assert.equal(sent.subject, "Order #7 confirmed");
    assert.equal(sent.text, "Order #7 confirmed\n  Total paid: 100.00 MDL");
  });

  it("works wherever a Notifier is expected: a booking emails its receipt", async () => {
    const mailer = offlineMailer();
    const sendMail = mock.method(mailer, "sendMail");
    const notifiers: Notifier[] = [new NodemailerNotifier(mailer, SENDER)];
    const service = new BookingService(new PriceCalculator([]), new CardPayment(), new InMemoryOrderRepository(), notifiers, new ReceiptFormatter());

    await service.book(conference(), BUYER, 2, ORDERED_ON);

    const sent = await sentMessage(sendMail.mock.calls[0]);
    assert.match(String(sent.subject), /^Order #1 confirmed: 2 x Test Conf/);
    assert.match(String(sent.text), /Total paid: 200\.00 MDL/);
  });

  it("passes library delivery failures back to the caller", async () => {
    const mailer = offlineMailer();
    mock.method(mailer, "sendMail", async () => {
      throw new Error("SMTP connection refused");
    });
    await assert.rejects(new NodemailerNotifier(mailer, SENDER).send(BUYER, "Order #1"), /SMTP connection refused/);
  });
});
