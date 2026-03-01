import enum
from datetime import datetime, timezone
from sqlalchemy import String, Enum, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    APPLICANT = "APPLICANT"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.APPLICANT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Prediction(Base):
    """
    Stores one row per ML prediction request.

    Demographic columns (gender, property_area) are captured at prediction time
    from the submitted loan application payload so the /system/fairness endpoint
    can compute real group-level approval rates (Disparate Impact / Four-Fifths Rule).
    Without these columns the fairness endpoint would have no choice but to return
    static baseline numbers, which is misleading.
    """
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    applicant_id: Mapped[int] = mapped_column(index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=True)
    model_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    explanation_summary: Mapped[str] = mapped_column(String, nullable=True)
    inference_time_ms: Mapped[float] = mapped_column(nullable=False)

    # Demographic fields — required for real fairness metric computation.
    # Nullable so existing DB rows (pre-migration) remain valid.
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    property_area: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
