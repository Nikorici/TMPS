import type { TicketOrder } from "../domain/models.ts";
import { formatMdl } from "../domain/money.ts";
import type { PriceQuote } from "./pricing.ts";

export class ReceiptFormatter {
  format(order: TicketOrder, quote: PriceQuote): string {
    const { event } = order;
    const lines = [
      `Order #${order.id} confirmed: ${order.quantity} x ${event.name}, ${event.venue}, ${event.date}`,
      `  Subtotal: ${formatMdl(quote.subtotal)}`,
      ...quote.discounts.map(([name, amount]) => `  ${name} discount: -${formatMdl(amount)}`),
    ];
    if (quote.capped) lines.push(`  Discounts capped at -${formatMdl(quote.savings)}`);
    lines.push(`  Total paid: ${formatMdl(quote.total)}`, `  Payment reference: ${order.paymentReference}`);
    return lines.join("\n");
  }
}
