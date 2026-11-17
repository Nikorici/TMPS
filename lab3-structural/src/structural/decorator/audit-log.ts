export interface AuditEntry {
  readonly reference: string;
  readonly customer: string;
  readonly amount: number;
}

export class AuditLog {
  private readonly entries: AuditEntry[] = [];

  record(entry: AuditEntry): void {
    this.entries.push(entry);
  }

  list(): readonly AuditEntry[] {
    return [...this.entries];
  }
}
