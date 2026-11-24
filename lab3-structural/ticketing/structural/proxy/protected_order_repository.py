from ticketing.domain.errors import AccessDenied
from ticketing.domain.models import Event, TicketOrder
from ticketing.services.repository import OrderRepository
from ticketing.structural.proxy.staff import Role, StaffMember

PERMISSIONS = {
    Role.SELLER: {"save", "find", "tickets_sold"},
    Role.ORGANIZER: {"save", "find", "all", "tickets_sold"},
}


class ProtectedOrderRepository(OrderRepository):
    def __init__(self, real: OrderRepository, staff: StaffMember):
        self._real = real
        self._staff = staff

    def save(self, order: TicketOrder) -> TicketOrder:
        self._authorize("save")
        return self._real.save(order)

    def find(self, order_id: int) -> TicketOrder | None:
        self._authorize("find")
        return self._real.find(order_id)

    def all(self) -> list[TicketOrder]:
        self._authorize("all")
        return self._real.all()

    def tickets_sold(self, event: Event) -> int:
        self._authorize("tickets_sold")
        return self._real.tickets_sold(event)

    def _authorize(self, operation: str) -> None:
        if operation not in PERMISSIONS[self._staff.role]:
            raise AccessDenied(f"{self._staff.name} ({self._staff.role.value}) may not call {operation}() on orders")
