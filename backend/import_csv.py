import csv
import sqlite3
import os
from collections import defaultdict
from datetime import datetime

CSV_PATH = "/home/kaus/Desktop/Kaus_Test/sails/VesselControl/file_data.csv"
DB_PATH = os.path.join(os.path.dirname(__file__), 'vessels_v2.db')

def import_csv():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        return

    vessels = {}
    positions = []

    print("Reading CSV...")
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mmsi_str = row['Id Embarcacao'].strip()
            if not mmsi_str or not mmsi_str.isdigit():
                continue
            mmsi = int(mmsi_str)
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            timestamp = row['timezone.utc'].replace('+00:00', 'Z')
            name = row['Nome do Barco'].strip() if row['Nome do Barco'] else None

            if mmsi not in vessels:
                vessels[mmsi] = {'mmsi': mmsi, 'name': name}

            positions.append({
                'mmsi': mmsi,
                'lat': lat,
                'lon': lon,
                'timestamp': timestamp
            })

    print(f"Found {len(vessels)} unique vessels, {len(positions)} positions")

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    cursor = conn.cursor()

    print("Inserting vessels...")
    for mmsi, data in vessels.items():
        cursor.execute('''
            INSERT OR IGNORE INTO vessels_master (mmsi, name, last_updated)
            VALUES (?, ?, ?)
        ''', (data['mmsi'], data['name'], datetime.now().isoformat()))

    print("Inserting positions...")
    cursor.executemany('''
        INSERT INTO positions_history (mmsi, lat, lon, speed, course, timestamp)
        VALUES (?, ?, ?, NULL, NULL, ?)
    ''', [(p['mmsi'], p['lat'], p['lon'], p['timestamp']) for p in positions])

    conn.commit()

    result = conn.execute("SELECT COUNT(*) FROM vessels_master").fetchone()
    vessels_count = result[0]
    result = conn.execute("SELECT COUNT(*) FROM positions_history").fetchone()
    positions_count = result[0]

    conn.close()

    print(f"Import complete: {vessels_count} vessels, {positions_count} positions")

if __name__ == '__main__':
    import_csv()