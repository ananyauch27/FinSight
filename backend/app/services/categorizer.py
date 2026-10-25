import joblib
from pathlib import Path

KEYWORDS = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "dominos", "mcdonald", "kfc", "starbucks"],
    "Groceries": ["bigbasket", "blinkit", "zepto", "dmart", "grofers", "reliance fresh"],
    "Transport": ["uber", "ola", "rapido", "irctc", "metro", "redbus"],
    "Fuel": ["petrol", "hpcl", "bpcl", "iocl", "indian oil", "shell"],
    "Subscriptions": ["netflix", "spotify", "prime video", "hotstar", "youtube premium", "icloud", "google one"],
    "Bills & Utilities": ["electricity", "jio", "airtel", "vodafone", "bsnl", "broadband", "gas bill", "water bill"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho"],
    "Health": ["pharmacy", "apollo", "medplus", "hospital", "clinic", "1mg", "pharmeasy"],
    "Salary": ["salary", "payroll"],
    "Interest": ["interest credit", "int.pd", "interest paid"],
    "Rent": ["rent"],
    "EMI & Loans": ["emi", "loan"],
    "Fees & Charges": ["charges", "gst", "annual fee", "sms charges"],
    "Investments": ["zerodha", "groww", "mutual fund", "sip", "upstox"],
}

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "model.joblib"
_model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None

def categorize(merchant: str, clean_desc: str, user_rules: dict[str, str]):
    """Returns (category_name, source, confidence)."""
    m = merchant.lower()
    if m in user_rules:
        return user_rules[m], "rule", 1.0

    text = f"{merchant} {clean_desc}".lower()
    for cat, words in KEYWORDS.items():
        if any(w in text for w in words):
            return cat, "rule", 0.95

    if _model is not None:
        probs = _model.predict_proba([text])[0]
        i = probs.argmax()
        if probs[i] >= 0.6:
            return str(_model.classes_[i]), "ml", float(probs[i])

    return "Uncategorized", "auto", 0.0