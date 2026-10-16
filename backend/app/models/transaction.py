# app/models/transaction.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (String, Text, Numeric, Boolean, Date, DateTime, Float, ForeignKey,
                        UniqueConstraint, CheckConstraint, Index, func)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "dedupe_hash", name="uq_txn_dedupe"),
        CheckConstraint("amount >= 0", name="ck_txn_amount"),
        CheckConstraint("direction IN ('debit','credit')", name="ck_txn_direction"),
        CheckConstraint("splits IS NULL OR jsonb_typeof(splits) = 'array'", name="splits_is_array"),
        Index("idx_txn_user_date", "user_id", "txn_date"),
        Index("idx_txn_user_category", "user_id", "category_id"),
        Index("idx_txn_user_merchant", "user_id", "merchant_id"),
        Index("idx_txn_tags", "tags", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    upload_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("uploads.id", ondelete="SET NULL"))
    txn_date: Mapped[date] = mapped_column(Date)
    raw_description: Mapped[str] = mapped_column(Text)
    clean_description: Mapped[str | None] = mapped_column(Text)
    merchant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("merchants.id", ondelete="SET NULL"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    direction: Mapped[str] = mapped_column(String(6))
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    reference_no: Mapped[str | None] = mapped_column(String(60))
    category_source: Mapped[str] = mapped_column(String(12), default="auto", server_default="auto")
    category_conf: Mapped[float | None] = mapped_column(Float)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, server_default="{}")
    # none_as_null=True: Python None is stored as SQL NULL (not JSON 'null'), so "splits IS NULL" works
    splits: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))
    dedupe_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    merchant = relationship("Merchant")
    category = relationship("Category")