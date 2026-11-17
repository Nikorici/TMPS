import type { TicketOrder } from "../domain/models.ts";
import { percentOf } from "../domain/money.ts";

const DAY_MS = 86_400_000;

export interface DiscountPolicy {
  readonly name: string;
  discount(order: TicketOrder, subtotal: number): number;
}

export class EarlyBirdDiscount implements DiscountPolicy {
  readonly name = "Early bird";
  private readonly daysBefore: number;
  private readonly percent: number;

  constructor(daysBefore = 30, percent = 20) {
    this.daysBefore = daysBefore;
    this.percent = percent;
  }

  discount(order: TicketOrder, subtotal: number): number {
    const daysLeft = (Date.parse(order.event.date) - Date.parse(order.orderedOn)) / DAY_MS;
    return daysLeft >= this.daysBefore ? percentOf(subtotal, this.percent) : 0;
  }
}

export class StudentDiscount implements DiscountPolicy {
  readonly name = "Student";
  private readonly percent: number;

  constructor(percent = 15) {
    this.percent = percent;
  }

  discount(order: TicketOrder, subtotal: number): number {
    return order.customer.isStudent ? percentOf(subtotal, this.percent) : 0;
  }
}

export class GroupDiscount implements DiscountPolicy {
  readonly name = "Group";
  private readonly minQuantity: number;
  private readonly percent: number;

  constructor(minQuantity = 5, percent = 10) {
    this.minQuantity = minQuantity;
    this.percent = percent;
  }

  discount(order: TicketOrder, subtotal: number): number {
    return order.quantity >= this.minQuantity ? percentOf(subtotal, this.percent) : 0;
  }
}

export class PriceQuote {
  readonly subtotal: number;
  readonly discounts: ReadonlyArray<readonly [string, number]>;
  readonly total: number;

  constructor(subtotal: number, discounts: ReadonlyArray<readonly [string, number]>, total: number) {
    this.subtotal = subtotal;
    this.discounts = discounts;
    this.total = total;
  }

  get savings(): number {
    return this.subtotal - this.total;
  }

  get capped(): boolean {
    return this.savings < this.discounts.reduce((sum, [, amount]) => sum + amount, 0);
  }
}

export class PriceCalculator {
  private readonly policies: readonly DiscountPolicy[];
  private readonly maxDiscountPercent: number;

  constructor(policies: readonly DiscountPolicy[], maxDiscountPercent = 30) {
    this.policies = policies;
    this.maxDiscountPercent = maxDiscountPercent;
  }

  quote(order: TicketOrder): PriceQuote {
    const subtotal = order.event.basePrice * order.quantity;
    const discounts = this.policies
      .map((policy) => [policy.name, policy.discount(order, subtotal)] as const)
      .filter(([, amount]) => amount > 0);
    const requested = discounts.reduce((sum, [, amount]) => sum + amount, 0);
    const total = subtotal - Math.min(requested, percentOf(subtotal, this.maxDiscountPercent));
    return new PriceQuote(subtotal, discounts, total);
  }
}
