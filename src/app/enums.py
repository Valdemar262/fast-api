from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    ADMIN = "admin"


class StatementStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class StatusTransitionType(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
