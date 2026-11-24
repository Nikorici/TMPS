from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    SELLER = "seller"
    ORGANIZER = "organizer"


@dataclass(frozen=True)
class StaffMember:
    name: str
    role: Role
