import pandas as pd
from decimal import Decimal, InvalidOperation
from .base import BaseParser, ParsedTxn


DATE_COLS = ["date", "txn date", "transaction date", "value date", "posting date"]
DESC_COLS = ["narration", "description", "particulars", "transaction remarks", "details"]
DEBIT_COLS = ["debit", "withdrawal", "withdrawal amt.", "dr", "debit amount"]
CREDIT_COLS = ["credit", "deposit", "deposit amt.", "cr", "credit amount"]
AMOUNT_COLS = ["amount"]
TYPE_COLS = ["type", "dr/cr", "cr/dr"]
BAL_COLS = ["balance", "closing balance", "running balance"]
REF_COLS = ["chq./ref.no.", "ref no", "reference", "utr", "chq/ref number"]


def _find(cols, candidates):
    for c in cols:
        if str(c).strip().lower() in candidates:
            return c
    return None


def _to_dec(v):
    if v is None or pd.isna(v):
        return None

    s = str(v).replace(",", "").replace("₹", "").strip()

    if s.lower() in ("", "-", "nan", "none"):
        return None

    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _clean(v):
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


class GenericTabularParser(BaseParser):
    bank_code = "generic"

    def can_parse(self, sample_text, filename):
        return filename.lower().endswith((".csv", ".xlsx", ".xls"))

    def _read_raw(self, path):
        if path.lower().endswith(".csv"):
            for enc in ("utf-8-sig", "cp1252", "latin-1"):
                try:
                    return pd.read_csv(
                        path, header=None, dtype=str,
                        skip_blank_lines=True,
                        on_bad_lines="skip",
                        encoding=enc, engine="python"
                    )
                except UnicodeDecodeError:
                    pass

            raise ValueError("Could not decode the CSV file")

        return pd.read_excel(path, header=None, dtype=str)

    def _find_header(self, raw):
        for i in range(min(30, len(raw))):
            row = [str(x).strip().lower() for x in raw.iloc[i]]

            if any(c in DATE_COLS for c in row) and any(c in DESC_COLS for c in row):
                df = raw.iloc[i + 1:].copy()
                df.columns = [str(x).strip() for x in raw.iloc[i]]
                return df.reset_index(drop=True)

        raise ValueError("Could not find a header row with date and description columns")

    def parse(self, path, password=None):
        raw = self._read_raw(path)
        df = self._find_header(raw)
        return self.parse_dataframe(df)

    def parse_dataframe(self, df) -> list[ParsedTxn]:
        cols = list(df.columns)

        c_date = _find(cols, DATE_COLS)
        c_desc = _find(cols, DESC_COLS)
        c_deb = _find(cols, DEBIT_COLS)
        c_cred = _find(cols, CREDIT_COLS)
        c_amt = _find(cols, AMOUNT_COLS)
        c_type = _find(cols, TYPE_COLS)
        c_bal = _find(cols, BAL_COLS)
        c_ref = _find(cols, REF_COLS)

        out = []

        for _, r in df.iterrows():
            desc = _clean(r[c_desc])
            d = pd.to_datetime(r[c_date], dayfirst=True, errors="coerce")

            if pd.isna(d) or not desc:
                continue

            amount = None
            direction = None

            if c_deb or c_cred:
                deb = _to_dec(r[c_deb]) if c_deb else None
                cred = _to_dec(r[c_cred]) if c_cred else None

                if deb is not None and deb > 0:
                    amount, direction = deb, "debit"
                elif cred is not None and cred > 0:
                    amount, direction = cred, "credit"

            elif c_amt:
                a = _to_dec(r[c_amt])

                if a is not None:
                    t = _clean(r[c_type]).lower() if c_type else ""

                    if t.startswith("cr"):
                        direction = "credit"
                    elif t.startswith("dr"):
                        direction = "debit"
                    else:
                        direction = "credit" if a > 0 else "debit"

                    amount = abs(a)

            if amount is None:
                continue

            out.append(
                ParsedTxn(
                    txn_date=d.date(),
                    description=desc,
                    amount=amount,
                    direction=direction,
                    balance=_to_dec(r[c_bal]) if c_bal else None,
                    reference=(_clean(r[c_ref]) or None) if c_ref else None,
                )
            )

        return out