import requests
import sqlite3
import os
import time
from datetime import datetime
from database import get_db_connection

def get_vessels_without_names():
    conn = get_db_connection()
    vessels = conn.execute('''
        SELECT mmsi FROM vessels_master 
        WHERE name IS NULL OR name = '' OR name = 'Unknown'
        LIMIT 100
    ''').fetchall()
    conn.close()
    return [v[0] for v in vessels]

def update_vessel(mmsi, data):
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE vessels_master SET
                name = COALESCE(?, name),
                flag = COALESCE(?, flag),
                vessel_type = COALESCE(?, vessel_type),
                callsign = COALESCE(?, callsign),
                last_updated = ?
            WHERE mmsi = ?
        ''', (
            data.get('name'), data.get('flag'), data.get('type'),
            data.get('callsign'), datetime.utcnow().isoformat() + "Z", mmsi
        ))
        conn.commit()
        print(f"[OSINT] Updated {mmsi}: {data.get('name')}")
    finally:
        conn.close()

def enrich_from_myshiptracking(mmsi):
    try:
        url = f"https://www.myshiptracking.com/requests/vessel/{mmsi}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                v = data.get('data', {})
                return {
                    'name': v.get('name'),
                    'flag': v.get('flag'),
                    'type': v.get('type'),
                    'callsign': v.get('callsign')
                }
    except Exception as e:
        pass
    return None

def enrich_from_vesselfinder(mmsi):
    try:
        url = f"https://www.vesselfinder.com/api/vessel/{mmsi}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('IMO') and data.get('VESSEL'):
                v = data['VESSEL']
                return {
                    'name': v.get('NAME'),
                    'flag': v.get('FLAG'),
                    'type': v.get('TYPE'),
                    'callsign': v.get('CALLSIGN')
                }
    except Exception as e:
        pass
    return None

def enrich_vessel(mmsi):
    result = enrich_from_myshiptracking(mmsi)
    if not result:
        result = enrich_from_vesselfinder(mmsi)
    return result

def run_enrichment():
    print("[OSINT] A iniciar enriquecimento de dados...")
    
    while True:
        vessels = get_vessels_without_names()
        if not vessels:
            print("[OSINT] Todas as embarcações já têm nome. A esperar...")
            time.sleep(60)
            continue
        
        print(f"[OSINT] A enriquecer {len(vessels)} embarcações...")
        
        for mmsi in vessels[:10]:
            data = enrich_vessel(mmsi)
            if data and data.get('name'):
                update_vessel(mmsi, data)
            time.sleep(2)
        
        time.sleep(30)

if __name__ == "__main__":
    run_enrichment()
