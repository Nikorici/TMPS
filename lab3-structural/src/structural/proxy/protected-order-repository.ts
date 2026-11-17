import { AccessDenied } from "../../domain/errors.ts";
import type { Event, TicketOrder } from "../../domain/models.ts";
import type { OrderRepository } from "../../services/order-repository.ts";
import type { Role, StaffMember } from "./staff.ts";

type Operation = "save" | "find" | "all" | "ticketsSold";

const PERMISSIONS: Record<Role, ReadonlySet<Operation>> = {
  seller: new Set<Operation>(["save", "find", "ticketsSold"]),
  organizer: new Set<Operation>(["save", "find", "all", "ticketsSold"]),
};

export class ProtectedOrderRepository implements OrderRepository {
  private readonly real: OrderRepository;
  private readonly staff: StaffMember;

  constructor(real: OrderRepository, staff: StaffMember) {
    this.real = real;
    this.staff = staff;
  }

  save(order: TicketOrder): TicketOrder {
    this.authorize("save");
    return this.real.save(order);
  }

  find(id: number): TicketOrder | undefined {
    this.authorize("find");
    return this.real.find(id);
  }

  all(): readonly TicketOrder[] {
    this.authorize("all");
    return this.real.all();
  }

  ticketsSold(event: Event): number {
    this.authorize("ticketsSold");
    return this.real.ticketsSold(event);
  }

  private authorize(operation: Operation): void {
    if (!PERMISSIONS[this.staff.role].has(operation)) {
      throw new AccessDenied(`${this.staff.name} (${this.staff.role}) may not call ${operation}() on orders`);
    }
  }
}
