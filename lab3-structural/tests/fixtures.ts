import nodemailer, { type Transporter } from "nodemailer";
import { EventBuilder } from "../src/creational/event-builder.ts";
import type { Customer, Event } from "../src/domain/models.ts";
import type { PaymentGateway } from "../src/services/payments.ts";

export const SENDER = "Test Conf <tickets@conf.example>";

export function offlineMailer(): Transporter {
  return nodemailer.createTransport({ jsonTransport: true });
}

export const BUYER: Customer = { name: "Buyer", email: "buyer@example.com", phone: "+1", isStudent: false };
export const STUDENT: Customer = { name: "Student", email: "student@example.com", phone: "+2", isStudent: true };
export const ORDERED_ON = "2026-11-25";

export class CountingGateway implements PaymentGateway {
  charges = 0;

  async charge(): Promise<string> {
    this.charges += 1;
    return `TEST-${this.charges}`;
  }
}

export function conference(capacity = 100): Event {
  return new EventBuilder().named("Test Conf").on("2026-12-01").at("Test Hall").pricedAt(100).withCapacity(capacity).build();
}
