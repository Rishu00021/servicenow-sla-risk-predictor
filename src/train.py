"""Train the SLA-breach classifier and save metrics + charts.

Model: Pipeline(TfidfVectorizer -> LogisticRegression) on the ticket
text (description + category + subcategory + priority + group + channel).
Real train/test split, stratified. Saves the pipeline with joblib,
metrics to results/metrics.json, and charts to docs/.
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
DOCS_DIR = ROOT / "docs"


def make_text(df: pd.DataFrame) -> pd.Series:
    return (df["short_description"] + " " + df["category"] + " "
            + df["subcategory"] + " " + df["priority"] + " "
            + df["assignment_group"] + " " + df["channel"])


def main() -> None:
    df = pd.read_csv(DATA_DIR / "tickets.csv")
    X = make_text(df)
    y = df["sla_breach"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "n_tickets": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "breach_rate": round(float(y.mean()), 4),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS_DIR / "sla_breach_model.joblib")
    (RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))

    # Chart 1: breach rate by priority
    rates = df.groupby("priority")["sla_breach"].mean().reindex(["P1", "P2", "P3", "P4"]) * 100
    fig, ax = plt.subplots(figsize=(7, 4))
    rates.plot(kind="bar", ax=ax, color="#d9534f")
    ax.set_ylabel("SLA breach rate (%)")
    ax.set_title("SLA breach rate by priority (synthetic data)")
    ax.set_ylim(0, max(rates) * 1.15)
    fig.tight_layout()
    fig.savefig(DOCS_DIR / "breach_rate_by_priority.png", dpi=150)
    plt.close(fig)

    # Chart 2: top TF-IDF features driving breach risk (log-reg coefficients)
    vec = model.named_steps["tfidf"]
    coef = model.named_steps["clf"].coef_[0]
    feats = pd.Series(coef, index=vec.get_feature_names_out())
    top = feats.sort_values(ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(7, 4))
    top.sort_values().plot(kind="barh", ax=ax, color="#337ab7")
    ax.set_xlabel("Logistic regression coefficient (higher = more breach risk)")
    ax.set_title("Top features predicting SLA breach")
    fig.tight_layout()
    fig.savefig(DOCS_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)
    print("Saved model, metrics.json and charts to docs/")


if __name__ == "__main__":
    main()
