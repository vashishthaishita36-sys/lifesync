import pandas as pd
import database

database.init_db()
df = pd.read_csv("data/sample_data.csv")

for _, r in df.iterrows():
    database.save_entry({
        "entry_date": r["entry_date"],
        "bedtime": r["bedtime"],
        "sleep_hours": float(r["sleep_hours"]),
        "study_hours": float(r["study_hours"]),
        "tasks_planned": int(r["tasks_planned"]),
        "tasks_completed": int(r["tasks_completed"]),
        "exercise_minutes": int(r["exercise_minutes"]),
        "screen_hours": float(r["screen_hours"]),
        "spending": float(r["spending"]),
        "productivity_score": int(r["productivity_score"]),
    })

print("Seeded", len(df), "rows into lifesync.db")