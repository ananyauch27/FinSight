# app/models/category.py
import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_category_user_name"),
        Index("uq_system_category", "name", unique=True, postgresql_where=text("user_id IS NULL")),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(60))
    icon: Mapped[str | None] = mapped_column(String(30))
    color: Mapped[str | None] = mapped_column(String(9))
    kind: Mapped[str] = mapped_column(String(10), default="expense")   # expense|income|transfer