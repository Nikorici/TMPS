import type { Customer } from "../domain/models.ts";

export interface Notifier {
  send(customer: Customer, message: string): Promise<void>;
}

export class EmailNotifier implements Notifier {
  async send(customer: Customer, message: string): Promise<void> {
    console.log(`[email -> ${customer.email}]\n${message}\n`);
  }
}

export class SmsNotifier implements Notifier {
  async send(customer: Customer, message: string): Promise<void> {
    console.log(`[sms -> ${customer.phone}] ${message.split("\n")[0]}\n`);
  }
}

export class ReceiptPrinter implements Notifier {
  async send(customer: Customer, message: string): Promise<void> {
    console.log(`[printer -> ${customer.name}]\n${message}\n`);
  }
}
