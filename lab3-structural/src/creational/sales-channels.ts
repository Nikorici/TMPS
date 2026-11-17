import type { Transporter } from "nodemailer";
import { type Notifier, ReceiptPrinter, SmsNotifier } from "../services/notifications.ts";
import { CardPayment, CashPayment, type PaymentGateway } from "../services/payments.ts";
import { NodemailerNotifier } from "../structural/adapter/nodemailer-notifier.ts";

export interface SalesChannel {
  createPayment(): PaymentGateway;
  createNotifiers(): Notifier[];
}

export class OnlineChannel implements SalesChannel {
  private readonly mailer: Transporter;
  private readonly sender: string;

  constructor(mailer: Transporter, sender: string) {
    this.mailer = mailer;
    this.sender = sender;
  }

  createPayment(): PaymentGateway {
    return new CardPayment();
  }

  createNotifiers(): Notifier[] {
    return [new NodemailerNotifier(this.mailer, this.sender), new SmsNotifier()];
  }
}

export class BoxOfficeChannel implements SalesChannel {
  createPayment(): PaymentGateway {
    return new CashPayment();
  }

  createNotifiers(): Notifier[] {
    return [new ReceiptPrinter()];
  }
}
