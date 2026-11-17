import type { Customer } from "../../domain/models.ts";
import type { PaymentGateway } from "../../services/payments.ts";

export abstract class PaymentDecorator implements PaymentGateway {
  protected readonly wrapped: PaymentGateway;

  constructor(wrapped: PaymentGateway) {
    this.wrapped = wrapped;
  }

  charge(customer: Customer, amount: number): Promise<string> {
    return this.wrapped.charge(customer, amount);
  }
}
