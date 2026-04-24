# Vessel_v2 - AIS Maritime Intelligence System

## Quick Start

```bash
# Docker (recommended)
docker compose up -d

# Or direct (requires venv + PostgreSQL running)
source venv/bin/activate
python3 launcher.py
```

## Auth
- User: `vessel`
- Pass: `control2026`

## Architecture
| File | Purpose |
|------|---------|
| `backend/api_server.py` | FastAPI + auth + PostgreSQL |
| `backend/database.py` | PostgreSQL connection |
| `backend/ais_ingestor.py` | AIS WebSocket stream listener |
| `launcher.py` | Service orchestrator |
| `docker-compose.yml` | Full stack (API + Ingestor + PostgreSQL) |

## Database
- **PostgreSQL 16 + PostGIS 3.4** (Docker container: `vessel_v2_db`)
- Tables: `vessels_master`, `positions`, `positions_dlq`, `occurrences`
- Raw message preservation: `positions.raw_msg` stores original NMEA JSON
- DLQ: `positions_dlq` for rejected/spoofed messages

## API Endpoints
| Route | Description |
|-------|-------------|
| `/api/health` | System + DB status |
| `/api/vessels` | All vessels |
| `/api/vessels/live` | Active vessels (< 1h) |
| `/api/dark-vessels?hours=N` | Vessels inactive > N hours |
| `/api/vessels/{mmsi}/gaps` | Signal gap detection |
| `/api/dlq` | Dead letter queue |

## AIS Stream
- WebSocket: `wss://stream.aisstream.io/v0/stream`
- BoundingBox in `.env` must be large enough to capture ships
- Working config: `[[[-20, 20], [0, 60]]` (larger area = more data)

## Docker Commands
```bash
# Start all services
docker compose up -d

# View logs
docker logs vessel_v2_ingestor
docker logs vessel_v2_api

# Restart a service
docker compose restart ingestor
```

## Known Issues
- **aisstream.io**: Sometimes closes connection immediately. Retry logic handles this.
- **BoundingBox**: Too small = no messages. Use `[[[-20, 20], [0, 60]]` or larger.
- Connection: `localhost:5432` (PostgreSQL), `localhost:8000` (API)

## Important
- CORS open for development only
- All endpoints require Basic auth
- PostgreSQL must be running before API starts
- If ports conflict: `pkill -f uvicorn`
