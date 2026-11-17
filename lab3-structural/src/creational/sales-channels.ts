import type { Transporter } from "nodemailer";
import { mdl } from "../domain/money.ts";
import { type Notifier, ReceiptPrinter, SmsNotifier } from "../services/notifications.ts";
import { CardPayment, CashPayment, type PaymentGateway } from "../services/payments.ts";
import { NodemailerNotifier } from "../structural/adapter/nodemailer-notifier.ts";
import type { AuditLog } from "../structural/decorator/audit-log.ts";
import { AuditedPayment } from "../structural/decorator/audited-payment.ts";
import { SpendingLimitPayment } from "../structural/decorator/spending-limit-payment.ts";

const ONLINE_CARD_LIMIT = mdl(10_000);

export interface SalesChannel {
  createPayment(): PaymentGateway;
  createNotifiers(): Notifier[];
}

export class OnlineChannel implements SalesChannel {
  private readonly mailer: Transporter;
  private readonly sender: string;
  private readonly auditLog: AuditLog;

  constructor(mailer: Transporter, sender: string, auditLog: AuditLog) {
    this.mailer = mailer;
    this.sender = sender;
    this.auditLog = auditLog;
  }

  createPayment(): PaymentGateway {
    return new SpendingLimitPayment(new AuditedPayment(new CardPayment(), this.auditLog), ONLINE_CARD_LIMIT);
  }

  createNotifiers(): Notifier[] {
    return [new NodemailerNotifier(this.mailer, this.sender), new SmsNotifier()];
  }
}

export class BoxOfficeChannel implements SalesChannel {
  private readonly auditLog: AuditLog;

  constructor(auditLog: AuditLog) {
    this.auditLog = auditLog;
  }

  createPayment(): PaymentGateway {
    return new AuditedPayment(new CashPayment(), this.auditLog);
  }

  createNotifiers(): Notifier[] {
    return [new ReceiptPrinter()];
  }
}
