import type { Event, EventDetails } from "../domain/models.ts";

export class EventCatalog {
  private readonly templates = new Map<string, Event>();

  register(key: string, template: Event): void {
    this.templates.set(key, template);
  }

  edition(key: string, changes: Partial<EventDetails> = {}): Event {
    const template = this.templates.get(key);
    if (!template) throw new Error(`No event template "${key}"`);
    return template.clone(changes);
  }
}
