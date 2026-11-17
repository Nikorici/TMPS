import { EmailNotifier, type Notifier, ReceiptPrinter, SmsNotifier } from "../services/notifications.ts";
import { CardPayment, CashPayment, type PaymentGateway } from "../services/payments.ts";

export interface SalesChannel {
  createPayment(): PaymentGateway;
  createNotifiers(): Notifier[];
}

export class OnlineChannel implements SalesChannel {
  createPayment(): PaymentGateway {
    return new CardPayment();
  }

  createNotifiers(): Notifier[] {
    return [new EmailNotifier(), new SmsNotifier()];
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
