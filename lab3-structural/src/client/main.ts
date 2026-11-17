import nodemailer from "nodemailer";
import { EventBuilder } from "../creational/event-builder.ts";
import { EventCatalog } from "../creational/event-catalog.ts";
import { BoxOfficeChannel, OnlineChannel, type SalesChannel } from "../creational/sales-channels.ts";
import { AccessDenied, PaymentDeclined, SoldOut } from "../domain/errors.ts";
import type { Customer } from "../domain/models.ts";
import { formatMdl, mdl } from "../domain/money.ts";
import { BookingService } from "../services/booking-service.ts";
import { InMemoryOrderRepository } from "../services/order-repository.ts";
import { EarlyBirdDiscount, GroupDiscount, PriceCalculator, StudentDiscount } from "../services/pricing.ts";
import { ReceiptFormatter } from "../services/receipts.ts";
import { AuditLog } from "../structural/decorator/audit-log.ts";
import { ProtectedOrderRepository } from "../structural/proxy/protected-order-repository.ts";
import type { StaffMember } from "../structural/proxy/staff.ts";

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
const auditLog = new AuditLog();

const onlineShop: StaffMember = { name: "Online shop", role: "seller" };
const cashier: StaffMember = { name: "Victor Rotaru", role: "seller" };
const organizer: StaffMember = { name: "Elena Moraru", role: "organizer" };

function openDesk(channel: SalesChannel, staff: StaffMember): BookingService {
  const orders = new ProtectedOrderRepository(repository, staff);
  return new BookingService(calculator, channel.createPayment(), orders, channel.createNotifiers(), receipts);
}

const mailer = nodemailer.createTransport({ jsonTransport: true });
const online = openDesk(new OnlineChannel(mailer, "Moldova Tech Summit <tickets@techsummit.example>", auditLog), onlineShop);
const boxOffice = openDesk(new BoxOfficeChannel(auditLog), cashier);

const student: Customer = { name: "Ana Rusu", email: "ana.rusu@example.com", phone: "+37360000001", isStudent: true };
const teamLead: Customer = { name: "Ion Ceban", email: "ion.ceban@example.com", phone: "+37360000002", isStudent: false };
const company: Customer = { name: "Mihai Popa", email: "mihai.popa@example.com", phone: "+37360000004", isStudent: false };
const lateBuyer: Customer = { name: "Maria Lungu", email: "maria.lungu@example.com", phone: "+37360000003", isStudent: false };

console.log("=== 1. Online sale, early-bird student, 2 tickets  [Proxy -> Decorators -> Adapter] ===");
await online.book(summit, student, 2, "2026-10-27");

console.log("=== 2. Box office sale, group of 6, Bălți edition  [Prototype event, Proxy -> Decorator] ===");
await boxOffice.book(balti, teamLead, 6, "2027-03-01");

console.log("=== 3. Online sale, 30 tickets over the 10,000 MDL card limit  [SpendingLimitPayment decorator] ===");
try {
  await online.book(summit, company, 30, "2026-11-20");
} catch (error) {
  if (!(error instanceof PaymentDeclined)) throw error;
  console.log(`Payment declined: ${error.message}\n`);
}

console.log("=== 4. Online sale, 3 more tickets for Bălți (8 seats)  [seats counted through the Proxy] ===");
try {
  await online.book(balti, lateBuyer, 3, "2027-03-02");
} catch (error) {
  if (!(error instanceof SoldOut)) throw error;
  console.log(`Sold out: ${error.message}\n`);
}

console.log("=== 5. Cashier tries to export the customer list  [Proxy blocks] ===");
try {
  new ProtectedOrderRepository(repository, cashier).all();
} catch (error) {
  if (!(error instanceof AccessDenied)) throw error;
  console.log(`Access denied: ${error.message}\n`);
}

console.log("=== 6. Organizer report  [Proxy allows] ===");
const organizerView = new ProtectedOrderRepository(repository, organizer);
for (const order of organizerView.all()) {
  const { customer, event } = order;
  console.log(`#${order.id}  ${customer.name.padEnd(10)}  ${customer.email.padEnd(22)}  ${order.quantity} x ${event.venue.padEnd(23)}  ${formatMdl(order.total).padStart(12)}`);
}
for (const event of [summit, balti]) {
  console.log(`${event.venue}: ${organizerView.ticketsSold(event)}/${event.capacity} seats sold`);
}

console.log("\n=== 7. Payment audit log  [AuditedPayment decorator] ===");
for (const entry of auditLog.list()) {
  console.log(`${entry.reference}  ${formatMdl(entry.amount).padStart(12)}  ${entry.customer}`);
}
