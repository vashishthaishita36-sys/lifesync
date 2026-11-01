import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 90

dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=N)

bedtime_num = np.clip(rng.normal(5.5, 1.3, N), 3, 9)
wake_time = rng.uniform(6.0, 8.0, N)
sleep_hours = np.clip(6 + wake_time - bedtime_num + rng.normal(0, 0.4, N), 3, 10)
study_hours = np.clip(rng.normal(4, 1.5, N), 0, 10)
tasks_planned = rng.integers(3, 9, N)
exercise_minutes = rng.choice([0, 15, 30, 45, 60], N, p=[0.3, 0.2, 0.25, 0.15, 0.1])
screen_hours = np.clip(rng.normal(4, 1.5, N), 1, 10)
spending = np.clip(rng.normal(250, 120, N), 0, None)

completion_rate = np.clip(
    0.5 + 0.06 * (sleep_hours - 6.5) + 0.04 * (study_hours - 4)
    - 0.03 * (screen_hours - 4) + rng.normal(0, 0.1, N),
    0.1, 1.0)
tasks_completed = np.minimum(np.round(tasks_planned * completion_rate), tasks_planned)

productivity = (
    5
    + 0.5 * (sleep_hours - 6.5)
    - 0.35 * (bedtime_num - 5.5)
    + 0.35 * (study_hours - 4)
    + 0.012 * exercise_minutes
    - 0.3 * (screen_hours - 4)
    + rng.normal(0, 0.6, N)
)
productivity = np.clip(np.round(productivity), 1, 10)

clock = 18 + bedtime_num
bedtime = [f"{int(c) % 24:02d}:{int((c - int(c)) * 60):02d}" for c in clock]

df = pd.DataFrame({
    "entry_date": dates.strftime("%Y-%m-%d"),
    "bedtime": bedtime,
    "bedtime_num": np.round(bedtime_num, 2),
    "sleep_hours": np.round(sleep_hours, 1),
    "study_hours": np.round(study_hours, 1),
    "tasks_planned": tasks_planned,
    "tasks_completed": tasks_completed.astype(int),
    "exercise_minutes": exercise_minutes,
    "screen_hours": np.round(screen_hours, 1),
    "spending": np.round(spending, 0),
    "productivity_score": productivity.astype(int),
})

os.makedirs("data", exist_ok=True)
df.to_csv("data/sample_data.csv", index=False)
print(df.head())
print(f"\nSaved {len(df)} rows to data/sample_data.csv")