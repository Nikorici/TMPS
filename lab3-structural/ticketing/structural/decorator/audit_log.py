from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AuditEntry:
    reference: str
    customer: str
    amount: Decimal


class AuditLog:
    def __init__(self):
        self._entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> list[AuditEntry]:
        return list(self._entries)
