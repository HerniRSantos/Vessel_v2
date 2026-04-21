from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import secrets
import os
from .database import get_db_connection
from typing import List, Dict
from dotenv import load_dotenv

# Carregar variáveis de ambiente da raiz do projeto ou V2
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

app = FastAPI(title="VesselControl V2 API", description="FastAPI Backend for Maritime Intelligence")
security = HTTPBasic()

# Variáveis de Auth - requeridas via .env
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

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Proteger API Internamente Reutilizando o `check_auth` em `Depends`
@app.get("/api/")
def read_root(username: str = Depends(check_auth)):
    return {"status": f"VesselControl V2 API Online. User: {username}"}

@app.get("/api/vessels", response_model=List[Dict])
def get_vessels(username: str = Depends(check_auth)):
    try:
        conn = get_db_connection()
        vessels = conn.execute("SELECT * FROM vessels_master").fetchall()
        return [dict(v) for v in vessels]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/api/vessels/live", response_model=List[Dict])
def get_live_positions(username: str = Depends(check_auth)):
    try:
        conn = get_db_connection()
        query = '''
            SELECT p.*, v.name, v.type, v.flag, v.suspicious, v.vessel_type, v.suspect_reason, v.notes
            FROM positions_history p
            JOIN vessels_master v ON p.mmsi = v.mmsi
            INNER JOIN (
                SELECT mmsi, MAX(timestamp) as max_time
                FROM positions_history
                GROUP BY mmsi
            ) pm ON p.mmsi = pm.mmsi AND p.timestamp = pm.max_time
            LIMIT 500
        '''
        positions = conn.execute(query).fetchall()
        return [dict(p) for p in positions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/api/vessel/{mmsi}", response_model=Dict)
def get_vessel(mmsi: int, username: str = Depends(check_auth)):
    try:
        conn = get_db_connection()
        vessel = conn.execute("SELECT * FROM vessels_master WHERE mmsi = ?", (mmsi,)).fetchone()
        if not vessel:
            raise HTTPException(status_code=404, detail=f"Embarcação {mmsi} não encontrada")
        
        pos_count = conn.execute(
            "SELECT COUNT(*) FROM positions_history WHERE mmsi = ?", (mmsi,)
        ).fetchone()[0]
        
        result = dict(vessel)
        result['position_count'] = pos_count
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.post("/api/vessel/{mmsi}")
def update_vessel(mmsi: int, data: Dict, username: str = Depends(check_auth)):
    try:
        conn = get_db_connection()
        
        allowed = {"name", "vessel_type", "suspicious", "suspect_reason", "notes"}
        fields = {k: v for k, v in data.items() if k in allowed}
        
        if not fields:
            return {"status": "ok", "vessel": {}}
        
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [mmsi]
        
        conn.execute(f"UPDATE vessels_master SET {set_clause} WHERE mmsi = ?", values)
        conn.commit()
        
        vessel = conn.execute("SELECT * FROM vessels_master WHERE mmsi = ?", (mmsi,)).fetchone()
        return {"status": "ok", "vessel": dict(vessel) if vessel else {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/api/vessel/{mmsi}/history", response_model=List[Dict])
def get_vessel_history(mmsi: int, hours: int = 24, username: str = Depends(check_auth)):
    try:
        conn = get_db_connection()
        from datetime import datetime, timezone, timedelta
        
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        query = '''
            SELECT lat, lon, timestamp FROM positions_history
            WHERE mmsi = ? AND timestamp > ?
            ORDER BY timestamp ASC
        '''
        rows = conn.execute(query, (mmsi, since)).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

# MONTAR FRONTEND (REACT/VITE STATIC) NA ROTA ROOT
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '../frontend/dist')

# Um truque FastAPI para proteger ficheiros estáticos é usar um Endpoint dependente de auth que devolve o HTML raiz.
@app.get("/")
async def serve_spa(username: str = Depends(check_auth)):
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard de UI ainda Não Compilado</h1><p>Corra npm run build no react!</p>", status_code=404)

# Proteger e Montar o Dist de React genérico /assets/
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST), name="static")

