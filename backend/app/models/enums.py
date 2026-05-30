from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    STAFF = "staff"


class PreferredShift(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"
    FLEXIBLE = "flexible"


class DutyType(str, Enum):
    EMERGENCY_MORNING = "Emergency Morning"
    EMERGENCY_EVENING = "Emergency Evening"
    EMERGENCY_NIGHT = "Emergency Night"
    INDOOR_MORNING = "Indoor Morning"
    INDOOR_NIGHT = "Indoor Night"
    OUTDOOR = "Outdoor"


class ShiftType(str, Enum):
    MORNING = "morning"
    EVENING = "evening"
    NIGHT = "night"
    OUTDOOR = "outdoor"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeaveType(str, Enum):
    CASUAL = "casual"
    SICK = "sick"
    EARNED = "earned"
    TRAINING = "training"
    OTHER = "other"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SYSTEM = "system"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [item.value for item in enum_cls]
