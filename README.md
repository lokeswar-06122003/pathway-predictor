# Pathway: Student Learning Pathway Predictor

A web app that predicts whether a student is better suited to a **Technical** or **Academic** stream from their maths, science and arts marks, weekly study hours and gender. The result updates live as you move the sliders. You also see how your marks compare with the average student in each stream.

Built with Flask and scikit-learn (Random Forest, 200 trees), trained on 5,141 student records.

| | |
|---|---|
| Accuracy on unseen students | 91.9% |
| 5-fold cross-validation | 91.4% |
| Baseline (always "Technical") | 85.9% |

## Project structure

```
pathway/
├── app.py                 Flask app: pages, JSON API, health check
├── train_model.py         Retrains the model and writes model_info.json
├── cleandata.py           Cleans the raw dataset
├── requirements.txt       Pinned versions (scikit-learn must match the .pkl)
├── Procfile               Start command for Render / Railway / Heroku
├── render.yaml            One-click Render setup
├── .python-version        Python 3.12
├── model/
│   ├── stream_model.pkl
│   ├── gender_encoder.pkl
│   ├── stream_encoder.pkl
│   └── model_info.json    Accuracy, averages and feature importance shown on the site
├── dataset/
│   ├── student_learning_pathway1_data.csv
│   └── fully_cleaned_student_pathway_data.csv
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/app.js          Live predictions and the comparison chart
    ├── fonts/             Familjen Grotesk (self-hosted, SIL OFL)
    └── favicon.svg
```

## Run it on your computer

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploy for free on Render

1. Push this folder to a GitHub repository.
2. On https://render.com, sign in with GitHub and choose **New → Blueprint**, then pick the repo. `render.yaml` fills in everything.
   (Or choose **New → Web Service** and set: build `pip install -r requirements.txt`, start `gunicorn app:app`.)
3. Wait for the build to finish and open the `.onrender.com` link.

The free plan sleeps after 15 minutes without visitors and takes about a minute to wake up, so open the link shortly before a demo.

## API

`POST /api/predict`

```json
{ "gender": "Female", "math": 72, "science": 68, "arts": 60, "hours": 18 }
```

Response:

```json
{ "stream": "Technical", "confidence": 91.2, "probabilities": { "Technical": 91.2, "Academic": 8.8 } }
```

`GET /health` returns `{"status": "ok"}`.

## Retraining

```bash
python cleandata.py      # optional: rebuild the cleaned CSV from the raw one
python train_model.py    # retrains and rewrites everything in model/
```

If you retrain with a different scikit-learn version, update the `scikit-learn==` line in `requirements.txt` to match.

## Author

P Lokeswar, MCA
