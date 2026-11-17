export interface Customer {
  readonly name: string;
  readonly email: string;
  readonly phone: string;
  readonly isStudent: boolean;
}

export interface EventDetails {
  readonly name: string;
  readonly date: string;
  readonly basePrice: number;
  readonly venue: string;
  readonly capacity: number;
}

export class Event implements EventDetails {
  readonly name: string;
  readonly date: string;
  readonly basePrice: number;
  readonly venue: string;
  readonly capacity: number;

  constructor(details: EventDetails) {
    if (!details.name.trim()) throw new Error("An event needs a name");
    if (Number.isNaN(Date.parse(details.date))) throw new Error(`Invalid event date: ${details.date}`);
    if (!Number.isInteger(details.basePrice) || details.basePrice < 0) throw new Error("Ticket price cannot be negative");
    if (!Number.isInteger(details.capacity) || details.capacity < 1) throw new Error("An event needs at least one seat");
    this.name = details.name;
    this.date = details.date;
    this.basePrice = details.basePrice;
    this.venue = details.venue;
    this.capacity = details.capacity;
  }

  clone(changes: Partial<EventDetails> = {}): Event {
    return new Event({ ...this, ...changes });
  }
}

export class TicketOrder {
  readonly event: Event;
  readonly customer: Customer;
  readonly quantity: number;
  readonly orderedOn: string;
  id: number | null = null;
  total = 0;
  paymentReference: string | null = null;

  constructor(event: Event, customer: Customer, quantity: number, orderedOn: string) {
    if (!Number.isInteger(quantity) || quantity < 1) throw new Error("An order needs at least one ticket");
    if (orderedOn > event.date) throw new Error("Tickets cannot be ordered after the event");
    this.event = event;
    this.customer = customer;
    this.quantity = quantity;
    this.orderedOn = orderedOn;
  }
}
