# app/models/plan.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (String, Date, DateTime, Numeric, ForeignKey, CheckConstraint,
                        Index, func, text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("kind IN ('budget','goal')", name="ck_plan_kind"),
        CheckConstraint("amount > 0", name="ck_plan_amount"),
        CheckConstraint(
            "(kind = 'budget' AND category_id IS NOT NULL) OR (kind = 'goal' AND name IS NOT NULL)",
            name="plan_shape"),
        Index("uq_budget_per_category", "user_id", "category_id", "period",
              unique=True, postgresql_where=text("kind = 'budget'")),
        Index("idx_plans_user_kind", "user_id", "kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(10))                 # 'budget' | 'goal'
    name: Mapped[str | None] = mapped_column(String(120))
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))       # budget limit OR goal target
    saved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    period: Mapped[str] = mapped_column(String(10), default="monthly")
    target_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())