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
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

app = FastAPI(title="VesselControl V2 API", description="FastAPI Backend for Maritime Intelligence")
security = HTTPBasic()

# Variáveis de Auth (Predefiniões de Segurança caso não exista .env)
USERNAME = os.getenv("HUB_USER", "vessel")
PASSWORD = os.getenv("HUB_PASS", "control2026")

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
            SELECT p.*, v.name, v.type, v.flag
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

