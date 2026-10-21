from app.models import Merchant, Category,Transaction

def load_user_rules(db, user_id) -> dict[str, str]:
    """Load the user's saved merchant category rules."""

    rows = (
        db.query(Merchant.name, Category.name)
        .join(Category, Merchant.default_category_id == Category.id)
        .filter(
            Merchant.user_id == user_id,
            Merchant.category_locked.is_(True)
        )
    )
    return {m.lower(): c for m, c in rows}


def lock_merchant_category(db, user_id, merchant, 
                           category_id, exclude_txn_id = None):
    """Save the category rule and update other matching transactions."""
    
    merchant.default_category_id = category_id
    merchant.category_locked = True
    q = db.query(Transaction).filter
    ( Transaction.user_id == user_id,
      Transaction.merchant_id == merchant.id, 
      Transaction.category_source != "user" 
    ) 
    
    if exclude_txn_id:
         q = q.filter(Transaction.id != exclude_txn_id) 
         
    q.update( 
        {
             "category_id": category_id, 
             "category_source": "rule",
               "category_conf": 1.0 
        }, 
        synchronize_session=False
    )

def apply_correction(db, user, txn,
                      category_id, apply_to_similar: bool):
       """Correct a category and optionally remember the choice."""
     
       txn.category_id = category_id
       txn.category_source = "user" 
       txn.category_conf = 1.0 
       
       if apply_to_similar and txn.merchant_id:
         m = db.get(Merchant, txn.merchant_id) 
         
         lock_merchant_category(
              db, user.id, m, category_id,
                exclude_txn_id=txn.id 
                )
         
         db.commit()