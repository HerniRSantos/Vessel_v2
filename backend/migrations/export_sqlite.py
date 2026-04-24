import sqlite3
import json
import os

DB_PATH = "/home/kaus/Desktop/Kaus_Test/Vessel_v2/backend/vessels_v2.db"
EXPORT_DIR = "/home/kaus/Desktop/Kaus_Test/Vessel_v2/backend/migrations"

os.makedirs(EXPORT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=== EXPORTING DATA FROM SQLITE ===")

# Export vessels_master
vessels = conn.execute("SELECT * FROM vessels_master").fetchall()
vessels_data = [dict(v) for v in vessels]
with open(f"{EXPORT_DIR}/vessels_master.json", "w") as f:
    json.dump(vessels_data, f, indent=2, default=str)
print(f"Vessels: {len(vessels_data)} records")

# Export positions_history
positions = conn.execute("SELECT * FROM positions_history").fetchall()
positions_data = [dict(p) for p in positions]
with open(f"{EXPORT_DIR}/positions_history.json", "w") as f:
    json.dump(positions_data, f, indent=2, default=str)
print(f"Positions: {len(positions_data)} records")

# Export occurrences
occurrences = conn.execute("SELECT * FROM occurrences").fetchall()
occurrences_data = [dict(o) for o in occurrences]
with open(f"{EXPORT_DIR}/occurrences.json", "w") as f:
    json.dump(occurrences_data, f, indent=2, default=str)
print(f"Occurrences: {len(occurrences_data)} records")

conn.close()

print(f"\n=== EXPORT COMPLETE ===")
print(f"Files saved to: {EXPORT_DIR}")