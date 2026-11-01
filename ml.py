import heapq
import json
import os
import sqlite3

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "metrics.json")

FEATURES = ["bedtime_num", "sleep_hours", "study_hours",
            "exercise_minutes", "screen_hours"]
TARGET = "productivity_score"

LABELS = {
    "bedtime_num": "Later bedtime",
    "sleep_hours": "Sleep hours",
    "study_hours": "Study hours",
    "exercise_minutes": "Exercise minutes",
    "screen_hours": "Screen hours",
}

NUDGES = {
    "bedtime_num": (-1.0, "Go to bed 1 hour earlier"),
    "sleep_hours": (1.0, "Sleep 1 hour more"),
    "study_hours": (1.0, "Study 1 hour more"),
    "exercise_minutes": (20, "Exercise 20 minutes more"),
    "screen_hours": (-1.0, "Cut screen time by 1 hour"),
}


def load_data():
    conn = sqlite3.connect(database.DB_PATH)
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY entry_date", conn)
    conn.close()
    return df


def train_and_save():
    df = load_data()
    if len(df) < 20:
        return None, f"Need at least 20 entries to train (you have {len(df)})."

    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    candidates = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
    }

    results = {}
    best_name, best_model, best_mae = None, None, None
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        results[name] = {"mae": round(mae, 3), "r2": round(r2, 3)}
        if best_mae is None or mae < best_mae:
            best_name, best_model, best_mae = name, model, mae

    best_model.fit(X, y)
    joblib.dump(best_model, MODEL_PATH)

    info = {"best": best_name, "results": results, "rows": len(df)}
    with open(METRICS_PATH, "w") as f:
        json.dump(info, f)
    return info, None


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)


def load_metrics():
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH) as f:
        return json.load(f)


def predict(model, state):
    row = pd.DataFrame([{f: float(state[f]) for f in FEATURES}])
    value = float(model.predict(row)[0])
    return round(min(10.0, max(1.0, value)), 1)


def recommend(model, state, k=3):
    base = predict(model, state)
    impacts = []
    for feature, (change, text) in NUDGES.items():
        changed = {f: float(state[f]) for f in FEATURES}
        changed[feature] = max(0.0, changed[feature] + change)
        gain = round(predict(model, changed) - base, 2)
        impacts.append((gain, text))
    top = heapq.nlargest(k, impacts)
    return [item for item in top if item[0] > 0]


def correlations():
    df = load_data()
    if len(df) < 5:
        return {}
    corr = df[FEATURES + [TARGET]].corr()[TARGET].drop(TARGET)
    corr = corr.dropna()
    ordered = corr.sort_values(key=abs, ascending=False)
    return {LABELS[name]: round(float(v), 2) for name, v in ordered.items()}


if __name__ == "__main__":
    info, error = train_and_save()
    if error:
        print(error)
    else:
        print("Rows used:", info["rows"])
        for name, r in info["results"].items():
            print(f"{name}: MAE={r['mae']}  R2={r['r2']}")
        print("Best model:", info["best"])
        print("\nCorrelation with productivity:")
        for label, value in correlations().items():
            print(f"  {label}: {value}")