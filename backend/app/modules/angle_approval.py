from enum import StrEnum


class AngleStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
