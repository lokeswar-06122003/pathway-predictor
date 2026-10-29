"""Train the stream model and save it, plus the numbers shown on the website.

Run:  python train_model.py
Writes into model/:
  stream_model.pkl, gender_encoder.pkl, stream_encoder.pkl  - the model
  model_info.json                                           - stats for the UI
"""
import json
import os

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "dataset", "fully_cleaned_student_pathway_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

FEATURES = ["Gender", "Math_Marks", "Science_Marks", "Arts_Marks", "Study_Hours_Per_Week"]


def make_model():
    # class_weight='balanced' stops the model from simply favouring the
    # bigger "Technical" class.
    return RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42
    )


def build_info(df, model, cv_accuracy, test_accuracy, baseline):
    """Numbers the website shows: averages per stream and model facts."""
    averages = {}
    for stream, group in df.groupby("Recommended_Stream"):
        averages[stream] = {
            "Math_Marks": round(group["Math_Marks"].mean(), 1),
            "Science_Marks": round(group["Science_Marks"].mean(), 1),
            "Arts_Marks": round(group["Arts_Marks"].mean(), 1),
            "Study_Hours_Per_Week": round(group["Study_Hours_Per_Week"].mean(), 1),
            "count": int(len(group)),
        }
    return {
        "algorithm": "Random Forest",
        "trees": model.n_estimators,
        "records": int(len(df)),
        "cv_accuracy": round(cv_accuracy * 100, 1),
        "test_accuracy": round(test_accuracy * 100, 1),
        "baseline_accuracy": round(baseline * 100, 1),
        "feature_importance": {
            f: round(float(v) * 100, 1) for f, v in zip(FEATURES, model.feature_importances_)
        },
        "averages": averages,
    }


def train_balanced_model():
    df = pd.read_csv(DATA_PATH).drop(columns=["RollNo"])

    le_gender = LabelEncoder()
    le_stream = LabelEncoder()
    X = df[FEATURES].copy()
    X["Gender"] = le_gender.fit_transform(X["Gender"])
    y = le_stream.fit_transform(df["Recommended_Stream"])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    cv_accuracy = cross_val_score(make_model(), X, y, cv=5).mean()
    baseline = DummyClassifier().fit(X_train, y_train).score(X_test, y_test)

    model = make_model().fit(X_train, y_train)
    test_accuracy = model.score(X_test, y_test)

    print(f"5-fold CV accuracy : {cv_accuracy * 100:.1f}%")
    print(f"Test accuracy      : {test_accuracy * 100:.1f}%")
    print(f"Always-'Technical' : {baseline * 100:.1f}%  (baseline to beat)")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "stream_model.pkl"))
    joblib.dump(le_gender, os.path.join(MODEL_DIR, "gender_encoder.pkl"))
    joblib.dump(le_stream, os.path.join(MODEL_DIR, "stream_encoder.pkl"))

    info = build_info(df, model, cv_accuracy, test_accuracy, baseline)
    with open(os.path.join(MODEL_DIR, "model_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    print("Saved model and model_info.json to", MODEL_DIR)


if __name__ == "__main__":
    train_balanced_model()
