import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, it, mock } from "node:test";
import { OnlineChannel } from "../src/creational/sales-channels.ts";
import { PaymentDeclined } from "../src/domain/errors.ts";
import { BookingService } from "../src/services/booking-service.ts";
import { InMemoryOrderRepository } from "../src/services/order-repository.ts";
import { PriceCalculator } from "../src/services/pricing.ts";
import { ReceiptFormatter } from "../src/services/receipts.ts";
import { AuditLog } from "../src/structural/decorator/audit-log.ts";
import { ProtectedOrderRepository } from "../src/structural/proxy/protected-order-repository.ts";
import { BUYER, conference, offlineMailer, ORDERED_ON, SENDER } from "./fixtures.ts";

function onlineDesk() {
  const repository = new InMemoryOrderRepository();
  const auditLog = new AuditLog();
  const mailer = offlineMailer();
  const sendMail = mock.method(mailer, "sendMail");
  const channel = new OnlineChannel(mailer, SENDER, auditLog);
  const desk = new BookingService(
    new PriceCalculator([]),
    channel.createPayment(),
    new ProtectedOrderRepository(repository, { name: "Online shop", role: "seller" }),
    channel.createNotifiers(),
    new ReceiptFormatter(),
  );
  return { desk, repository, auditLog, sendMail };
}

describe("Patterns working together in one booking", () => {
  beforeEach(() => mock.method(console, "log", () => {}));
  afterEach(() => mock.restoreAll());

  it("an online booking goes through the Proxy, the Decorators and the Adapter", async () => {
    const { desk, repository, auditLog, sendMail } = onlineDesk();
    const order = await desk.book(conference(), BUYER, 2, ORDERED_ON);

    assert.deepEqual(repository.all(), [order]);
    assert.deepEqual(auditLog.list(), [{ reference: "CARD-0001", customer: "Buyer", amount: order.total }]);
    assert.equal(sendMail.mock.callCount(), 1);
  });

  it("an over-limit booking stops in the Decorator: nothing saved, audited or emailed", async () => {
    const { desk, repository, auditLog, sendMail } = onlineDesk();
    await assert.rejects(desk.book(conference(200), BUYER, 150, ORDERED_ON), PaymentDeclined);

    assert.equal(repository.all().length, 0);
    assert.equal(auditLog.list().length, 0);
    assert.equal(sendMail.mock.callCount(), 0);
  });
});
