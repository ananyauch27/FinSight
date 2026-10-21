import hashlib


def make_hash(account_id, txn) -> str:
    key = "|".join([
        str(account_id),
        txn.txn_date.isoformat(),
        str(txn.amount),
        txn.direction,
        " ".join(txn.description.upper().split()),
        str(txn.balance or "")
    ])

    return hashlib.sha256(key.encode("utf-8")).hexdigest()
