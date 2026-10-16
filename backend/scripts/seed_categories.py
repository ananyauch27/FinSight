from app.database import Sessionlocal
from app.models import Category

EXPENSE = ["Food & Dining","Groceries","Transport","Fuel","Shopping","Entertainment","Subscriptions",
           "Bills & Utilities","Rent","EMI & Loans","Health","Education","Travel","Insurance",
           "Investments","Personal Care","Gifts & Donations","Fees & Charges","Uncategorized"]
INCOME = ["Salary","Interest","Refund","Other Income"]
TRANSFER = ["Self Transfer","Credit Card Payment"]

def main():
    db = Sessionlocal()
    existing = {c.name for c in db.query(Category).filter(Category.user_id.is_(None))}
    for kind, names in (("expense", EXPENSE), ("income", INCOME), ("transfer", TRANSFER)):
        for n in names:
            if n not in existing:
                db.add(Category(user_id=None, name=n, kind=kind))
    db.commit(); db.close()
    print("Categories seeded.")

if __name__ == "__main__":
    main()