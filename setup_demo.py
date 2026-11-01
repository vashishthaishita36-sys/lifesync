import subprocess
import sys

steps = ["generate_data.py", "seed_db.py", "ml.py"]

for step in steps:
    print("Running", step, "...")
    subprocess.run([sys.executable, step], check=True)

print("\nSetup complete. Now run: python app.py")