import { SoldOut } from "../domain/errors.ts";
import { type Customer, type Event, TicketOrder } from "../domain/models.ts";
import type { Notifier } from "./notifications.ts";
import type { OrderRepository } from "./order-repository.ts";
import type { PaymentGateway } from "./payments.ts";
import type { PriceCalculator } from "./pricing.ts";
import type { ReceiptFormatter } from "./receipts.ts";

export class BookingService {
  private readonly calculator: PriceCalculator;
  private readonly payments: PaymentGateway;
  private readonly repository: OrderRepository;
  private readonly notifiers: readonly Notifier[];
  private readonly receipts: ReceiptFormatter;

  constructor(
    calculator: PriceCalculator,
    payments: PaymentGateway,
    repository: OrderRepository,
    notifiers: readonly Notifier[],
    receipts: ReceiptFormatter,
  ) {
    this.calculator = calculator;
    this.payments = payments;
    this.repository = repository;
    this.notifiers = notifiers;
    this.receipts = receipts;
  }

  async book(event: Event, customer: Customer, quantity: number, orderedOn: string): Promise<TicketOrder> {
    const order = new TicketOrder(event, customer, quantity, orderedOn);
    const seatsLeft = event.capacity - this.repository.ticketsSold(event);
    if (quantity > seatsLeft) {
      throw new SoldOut(`${event.name}, ${event.venue}: ${seatsLeft} seats left, ${quantity} requested`);
    }
    const quote = this.calculator.quote(order);
    order.paymentReference = await this.payments.charge(customer, quote.total);
    order.total = quote.total;
    const saved = this.repository.save(order);
    const receipt = this.receipts.format(saved, quote);
    for (const notifier of this.notifiers) await notifier.send(customer, receipt);
    return saved;
  }
}
