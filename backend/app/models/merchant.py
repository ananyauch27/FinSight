# app/models/merchant.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (String, Boolean, Integer, Date, DateTime, Numeric, ForeignKey,
                        UniqueConstraint, Index, func, text)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_merchant_user_name"),
        Index("idx_merchants_name_trgm", "name", postgresql_using="gin",
              postgresql_ops={"name": "gin_trgm_ops"}),
        Index("idx_merchants_recurring", "user_id",
              postgresql_where=text("recurring_frequency IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, server_default="{}")

    # category rule
    default_category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    category_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    # recurring series (NULL frequency = not recurring)
    recurring_frequency: Mapped[str | None] = mapped_column(String(12))
    typical_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    last_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    last_date: Mapped[date | None] = mapped_column(Date)
    next_expected: Mapped[date | None] = mapped_column(Date)
    occurrences: Mapped[int] = mapped_column(Integer, default=0)
    recurring_status: Mapped[str] = mapped_column(String(10), default="active")
    price_changed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    default_category = relationship("Category", foreign_keys=[default_category_id])