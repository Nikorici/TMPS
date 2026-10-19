from ticketing.models import TicketOrder
from ticketing.pricing import PriceQuote


class ReceiptFormatter:
    def format(self, order: TicketOrder, quote: PriceQuote) -> str:
        lines = [
            f"Order #{order.id} confirmed: {order.quantity} x {order.event.name} on {order.event.date:%d.%m.%Y}",
            f"  Subtotal: {quote.subtotal} MDL",
        ]
        lines += [f"  {name} discount: -{amount} MDL" for name, amount in quote.discounts]
        if quote.capped:
            lines.append(f"  Discounts capped at -{quote.savings} MDL")
        lines += [
            f"  Total paid: {quote.total} MDL",
            f"  Payment reference: {order.payment_reference}",
        ]
        return "\n".join(lines)
