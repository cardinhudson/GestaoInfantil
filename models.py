"""Data structures used by the services layer.

These lightweight dataclasses replace the previous SQLAlchemy models so that the
rest of the application can continue to interact with plain Python objects even
though persistence is now handled via the sqlite3 module directly.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: Optional[str]
    roles: str
    password_hash: Optional[str]
    photo: Optional[str]


@dataclass
class Conversion:
    id: int
    money_per_point: float
    hours_per_point: float


@dataclass
class Task:
    id: int
    name: str
    points: float
    conversion_type: str
    child_id: int
    submitted_by_id: int
    validator_id: Optional[int]
    validated: bool
    created_at: str
    validated_at: Optional[str]


@dataclass
class Debit:
    id: int
    user_id: int
    points_deducted: int
    money_amount: Optional[float]
    hours_amount: Optional[float]
    reason: Optional[str]
    performed_by_id: int
    created_at: str
