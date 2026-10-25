
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import Category, Merchant, User
from app.services.repo import visible_categories
from app.services.rules import lock_merchant_category

router = APIRouter(tags=["categories"])


# Input for creating a category rule
class RuleIn(BaseModel):
    merchant_name: str = Field(min_length=1, max_length=120)
    aliases: list[str] = []
    category_id: UUID


# Get all visible categories
@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    categories = visible_categories(db, user.id)

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "kind": c.kind,
            "icon": c.icon,
            "color": c.color,
            "is_system": c.user_id is None,
        }
        for c in categories
    ]


# Get all category rules
@router.get("/category-rules")
def list_rules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    merchants = (
        db.query(Merchant)
        .filter(
            Merchant.user_id == user.id,
            Merchant.category_locked.is_(True),
        )
        .all()
    )

    return [
        {
            "id": str(m.id),
            "merchant": m.name,
            "aliases": m.aliases,
            "category": m.default_category.name if m.default_category else None,
        }
        for m in merchants
    ]


# Create a category rule
@router.post("/category-rules", status_code=201)
def create_rule(
    body: RuleIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Check whether the category is available to the user
    category = (
        db.query(Category)
        .filter(
            Category.id == body.category_id,
            or_(
                Category.user_id.is_(None),
                Category.user_id == user.id,
            ),
        )
        .first()
    )

    if not category:
        raise HTTPException(422, "Unknown category")

    # Find or create the merchant
    name = body.merchant_name.strip().title()

    merchant = (
        db.query(Merchant)
        .filter_by(user_id=user.id, name=name)
        .first()
    )

    if not merchant:
        merchant = Merchant(user_id=user.id, name=name)
        db.add(merchant)
        db.flush()

    # Add new aliases without duplicates
    aliases = merchant.aliases or []
    aliases.extend(
        alias.strip().lower()
        for alias in body.aliases
        if alias.strip()
    )
    merchant.aliases = sorted(set(aliases))

    # Save the category rule
    lock_merchant_category(
        db,
        user.id,
        merchant,
        category.id,
    )

    db.commit()

    return {
        "id": str(merchant.id),
        "merchant": merchant.name,
        "aliases": merchant.aliases,
        "category": category.name,
    }


# Delete a category rule
@router.delete("/category-rules/{merchant_id}", status_code=204)
def delete_rule(
    merchant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    merchant = (
        db.query(Merchant)
        .filter_by(id=merchant_id, user_id=user.id)
        .first()
    )

    if not merchant:
        raise HTTPException(404, "Rule not found")

    merchant.category_locked = False
    db.commit()
