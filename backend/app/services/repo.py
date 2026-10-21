from sqlalchemy import or_
from app.models import Category, Merchant, Alert


def visible_categories(db, user_id):
    """Get system categories and this user's categories."""
    return db.query(Category).filter(
        or_(
            Category.user_id.is_(None),
            Category.user_id == user_id
        )
    ).all()


def category_map(db, user_id) -> dict[str, "UUID"]:
    """Map lowercase category names to IDs."""
    cats = visible_categories(db, user_id)

    # User categories override system categories with the same name.
    cats.sort(key=lambda c: c.user_id is not None)

    return {c.name.lower(): c.id for c in cats}


def get_or_create_merchant(db, user_id, name, cache: dict) -> Merchant:
    """Find a merchant in the cache or create a new one."""
    m = cache.get(name.lower())

    if m is None:
        m = Merchant(user_id=user_id, name=name)
        db.add(m)
        db.flush()
        cache[name.lower()] = m

    return m


def create_alert(db, user_id, type_, severity, title, message, transaction_id=None):
    """Add an alert to the database session."""
    alert = Alert(
        user_id=user_id,
        type=type_,
        severity=severity,
        title=title,
        message=message,
        transaction_id=transaction_id
    )

    db.add(alert)
