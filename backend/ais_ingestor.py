import asyncio
import websockets
import json
from datetime import datetime
import os
from database import get_db_connection

AIS_WEBSOCKET_URL = "wss://stream.aisstream.io/v0/stream"
AIS_API_KEY = os.getenv("AIS_API_KEY", "")

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
        "true_heading": msg.get("TrueHeading", 0),
        "nav_status": msg.get("NavigationalStatus", 0),
        "timestamp": datetime.utcnow().isoformat() + "Z"
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

SHIP_TYPE_MAP = {
    0: "Desconhecido", 20: "Carga", 30: "Petroleiro", 31: "Petroleiro",
    40: "Carga", 50: "Carga", 60: "Passageiros", 70: "Ferry",
    80: "Rebocador", 90: "Pesca", 100: "Veleiro", 101: "Recreio",
}

def get_ship_type_name(type_code):
    return SHIP_TYPE_MAP.get(type_code, "Outro")

async def process_ais_message(data_dict: dict):
    msg_type = data_dict.get("MessageType")
    
    conn = get_db_connection()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        if msg_type == "PositionReport":
            pos_data = await process_position_report(data_dict)
            if not pos_data:
                return
            
            conn.execute('''
                INSERT INTO vessels_master (mmsi, last_updated) 
                VALUES (?, ?)
                ON CONFLICT(mmsi) DO UPDATE SET last_updated = excluded.last_updated
            ''', (pos_data["mmsi"], timestamp))
            
            conn.execute('''
                INSERT INTO positions_history 
                (mmsi, lat, lon, speed, course, true_heading, nav_status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pos_data["mmsi"], pos_data["lat"], pos_data["lon"], 
                  pos_data["speed"], pos_data["course"], pos_data["true_heading"], 
                  pos_data["nav_status"], pos_data["timestamp"]))
            
            print(f"[AIS] Pos: {pos_data['mmsi']} ({pos_data['lat']:.4f}, {pos_data['lon']:.4f})")
        
        elif msg_type == "ShipStaticData":
            static_data = await process_ship_static_data(data_dict)
            if not static_data:
                return
            
            ship_type = get_ship_type_name(static_data.get("ship_type", 0))
            
            conn.execute('''
                INSERT INTO vessels_master (
                    mmsi, name, callsign, vessel_type, dimension_a, dimension_b,
                    dimension_c, dimension_d, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mmsi) DO UPDATE SET
                    name = COALESCE(excluded.name, name),
                    callsign = COALESCE(excluded.callsign, callsign),
                    vessel_type = COALESCE(excluded.vessel_type, vessel_type),
                    dimension_a = COALESCE(excluded.dimension_a, dimension_a),
                    dimension_b = COALESCE(excluded.dimension_b, dimension_b),
                    dimension_c = COALESCE(excluded.dimension_c, dimension_c),
                    dimension_d = COALESCE(excluded.dimension_d, dimension_d),
                    last_updated = excluded.last_updated
            ''', (
                static_data["mmsi"], static_data.get("name"), static_data.get("call_sign"),
                ship_type, static_data.get("dimension_a"), static_data.get("dimension_b"),
                static_data.get("dimension_c"), static_data.get("dimension_d"), timestamp
            ))
            
            print(f"[AIS] Static: {static_data['mmsi']} - {static_data.get('name') or 'Unknown'} ({ship_type})")
        
        conn.commit()
        
    except Exception as e:
        print(f"[AIS] Erro: {e}")
    finally:
        conn.close()

async def ais_listener():
    print(f"Conectando ao Stream: {AIS_WEBSOCKET_URL}")
    
    bbox = os.getenv("AIS_BBOX", "[[[-10, 35], [5, 45]]]")
    try:
        bounding_boxes = json.loads(bbox)
    except:
        bounding_boxes = [[[-10, 35], [5, 45]]]
    
    while True:
        try:
            async with websockets.connect(AIS_WEBSOCKET_URL) as websocket:
                subscribe_msg = {
                    "APIKey": AIS_API_KEY,
                    "BoundingBoxes": bounding_boxes,
                    "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                print(f"Subscreveu. A escutar em {bounding_boxes}...")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await process_ais_message(data)
                    except json.JSONDecodeError:
                        continue
                        
        except websockets.exceptions.ConnectionClosed:
            print("[AIS] Conexão encerrada. A tentar novamente em 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[AIS] Erro: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(ais_listener())
