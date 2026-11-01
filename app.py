from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
import database
import dsa_utils
import ml

app = Flask(__name__)
app.secret_key = "change-this-later"

database.init_db()

SLIDERS = [
    ("bedtime_num", "Bedtime", 0, 12, 0.25),
    ("sleep_hours", "Sleep hours", 3, 12, 0.5),
    ("study_hours", "Study / work hours", 0, 12, 0.5),
    ("exercise_minutes", "Exercise (minutes)", 0, 120, 5),
    ("screen_hours", "Screen time (hours)", 0, 14, 0.5),
]


def read_and_validate(form):
    try:
        entry = {
            "entry_date": form["entry_date"],
            "bedtime": form["bedtime"],
            "sleep_hours": float(form["sleep_hours"]),
            "study_hours": float(form["study_hours"]),
            "tasks_planned": int(form["tasks_planned"]),
            "tasks_completed": int(form["tasks_completed"]),
            "exercise_minutes": int(form["exercise_minutes"]),
            "screen_hours": float(form["screen_hours"]),
            "spending": float(form["spending"]),
            "productivity_score": int(form["productivity_score"]),
        }
    except (KeyError, ValueError):
        return None, "Please fill every field with a valid number."

    if not entry["bedtime"] or not entry["entry_date"]:
        return None, "Date and bedtime are required."
    if not 0 <= entry["sleep_hours"] <= 24 or not 0 <= entry["study_hours"] <= 24:
        return None, "Sleep and study hours must be between 0 and 24."
    if not 0 <= entry["screen_hours"] <= 24:
        return None, "Screen hours must be between 0 and 24."
    if entry["tasks_completed"] > entry["tasks_planned"]:
        return None, "Completed tasks can't be more than planned tasks."
    if not 1 <= entry["productivity_score"] <= 10:
        return None, "Productivity score must be between 1 and 10."
    if min(entry["spending"], entry["exercise_minutes"],
           entry["tasks_planned"], entry["tasks_completed"]) < 0:
        return None, "Values can't be negative."
    return entry, None


@app.route("/")
def home():
    return redirect(url_for("twin"))


@app.route("/add", methods=["GET", "POST"])
def add_entry():
    if request.method == "POST":
        entry, error = read_and_validate(request.form)
        if error:
            flash(error)
            return redirect(url_for("add_entry"))
        database.save_entry(entry)
        flash("Entry saved! Your twin has been updated.")
        return redirect(url_for("twin"))
    return render_template("add_entry.html", today=date.today().isoformat())


@app.route("/entries")
def entries():
    rows = database.get_all_entries()
    return render_template("entries.html", rows=rows)


@app.route("/twin")
def twin():
    rows = database.get_all_entries()
    if not rows:
        flash("No entries yet. Add one or run seed_db.py.")
        return redirect(url_for("add_entry"))

    chrono = list(reversed(rows))
    latest = dict(rows[0])

    sleep_avg = dsa_utils.rolling_average([r["sleep_hours"] for r in chrono])[-1]
    scores_all = [r["productivity_score"] for r in chrono]
    prod_avg = dsa_utils.rolling_average(scores_all)[-1]
    streak = dsa_utils.current_streak([s >= 7 for s in scores_all])

    model = ml.load_model()
    prediction = None
    recs = []
    if model is not None:
        prediction = ml.predict(model, latest)
        recs = ml.recommend(model, latest)

    labels = [r["entry_date"] for r in chrono][-30:]
    scores = scores_all[-30:]
    averages = [round(a, 2) for a in dsa_utils.rolling_average(scores_all)][-30:]

    return render_template(
        "twin.html", latest=latest, sleep_avg=sleep_avg, prod_avg=prod_avg,
        streak=streak, prediction=prediction, recs=recs,
        insights=ml.correlations(), metrics=ml.load_metrics(),
        labels=labels, scores=scores, averages=averages)


@app.route("/simulate", methods=["GET", "POST"])
def simulate():
    rows = database.get_all_entries()
    model = ml.load_model()
    if not rows or model is None:
        flash("Add entries and train the model first (python ml.py).")
        return redirect(url_for("twin"))

    latest = dict(rows[0])
    current = {f: float(latest[f]) for f in ml.FEATURES}
    values = dict(current)
    result = None

    if request.method == "POST":
        try:
            values = {f: float(request.form[f]) for f in ml.FEATURES}
        except (KeyError, ValueError):
            flash("Invalid slider values.")
            return redirect(url_for("simulate"))
        now = ml.predict(model, current)
        simulated = ml.predict(model, values)
        result = {"current": now, "simulated": simulated,
                  "change": round(simulated - now, 1)}

    return render_template("simulate.html", sliders=SLIDERS,
                           values=values, result=result)


@app.route("/retrain", methods=["POST"])
def retrain():
    info, error = ml.train_and_save()
    if error:
        flash(error)
    else:
        flash(f"Model retrained on {info['rows']} entries. Best model: {info['best']}.")
    return redirect(url_for("twin"))


if __name__ == "__main__":
    app.run(debug=True)