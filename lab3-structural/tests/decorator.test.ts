import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { PaymentDeclined } from "../src/domain/errors.ts";
import type { Customer } from "../src/domain/models.ts";
import { mdl } from "../src/domain/money.ts";
import type { PaymentGateway } from "../src/services/payments.ts";
import { AuditLog } from "../src/structural/decorator/audit-log.ts";
import { AuditedPayment } from "../src/structural/decorator/audited-payment.ts";
import { PaymentDecorator } from "../src/structural/decorator/payment-decorator.ts";
import { SpendingLimitPayment } from "../src/structural/decorator/spending-limit-payment.ts";
import { BUYER, CountingGateway } from "./fixtures.ts";

const LIMIT = mdl(1_000);

describe("Decorator: payment gateways wrapped with extra responsibilities", () => {
  it("AuditedPayment records the charge and returns the wrapped reference unchanged", async () => {
    const log = new AuditLog();
    const reference = await new AuditedPayment(new CountingGateway(), log).charge(BUYER, mdl(250));
    assert.equal(reference, "TEST-1");
    assert.deepEqual(log.list(), [{ reference: "TEST-1", customer: "Buyer", amount: mdl(250) }]);
  });

  it("SpendingLimitPayment declines an over-limit amount without calling the wrapped gateway", async () => {
    const card = new CountingGateway();
    const limited = new SpendingLimitPayment(card, LIMIT);
    await assert.rejects(limited.charge(BUYER, LIMIT + 1), PaymentDeclined);
    assert.equal(card.charges, 0);
    assert.equal(await limited.charge(BUYER, LIMIT), "TEST-1");
  });

  it("decorators stacked in either order give the same result", async () => {
    const stacks: Array<(card: PaymentGateway, log: AuditLog) => PaymentGateway> = [
      (card, log) => new SpendingLimitPayment(new AuditedPayment(card, log), LIMIT),
      (card, log) => new AuditedPayment(new SpendingLimitPayment(card, LIMIT), log),
    ];
    for (const stack of stacks) {
      const card = new CountingGateway();
      const log = new AuditLog();
      const payment = stack(card, log);
      assert.equal(await payment.charge(BUYER, mdl(300)), "TEST-1");
      await assert.rejects(payment.charge(BUYER, mdl(5_000)), PaymentDeclined);
      assert.equal(card.charges, 1);
      assert.deepEqual(log.list().map((entry) => entry.reference), ["TEST-1"]);
    }
  });

  it("a new decorator is added as a new class only and stacks with the existing ones", async () => {
    class PrefixedReferencePayment extends PaymentDecorator {
      override async charge(customer: Customer, amount: number): Promise<string> {
        return `SUMMIT-${await super.charge(customer, amount)}`;
      }
    }
    const log = new AuditLog();
    const payment = new PrefixedReferencePayment(new AuditedPayment(new SpendingLimitPayment(new CountingGateway(), LIMIT), log));
    assert.equal(await payment.charge(BUYER, mdl(100)), "SUMMIT-TEST-1");
    assert.equal(log.list().length, 1);
  });
});
