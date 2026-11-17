import type { Event, TicketOrder } from "../domain/models.ts";

export interface OrderRepository {
  save(order: TicketOrder): TicketOrder;
  find(id: number): TicketOrder | undefined;
  all(): readonly TicketOrder[];
  ticketsSold(event: Event): number;
}

export class InMemoryOrderRepository implements OrderRepository {
  private readonly orders = new Map<number, TicketOrder>();
  private nextId = 1;

  save(order: TicketOrder): TicketOrder {
    if (order.id === null) order.id = this.nextId++;
    this.orders.set(order.id, order);
    return order;
  }

  find(id: number): TicketOrder | undefined {
    return this.orders.get(id);
  }

  all(): readonly TicketOrder[] {
    return [...this.orders.values()];
  }

  ticketsSold(event: Event): number {
    let sold = 0;
    for (const order of this.orders.values()) if (order.event === event) sold += order.quantity;
    return sold;
  }
}
