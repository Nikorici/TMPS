import type { Customer } from "../../domain/models.ts";
import type { PaymentGateway } from "../../services/payments.ts";
import type { AuditLog } from "./audit-log.ts";
import { PaymentDecorator } from "./payment-decorator.ts";

export class AuditedPayment extends PaymentDecorator {
  private readonly log: AuditLog;

  constructor(wrapped: PaymentGateway, log: AuditLog) {
    super(wrapped);
    this.log = log;
  }

  override async charge(customer: Customer, amount: number): Promise<string> {
    const reference = await super.charge(customer, amount);
    this.log.record({ reference, customer: customer.name, amount });
    return reference;
  }
}
