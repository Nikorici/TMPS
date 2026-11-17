import type { Customer } from "../domain/models.ts";

export interface PaymentGateway {
  charge(customer: Customer, amount: number): Promise<string>;
}

export class CardPayment implements PaymentGateway {
  private issued = 0;

  async charge(_customer: Customer, _amount: number): Promise<string> {
    this.issued += 1;
    return `CARD-${String(this.issued).padStart(4, "0")}`;
  }
}

export class CashPayment implements PaymentGateway {
  private issued = 0;

  async charge(_customer: Customer, _amount: number): Promise<string> {
    this.issued += 1;
    return `CASH-${String(this.issued).padStart(4, "0")}`;
  }
}
