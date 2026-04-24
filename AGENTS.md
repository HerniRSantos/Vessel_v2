# Vessel_v2

## Quick Start
```bash
# Ativar venv primeiro (senão importações falham)
source venv/bin/activate

# Arrancar tudo (API + DB init)
python3 launcher.py

# Apenas API (sem launcher)
python3 -m uvicorn backend.api_server:app --host 0.0.0.0 --port 8000
```

## Development
```bash
cd frontend && npm run dev   # Frontend dev server
cd frontend && npm run build  # Production build
```

## Auth
- Basic auth (valores definidos em .env para produção)

## Architecture
| File | Purpose |
|------|---------|
| `backend/api_server.py` | FastAPI + static files + auth |
| `backend/database.py` | SQLite WAL schema |
| `launcher.py` | Service orchestrator |
| `frontend/dist/` | Built React assets |

## Endpoints
| Route | Auth | Description |
|-------|------|-------------|
| `/api/` | Basic | API status |
| `/api/vessels` | Basic | All vessels |
| `/api/vessels/live` | Basic | Latest positions |
| `/` | Basic | Frontend SPA |

## Database
- Path: `backend/vessels_v2.db`
- Tables: `vessels_master`, `positions_history`, `occurrences`
- WAL mode enabled

## Skills (auto-carregadas por contexto)
| Task | Skill |
|------|-------|
| UI React | `@[skills/tailwind-patterns]`, `@[skills/nextjs-react-expert]` |
| API Backend | `@[skills/python-patterns]`, `@[skills/api-patterns]` |
| Database | `@[skills/database-design]` |
| Testing | `@[skills/webapp-testing]` |
| Debugging | `@[skills/systematic-debugging]` |

Local skills: `/home/kaus/Desktop/Kaus_Test/.agent/skills/`

## Quirks
- CORS aberto (`allow_origins=["*"]`) - desenvolvimento apenas
- Todos os endpoints requerem Basic auth
- Se servidor continuar em background após Ctrl+C: `pkill -f uvicorn`
- O `.env` carrega de `../.env` (mesma raiz do projeto)

## Important
- Ativar venv **antes** de qualquer comando Python
- Build do frontend vai para `frontend/dist/`, servida na root `/`