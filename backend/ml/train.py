from pathlib import Path
import pandas as pd, joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "seed_training_data.csv", encoding="utf-8-sig")

X_train, X_test, y_train, y_test = train_test_split(
    df.description.str.lower(), df.category, test_size=0.2, stratify=df.category, random_state=42)

model = Pipeline([
    ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))),
    ("clf", LogisticRegression(max_iter=2000, C=5)),
])
model.fit(X_train, y_train)
print(classification_report(y_test, model.predict(X_test)))   # screenshot this for your README
joblib.dump(model, HERE / "model.joblib")