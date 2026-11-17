import assert from "node:assert/strict";
import { describe, it, mock } from "node:test";
import { AccessDenied } from "../src/domain/errors.ts";
import { TicketOrder } from "../src/domain/models.ts";
import { InMemoryOrderRepository } from "../src/services/order-repository.ts";
import { ProtectedOrderRepository } from "../src/structural/proxy/protected-order-repository.ts";
import type { StaffMember } from "../src/structural/proxy/staff.ts";
import { BUYER, conference, ORDERED_ON } from "./fixtures.ts";

const CASHIER: StaffMember = { name: "Cashier", role: "seller" };
const ORGANIZER: StaffMember = { name: "Organizer", role: "organizer" };

describe("Proxy: ProtectedOrderRepository controls access to orders", () => {
  it("passes a seller's allowed calls through to the real repository unchanged", () => {
    const real = new InMemoryOrderRepository();
    const proxy = new ProtectedOrderRepository(real, CASHIER);
    const event = conference();
    const order = new TicketOrder(event, BUYER, 3, ORDERED_ON);

    assert.equal(proxy.save(order), order);
    assert.equal(real.find(order.id!), order);
    assert.equal(proxy.find(order.id!), order);
    assert.equal(proxy.ticketsSold(event), real.ticketsSold(event));
  });

  it("blocks a seller from exporting the customer list without reaching the real repository", () => {
    const real = new InMemoryOrderRepository();
    const all = mock.method(real, "all");
    const proxy = new ProtectedOrderRepository(real, CASHIER);

    assert.throws(() => proxy.all(), AccessDenied);
    assert.equal(all.mock.callCount(), 0);
  });

  it("gives an organizer exactly what the real repository returns", () => {
    const real = new InMemoryOrderRepository();
    real.save(new TicketOrder(conference(), BUYER, 1, ORDERED_ON));

    assert.deepEqual(new ProtectedOrderRepository(real, ORGANIZER).all(), real.all());
  });
});
