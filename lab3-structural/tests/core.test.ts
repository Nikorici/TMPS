import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { SoldOut } from "../src/domain/errors.ts";
import { TicketOrder } from "../src/domain/models.ts";
import { mdl } from "../src/domain/money.ts";
import { BookingService } from "../src/services/booking-service.ts";
import { InMemoryOrderRepository } from "../src/services/order-repository.ts";
import { EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount } from "../src/services/pricing.ts";
import { ReceiptFormatter } from "../src/services/receipts.ts";
import { BUYER, conference, CountingGateway, ORDERED_ON, STUDENT } from "./fixtures.ts";

describe("core booking (ported from Labs 1-2)", () => {
  it("caps combined discounts at 30%", () => {
    const calculator = new PriceCalculator([new EarlyBirdDiscount(), new StudentDiscount(), new GroupDiscount()]);
    const quote = calculator.quote(new TicketOrder(conference(), STUDENT, 5, "2026-10-01"));
    assert.equal(quote.subtotal, mdl(500));
    assert.equal(quote.total, mdl(350));
    assert.equal(quote.capped, true);
  });

  it("refuses a sold-out booking before charging", async () => {
    const gateway = new CountingGateway();
    const repository = new InMemoryOrderRepository();
    const service = new BookingService(new PriceCalculator([]), gateway, repository, [], new ReceiptFormatter());
    const event = conference(3);
    await service.book(event, BUYER, 2, ORDERED_ON);
    await assert.rejects(service.book(event, BUYER, 2, ORDERED_ON), SoldOut);
    assert.equal(gateway.charges, 1);
    assert.equal(repository.ticketsSold(event), 2);
  });
});
