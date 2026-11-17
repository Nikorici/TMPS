import { EventBuilder } from "../creational/event-builder.ts";
import { EventCatalog } from "../creational/event-catalog.ts";
import { BoxOfficeChannel, OnlineChannel, type SalesChannel } from "../creational/sales-channels.ts";
import { SoldOut } from "../domain/errors.ts";
import type { Customer } from "../domain/models.ts";
import { mdl } from "../domain/money.ts";
import { BookingService } from "../services/booking-service.ts";
import { InMemoryOrderRepository } from "../services/order-repository.ts";
import { EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount } from "../services/pricing.ts";
import { ReceiptFormatter } from "../services/receipts.ts";

const summit = new EventBuilder()
  .named("Moldova Tech Summit")
  .on("2026-12-05")
  .at("Chișinău Arena")
  .pricedAt(450)
  .withCapacity(300)
  .build();

const catalog = new EventCatalog();
catalog.register("tech-summit", summit);
const balti = catalog.edition("tech-summit", {
  date: "2027-03-12",
  venue: "Bălți Palace of Culture",
  basePrice: mdl(350),
  capacity: 8,
});

const calculator = new PriceCalculator([new EarlyBirdDiscount(), new StudentDiscount(), new GroupDiscount()]);
const repository = new InMemoryOrderRepository();
const receipts = new ReceiptFormatter();

function openDesk(channel: SalesChannel): BookingService {
  return new BookingService(calculator, channel.createPayment(), repository, channel.createNotifiers(), receipts);
}

const online = openDesk(new OnlineChannel());
const boxOffice = openDesk(new BoxOfficeChannel());

const student: Customer = { name: "Ana Rusu", email: "ana.rusu@example.com", phone: "+37360000001", isStudent: true };
const teamLead: Customer = { name: "Ion Ceban", email: "ion.ceban@example.com", phone: "+37360000002", isStudent: false };
const lateBuyer: Customer = { name: "Maria Lungu", email: "maria.lungu@example.com", phone: "+37360000003", isStudent: false };

console.log("=== Online: early-bird student, 2 tickets, Chișinău ===");
await online.book(summit, student, 2, "2026-10-27");

console.log("=== Box office: group of 6, Bălți edition ===");
await boxOffice.book(balti, teamLead, 6, "2027-03-01");

console.log("=== Online: 3 more tickets for Bălți (8 seats) ===");
try {
  await online.book(balti, lateBuyer, 3, "2027-03-02");
} catch (error) {
  if (!(error instanceof SoldOut)) throw error;
  console.log(`Sold out: ${error.message}\n`);
}

for (const event of [summit, balti]) {
  console.log(`${event.venue}: ${repository.ticketsSold(event)}/${event.capacity} seats sold`);
}
