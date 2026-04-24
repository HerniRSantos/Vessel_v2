from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import secrets
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

app = FastAPI(title="VesselControl V2 API", description="FastAPI Backend for Maritime Intelligence - PRD v1.2")
security = HTTPBasic()

USERNAME = os.getenv("HUB_USER")
PASSWORD = os.getenv("HUB_PASS")

if not USERNAME or not PASSWORD:
    raise ValueError("HUB_USER and HUB_PASS must be set in .env")

def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais Incorretas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_engine():
    from sqlalchemy import create_engine
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
    pg_url = os.getenv("DATABASE_URL", "postgresql://vessel_user:vessel_pass_2026@localhost:5432/vessels_db")
    return create_engine(pg_url)


@app.get("/api/")
def read_root(username: str = Depends(check_auth)):
    return {"status": "VesselControl V2 API Online", "user": username, "version": "1.2_phase1"}


@app.get("/api/vessels", response_model=List[Dict])
def get_vessels(username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            vessels = conn.execute(text("SELECT * FROM vessels_master")).fetchall()
        return [dict(v._mapping) for v in vessels]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vessels/live", response_model=List[Dict])
def get_live_positions(username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            SELECT p.*, v.name, v.vessel_type, v.flag, v.suspicious, v.suspect_reason, v.notes
            FROM positions p
            JOIN vessels_master v ON p.mmsi = v.mmsi
            INNER JOIN (
                SELECT mmsi, MAX(timestamp) as max_time
                FROM positions
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY mmsi
            ) pm ON p.mmsi = pm.mmsi AND p.timestamp = pm.max_time
            ORDER BY p.timestamp DESC
            LIMIT 500
        ''')
        with engine.connect() as conn:
            positions = conn.execute(query).fetchall()
        return [dict(p._mapping) for p in positions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vessels/trail/{mmsi}", response_model=Dict)
def get_vessel_trail(mmsi: int, hours: int = 6, username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            SELECT latitude, longitude, sog, cog, heading, timestamp
            FROM positions
            WHERE mmsi = :mmsi AND timestamp > NOW() - :hours * INTERVAL '1 hour'
            ORDER BY timestamp ASC
        ''')
        with engine.connect() as conn:
            trail = conn.execute(query, {"mmsi": mmsi, "hours": hours}).fetchall()
        return {"mmsi": mmsi, "trail": [dict(p._mapping) for p in trail]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vessels/{mmsi}/gaps", response_model=List[Dict])
def get_vessel_gaps(mmsi: int, username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            WITH vessel_positions AS (
                SELECT 
                    mmsi,
                    latitude,
                    longitude,
                    timestamp,
                    LAG(timestamp) OVER w AS prev_timestamp,
                    LAG(latitude) OVER w AS prev_lat,
                    LAG(longitude) OVER w AS prev_lon
                FROM positions
                WHERE mmsi = :mmsi
                WINDOW w AS (ORDER BY timestamp)
            )
            SELECT 
                mmsi,
                prev_lat AS last_latitude,
                prev_lon AS last_longitude,
                prev_timestamp AS last_seen,
                timestamp AS appeared,
                EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) / 60.0 AS gap_minutes
            FROM vessel_positions
            WHERE prev_timestamp IS NOT NULL
              AND (timestamp - prev_timestamp) > INTERVAL '2 hours'
            ORDER BY timestamp DESC
            LIMIT 100
        ''')
        with engine.connect() as conn:
            gaps = conn.execute(query, {"mmsi": mmsi}).fetchall()
        return [dict(g._mapping) for g in gaps]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dark-vessels", response_model=List[Dict])
def get_dark_vessels(username: str = Depends(check_auth), hours: int = 2):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            WITH last_positions AS (
                SELECT 
                    mmsi,
                    latitude,
                    longitude,
                    timestamp,
                    MAX(timestamp) OVER w AS max_time
                FROM positions
                WINDOW w AS (PARTITION BY mmsi)
            )
            SELECT 
                v.mmsi,
                v.name,
                v.vessel_type,
                v.flag,
                v.suspicious,
                lp.latitude,
                lp.longitude,
                lp.timestamp AS last_seen,
                EXTRACT(EPOCH FROM (NOW() - lp.timestamp)) / 60.0 AS minutes_since
            FROM last_positions lp
            JOIN vessels_master v ON lp.mmsi = v.mmsi
            WHERE lp.timestamp = lp.max_time
              AND lp.timestamp < NOW() - :hours * INTERVAL '1 hour'
            ORDER BY lp.timestamp DESC
            LIMIT 200
        ''')
        with engine.connect() as conn:
            dark = conn.execute(query, {"hours": hours}).fetchall()
        return [dict(d._mapping) for d in dark]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vessel/{mmsi}", response_model=Dict)
def get_vessel(mmsi: int, username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            vessel = conn.execute(text("SELECT * FROM vessels_master WHERE mmsi = :mmsi"), {"mmsi": mmsi}).fetchone()
            if not vessel:
                raise HTTPException(status_code=404, detail=f"Embarcação {mmsi} não encontrada")
            pos_count = conn.execute(text("SELECT COUNT(*) FROM positions WHERE mmsi = :mmsi"), {"mmsi": mmsi}).fetchone()[0]
        result = dict(vessel._mapping)
        result['position_count'] = pos_count
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vessel/{mmsi}")
def update_vessel(mmsi: int, data: Dict, username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        allowed = {"name", "vessel_type", "suspicious", "suspect_reason", "notes"}
        fields = {k: v for k, v in data.items() if k in allowed}
        if not fields:
            return {"status": "ok", "vessel": {}}
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["mmsi"] = mmsi
        with engine.begin() as conn:
            conn.execute(text(f"UPDATE vessels_master SET {set_clause} WHERE mmsi = :mmsi"), fields)
            vessel = conn.execute(text("SELECT * FROM vessels_master WHERE mmsi = :mmsi"), {"mmsi": mmsi}).fetchone()
        return {"status": "ok", "vessel": dict(vessel._mapping) if vessel else {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vessel/{mmsi}/history", response_model=List[Dict])
def get_vessel_history(mmsi: int, hours: int = 24, username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            SELECT latitude, longitude, timestamp FROM positions
            WHERE mmsi = :mmsi AND timestamp > NOW() - :hours * INTERVAL '1 hour'
            ORDER BY timestamp ASC
        ''')
        with engine.connect() as conn:
            rows = conn.execute(query, {"mmsi": mmsi, "hours": hours}).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dlq", response_model=List[Dict])
def get_dlq(username: str = Depends(check_auth), limit: int = 100):
    try:
        from sqlalchemy import text
        engine = get_engine()
        query = text('''
            SELECT * FROM positions_dlq
            ORDER BY received_at DESC
            LIMIT :limit
        ''')
        with engine.connect() as conn:
            rows = conn.execute(query, {"limit": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", response_model=Dict)
def health_check(username: str = Depends(check_auth)):
    try:
        from sqlalchemy import text, create_engine
        pg_url = os.getenv("DATABASE_URL", "postgresql://vessel_user:vessel_pass_2026@localhost:5432/vessels_db")
        engine = create_engine(pg_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "version": "1.2_phase1"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '../frontend/dist')


@app.get("/")
async def serve_spa(username: str = Depends(check_auth)):
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard de UI ainda Não Compilado</h1><p>Corra npm run build no react!</p>", status_code=404)


if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST), name="static")