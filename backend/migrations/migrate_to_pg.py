import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

MIGRATIONS_DIR = os.path.dirname(__file__)

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DB", "vessels_db"),
    "user": os.getenv("PG_USER", "vessel_user"),
    "password": os.getenv("PG_PASSWORD", "vessel_pass_2026"),
}

PG_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

engine = create_engine(PG_URL, echo=False)


def import_vessels():
    """Import vessels_master from JSON"""
    vessels_path = os.path.join(MIGRATIONS_DIR, 'vessels_master.json')
    if not os.path.exists(vessels_path):
        print("vessels_master.json not found")
        return 0
    
    with open(vessels_path, "r") as f:
        vessels = json.load(f)
    
    print(f"Importing {len(vessels)} vessels...")
    
    with engine.begin() as conn:
        for v in vessels:
            conn.execute(
                text("""
                    INSERT INTO vessels_master (
                        mmsi, name, vessel_type, flag, callsign, 
                        dimension_a, dimension_b, dimension_c, dimension_d,
                        first_seen, last_seen, last_updated,
                        suspicious, suspect_reason, notes
                    ) VALUES (
                        :mmsi, :name, :vessel_type, :flag, :callsign,
                        :dimension_a, :dimension_b, :dimension_c, :dimension_d,
                        :first_seen, :last_seen, :last_updated,
                        :suspicious, :suspect_reason, :notes
                    ) ON CONFLICT (mmsi) DO UPDATE SET
                        name = COALESCE(EXCLUDED.name, vessels_master.name),
                        vessel_type = COALESCE(EXCLUDED.vessel_type, vessels_master.vessel_type),
                        flag = COALESCE(EXCLUDED.flag, vessels_master.flag),
                        callsign = COALESCE(EXCLUDED.callsign, vessels_master.callsign),
                        last_updated = COALESCE(EXCLUDED.last_updated, vessels_master.last_updated)
                """),
                {
                    "mmsi": v.get("mmsi"),
                    "name": v.get("name"),
                    "vessel_type": v.get("vessel_type") or "Desconhecido",
                    "flag": v.get("flag"),
                    "callsign": v.get("callsign"),
                    "dimension_a": v.get("dimension_a"),
                    "dimension_b": v.get("dimension_b"),
                    "dimension_c": v.get("dimension_c"),
                    "dimension_d": v.get("dimension_d"),
                    "first_seen": v.get("first_seen") or datetime.now().isoformat(),
                    "last_seen": v.get("last_seen"),
                    "last_updated": v.get("last_updated"),
                    "suspicious": bool(v.get("suspicious", 0)),
                    "suspect_reason": v.get("suspect_reason", ""),
                    "notes": v.get("notes", ""),
                }
            )
    
    print(f"Imported {len(vessels)} vessels")
    return len(vessels)


def import_positions():
    """Import positions_history from JSON"""
    positions_path = os.path.join(MIGRATIONS_DIR, 'positions_history.json')
    if not os.path.exists(positions_path):
        print("positions_history.json not found")
        return 0
    
    with open(positions_path, "r") as f:
        positions = json.load(f)
    
    print(f"Importing {len(positions)} positions in batches...")
    
    batch_size = 500
    for i in range(0, len(positions), batch_size):
        batch = positions[i:i + batch_size]
        
        with engine.begin() as conn:
            for p in batch:
                conn.execute(
                    text("""
                        INSERT INTO positions (
                            mmsi, latitude, longitude, sog, cog, heading,
                            nav_status, timestamp, raw_msg
                        ) VALUES (
                            :mmsi, :lat, :lon, :speed, :course, :heading,
                            :nav_status, :timestamp, :raw_msg
                        )
                    """),
                    {
                        "mmsi": p.get("mmsi"),
                        "lat": p.get("lat"),
                        "lon": p.get("lon"),
                        "speed": p.get("speed"),
                        "course": p.get("course"),
                        "heading": p.get("true_heading"),
                        "nav_status": p.get("nav_status"),
                        "timestamp": p.get("timestamp"),
                        "raw_msg": json.dumps(p),  # Store original dict as raw_msg for forense
                    }
                )
        
        print(f"  Imported {min(i + batch_size, len(positions))}/{len(positions)} positions")
    
    print(f"Imported {len(positions)} positions")
    return len(positions)


if __name__ == "__main__":
    print("=== MIGRATING DATA TO POSTGRESQL ===")
    
    try:
        vessels_count = import_vessels()
        positions_count = import_positions()
        
        print(f"\n=== MIGRATION COMPLETE ===")
        print(f"Vessels: {vessels_count}")
        print(f"Positions: {positions_count}")
    except Exception as e:
        print(f"Migration failed: {e}")