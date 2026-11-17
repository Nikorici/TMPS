import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { EventBuilder } from "../src/creational/event-builder.ts";
import { EventCatalog } from "../src/creational/event-catalog.ts";
import { BoxOfficeChannel, OnlineChannel } from "../src/creational/sales-channels.ts";
import { mdl } from "../src/domain/money.ts";
import { AuditLog } from "../src/structural/decorator/audit-log.ts";
import { BUYER, conference, offlineMailer, SENDER } from "./fixtures.ts";

describe("creational patterns reused from Lab 2", () => {
  it("Builder names the missing required steps", () => {
    assert.throws(() => new EventBuilder().named("Summit").build(), /missing: date, price/);
  });

  it("Prototype edition copies the template and leaves it unchanged", () => {
    const template = conference();
    const catalog = new EventCatalog();
    catalog.register("conf", template);
    const edition = catalog.edition("conf", { venue: "Bălți", capacity: 8 });
    assert.notEqual(edition, template);
    assert.equal(edition.name, template.name);
    assert.deepEqual([edition.venue, edition.capacity, template.venue, template.capacity], ["Bălți", 8, "Test Hall", 100]);
  });

  it("Abstract Factory creates a matching payment per channel", async () => {
    const audit = new AuditLog();
    assert.match(await new OnlineChannel(offlineMailer(), SENDER, audit).createPayment().charge(BUYER, mdl(10)), /^CARD-/);
    assert.match(await new BoxOfficeChannel(audit).createPayment().charge(BUYER, mdl(10)), /^CASH-/);
  });
});
