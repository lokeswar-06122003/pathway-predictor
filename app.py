"""Pathway - Student Learning Pathway Predictor (Flask app)."""
import json
import os

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

app = Flask(__name__)

# Load once at startup. If a file is missing the app stops with a clear error,
# which shows up in the hosting platform's logs.
model = joblib.load(os.path.join(MODEL_DIR, "stream_model.pkl"))
gender_encoder = joblib.load(os.path.join(MODEL_DIR, "gender_encoder.pkl"))
stream_encoder = joblib.load(os.path.join(MODEL_DIR, "stream_encoder.pkl"))
with open(os.path.join(MODEL_DIR, "model_info.json")) as f:
    MODEL_INFO = json.load(f)

FEATURES = ["Gender", "Math_Marks", "Science_Marks", "Arts_Marks", "Study_Hours_Per_Week"]

# name -> (label, min, max)
FIELDS = {
    "math": ("Maths marks", 0, 100),
    "science": ("Science marks", 0, 100),
    "arts": ("Arts marks", 0, 100),
    "hours": ("Study hours per week", 0, 60),
}
DEFAULTS = {"gender": "Female", "math": 72, "science": 68, "arts": 60, "hours": 18}


def parse_input(data):
    """Validate raw input. Returns (values, error_message)."""
    values = {}
    gender = str(data.get("gender", "")).strip().capitalize()
    if gender not in gender_encoder.classes_:
        return None, "Choose Female or Male."
    values["gender"] = gender
    for name, (label, low, high) in FIELDS.items():
        raw = str(data.get(name, "")).strip()
        try:
            value = int(round(float(raw)))
        except ValueError:
            return None, f"Enter a number for {label.lower()}."
        if not low <= value <= high:
            return None, f"{label} must be between {low} and {high}."
        values[name] = value
    return values, None


def run_model(v):
    row = pd.DataFrame(
        [[gender_encoder.transform([v["gender"]])[0], v["math"], v["science"], v["arts"], v["hours"]]],
        columns=FEATURES,
    )
    probs = model.predict_proba(row)[0]
    by_stream = {
        stream_encoder.inverse_transform([cls])[0]: round(float(p) * 100, 1)
        for cls, p in zip(model.classes_, probs)
    }
    stream = max(by_stream, key=by_stream.get)
    return {"stream": stream, "confidence": by_stream[stream], "probabilities": by_stream}


@app.route("/")
def index():
    return render_template("index.html", values=DEFAULTS, result=run_model(DEFAULTS),
                           info=MODEL_INFO, fields=FIELDS, error=None)


@app.route("/predict", methods=["POST"])
def predict_form():
    """Works without JavaScript: normal form post, page re-renders."""
    values, error = parse_input(request.form)
    if error:
        merged = {**DEFAULTS, **{k: request.form.get(k, v) for k, v in DEFAULTS.items()}}
        return render_template("index.html", values=merged, result=None,
                               info=MODEL_INFO, fields=FIELDS, error=error), 400
    return render_template("index.html", values=values, result=run_model(values),
                           info=MODEL_INFO, fields=FIELDS, error=None)


@app.route("/api/predict", methods=["POST"])
def predict_api():
    """Used by the live predictor on the page."""
    values, error = parse_input(request.get_json(silent=True) or {})
    if error:
        return jsonify({"error": error}), 400
    return jsonify(run_model(values))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
