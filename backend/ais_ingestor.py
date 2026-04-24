import asyncio
import websockets
import json
from datetime import datetime, timezone
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

AIS_WEBSOCKET_URL = "wss://stream.aisstream.io/v0/stream"
AIS_API_KEY = os.getenv("AIS_API_KEY", "")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "database": os.getenv("PG_DB", "vessels_db"),
    "user": os.getenv("PG_USER", "vessel_user"),
    "password": os.getenv("PG_PASSWORD", "vessel_pass_2026"),
}
PG_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(PG_URL, echo=False)

SHIP_TYPE_MAP = {
    0: "Desconhecido", 20: "Carga", 30: "Petroleiro", 31: "Petroleiro",
    40: "Carga", 50: "Carga", 60: "Passageiros", 70: "Ferry",
    80: "Rebocador", 90: "Pesca", 100: "Veleiro", 101: "Recreio",
}

def get_ship_type_name(type_code):
    return SHIP_TYPE_MAP.get(type_code, "Outro")


async def process_position_report(data_dict: dict):
    msg = data_dict.get("Message", {}).get("PositionReport", {})
    if not msg:
        return None
    
    mmsi = str(msg.get("UserID", ""))
    if not mmsi:
        return None
    
    return {
        "mmsi": mmsi,
        "lat": msg.get("Latitude"),
        "lon": msg.get("Longitude"),
        "speed": msg.get("Sog", 0),
        "course": msg.get("Cog", 0),
        "heading": msg.get("TrueHeading", 0),
        "nav_status": msg.get("NavigationalStatus", 0),
    }


async def process_ship_static_data(data_dict: dict):
    msg = data_dict.get("Message", {}).get("ShipStaticData", {})
    if not msg:
        return None
    
    mmsi = str(msg.get("UserID", ""))
    if not mmsi:
        return None
    
    return {
        "mmsi": mmsi,
        "name": msg.get("Name", "").strip() or None,
        "call_sign": msg.get("CallSign", "").strip() or None,
        "ship_type": msg.get("ShipType", 0),
        "dimension_a": msg.get("DimensionA", 0),
        "dimension_b": msg.get("DimensionB", 0),
        "dimension_c": msg.get("DimensionC", 0),
        "dimension_d": msg.get("DimensionD", 0),
        "eta": msg.get("ETA", ""),
        "draft": msg.get("MaximumDraught", 0),
        "destination": msg.get("Destination", "").strip() or None,
    }


async def process_ais_message(data_dict: dict):
    msg_type = data_dict.get("MessageType")
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        if msg_type == "PositionReport":
            pos_data = await process_position_report(data_dict)
            if not pos_data:
                return
            
            raw_msg = json.dumps(data_dict)
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO vessels_master (mmsi, last_updated) 
                        VALUES (:mmsi, :timestamp)
                        ON CONFLICT(mmsi) DO UPDATE SET last_updated = EXCLUDED.last_updated
                    """),
                    {"mmsi": pos_data["mmsi"], "timestamp": timestamp}
                )
                
                conn.execute(
                    text("""
                        INSERT INTO positions 
                        (mmsi, latitude, longitude, sog, cog, heading, nav_status, timestamp, raw_msg)
                        VALUES (:mmsi, :lat, :lon, :speed, :course, :heading, :nav_status, :timestamp, :raw_msg)
                    """),
                    {
                        "mmsi": pos_data["mmsi"],
                        "lat": pos_data["lat"],
                        "lon": pos_data["lon"],
                        "speed": pos_data["speed"],
                        "course": pos_data["course"],
                        "heading": pos_data["heading"],
                        "nav_status": pos_data["nav_status"],
                        "timestamp": timestamp,
                        "raw_msg": raw_msg,
                    }
                )
            
            print(f"[AIS] Pos: {pos_data['mmsi']} ({pos_data['lat']:.4f}, {pos_data['lon']:.4f})")
        
        elif msg_type == "ShipStaticData":
            static_data = await process_ship_static_data(data_dict)
            if not static_data:
                return
            
            ship_type = get_ship_type_name(static_data.get("ship_type", 0))
            
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO vessels_master (
                            mmsi, name, callsign, vessel_type, dimension_a, dimension_b,
                            dimension_c, dimension_d, last_updated
                        ) VALUES (
                            :mmsi, :name, :callsign, :vessel_type, :dimension_a, :dimension_b,
                            :dimension_c, :dimension_d, :timestamp
                        ) ON CONFLICT(mmsi) DO UPDATE SET
                            name = COALESCE(EXCLUDED.name, vessels_master.name),
                            callsign = COALESCE(EXCLUDED.callsign, vessels_master.callsign),
                            vessel_type = COALESCE(EXCLUDED.vessel_type, vessels_master.vessel_type),
                            last_updated = EXCLUDED.last_updated
                    """),
                    {
                        "mmsi": static_data["mmsi"],
                        "name": static_data.get("name"),
                        "callsign": static_data.get("call_sign"),
                        "vessel_type": ship_type,
                        "dimension_a": static_data.get("dimension_a"),
                        "dimension_b": static_data.get("dimension_b"),
                        "dimension_c": static_data.get("dimension_c"),
                        "dimension_d": static_data.get("dimension_d"),
                        "timestamp": timestamp,
                    }
                )
            
            print(f"[AIS] Static: {static_data['mmsi']} - {static_data.get('name') or 'Unknown'}")
    
    except Exception as e:
        print(f"[AIS] Erro: {e}")


async def ais_listener():
    print(f"[AIS] Conectando ao Stream: {AIS_WEBSOCKET_URL}")
    
    bbox = [[[-20, 20], [0, 60]]]
    
    while True:
        try:
            async with websockets.connect(AIS_WEBSOCKET_URL) as websocket:
                subscribe_msg = {
                    "APIKey": AIS_API_KEY,
                    "BoundingBoxes": bbox,
                    "FiltersShipMMSI": [],
                    "FilterMessageTypes": ["PositionReport"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                print(f"[AIS] Subscreveu. A escutar em {bbox}...")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await process_ais_message(data)
                    except json.JSONDecodeError:
                        continue
                        
        except websockets.exceptions.ConnectionClosed:
            print("[AIS] Conexao encerrada. A tentar novamente em 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[AIS] Erro: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[AIS] Erro: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(ais_listener())