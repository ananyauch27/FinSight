import pandas as pd
from app.services.parsers.generic_csv import GenericTabularParser

# Sample bank statement data
df = pd.DataFrame({
    "Date": ["15-10-2026", "16-10-2026", "17-10-2026"],
    "Description": ["Grocery Store", "Salary", "Bus Ticket"],
    "Debit": ["500", "0", "50"],
    "Credit": ["0", "20000", "0"],
    "Balance": ["9500", "29500", "29450"]
})

# Create parser
parser = GenericTabularParser()

# Parse the sample data
transactions = parser.parse_dataframe(df)

# Display results
print("Total transactions:", len(transactions))

for txn in transactions:
    print("--------------------")
    print("Date:", txn.txn_date)
    print("Description:", txn.description)
    print("Amount:", txn.amount)
    print("Direction:", txn.direction)
    print("Balance:", txn.balance)

# Basic test
assert len(transactions) == 3
assert transactions[0].direction == "debit"
assert transactions[1].direction == "credit"
assert transactions[2].amount == 50

print("\nAll tests passed!")
