import { Event } from "../domain/models.ts";
import { mdl } from "../domain/money.ts";

export class EventBuilder {
  private name: string | null = null;
  private date: string | null = null;
  private basePrice: number | null = null;
  private venue = "To be announced";
  private capacity = 100;

  named(name: string): this {
    this.name = name;
    return this;
  }

  on(date: string): this {
    this.date = date;
    return this;
  }

  at(venue: string): this {
    this.venue = venue;
    return this;
  }

  pricedAt(amountMdl: number): this {
    this.basePrice = mdl(amountMdl);
    return this;
  }

  withCapacity(seats: number): this {
    this.capacity = seats;
    return this;
  }

  build(): Event {
    const missing = Object.entries({ name: this.name, date: this.date, price: this.basePrice })
      .filter(([, value]) => value === null)
      .map(([step]) => step);
    if (missing.length > 0) throw new Error(`Event is missing: ${missing.join(", ")}`);
    return new Event({
      name: this.name!,
      date: this.date!,
      basePrice: this.basePrice!,
      venue: this.venue,
      capacity: this.capacity,
    });
  }
}
