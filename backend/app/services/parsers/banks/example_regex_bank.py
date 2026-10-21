import re
LINE = re.compile(r"^(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$")
# groups: date, narration, amount, balance
# Decide debit vs credit by comparing this balance to the previous row's balance.