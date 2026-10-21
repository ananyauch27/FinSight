import re
from rapidfuzz import process, fuzz

NOISE_WORDS = {
    "UPI", "DR", "CR", "IMPS", "NEFT", "RTGS", "POS", "ECOM",
    "PUR", "TXN", "PAYMENT", "PAY", "TO", "FROM", "BY", "REF",
    "ATM", "WDL"
}

UPI_HANDLES = re.compile(
    r"@?(ok(axis|sbi|hdfcbank|icici)|ybl|paytm|ibl|axl|upi|apl)", re.I
)

ALIASES = {
    "BUNDL TECHNOLOGIES": "Swiggy",
    "SWIGGY": "Swiggy",
    "ZOMATO": "Zomato",
    "NETFLIX": "Netflix",
    "AMAZON PAY": "Amazon",
    "AMZN": "Amazon",
    "UBER": "Uber",
    "OLA": "Ola",
    "IRCTC": "IRCTC",
    "SPOTIFY": "Spotify",
    "JIO": "Jio",
    "AIRTEL": "Airtel",
    "BIGBASKET": "BigBasket",
    "BLINKIT": "Blinkit",
    "ZEPTO": "Zepto",
    "FLIPKART": "Flipkart",
}


def clean_description(raw: str) -> str:
    text = raw.upper()
    parts = re.split(r"[/|]", text)

    candidates = []

    for p in parts:
        p = p.strip()

        if not p:
            continue
        if re.fullmatch(r"[\d\W]+", p):
            continue
        if p in NOISE_WORDS:
            continue
        if UPI_HANDLES.fullmatch(p):
            continue

        candidates.append(p)

    if candidates:
        text = candidates[0]

    text = re.sub(r"\b\d{5,}\b", "", text)
    text = re.sub(r"[^A-Z0-9 &.\-]", " ", text)

    tokens = []

    for t in text.split():
        if t not in NOISE_WORDS:
            tokens.append(t)

    return " ".join(tokens).strip()


def match_user_alias(raw: str, alias_rows: list[tuple[str, list[str]]]) -> str | None:
    up = raw.upper()

    for name, aliases in alias_rows:
        for a in aliases:
            if a.strip() and a.upper() in up:
                return name

    return None


def to_merchant_name(
    raw: str,
    known_merchants: list[str] | None = None,
    user_alias_rows: list[tuple[str, list[str]]] | None = None
) -> str:

    if user_alias_rows:
        hit = match_user_alias(raw, user_alias_rows)

        if hit:
            return hit

    upper = raw.upper()

    for key, name in ALIASES.items():
        if key in upper:
            return name

    cleaned = clean_description(raw)

    if known_merchants and cleaned:
        match = process.extractOne(
            cleaned,
            known_merchants,
            scorer=fuzz.token_set_ratio
        )

        if match and match[1] >= 88:
            return match[0]

    return cleaned.title() or "Unknown"
