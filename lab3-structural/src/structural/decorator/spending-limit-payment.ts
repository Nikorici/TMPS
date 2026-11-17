import { PaymentDeclined } from "../../domain/errors.ts";
import type { Customer } from "../../domain/models.ts";
import { formatMdl } from "../../domain/money.ts";
import type { PaymentGateway } from "../../services/payments.ts";
import { PaymentDecorator } from "./payment-decorator.ts";

export class SpendingLimitPayment extends PaymentDecorator {
  private readonly limit: number;

  constructor(wrapped: PaymentGateway, limit: number) {
    super(wrapped);
    this.limit = limit;
  }

  override async charge(customer: Customer, amount: number): Promise<string> {
    if (amount > this.limit) {
      throw new PaymentDeclined(`card payments are limited to ${formatMdl(this.limit)} per order, got ${formatMdl(amount)}`);
    }
    return super.charge(customer, amount);
  }
}
