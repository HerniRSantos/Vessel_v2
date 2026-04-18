import asyncio
import websockets
import json
from datetime import datetime
from database import get_db_connection

# Socket do parceiro de AIS open source
AIS_WEBSOCKET_URL = "wss://stream.aisstream.io/v0/stream"
AIS_API_KEY = "dummy_key_to_be_replaced_by_dot_env" # O user tem as keys no dot env.

async def process_ais_message(data_dict: dict):
    if "MessageType" not in data_dict:
        return
        
    msg_type = data_dict["MessageType"]
    if msg_type == "PositionReport":
        report = data_dict["Message"]["PositionReport"]
        mmsi = str(report.get("UserID"))
        lat = report.get("Latitude")
        lon = report.get("Longitude")
        speed = report.get("Sog", 0)
        course = report.get("Cog", 0)
        true_heading = report.get("TrueHeading", 0)
        nav_status = report.get("NavigationalStatus", 0)
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        conn = get_db_connection()
        try:
            # 1. Atualizar ou inserir Vaso Genérico na Master (o detalhe é feito pelo OSINT)
            conn.execute('''
                INSERT INTO vessels_master (mmsi, last_updated) 
                VALUES (?, ?)
                ON CONFLICT(mmsi) DO UPDATE SET last_updated = excluded.last_updated
            ''', (mmsi, timestamp))
            
            # 2. Inserir a posição no Histórico
            conn.execute('''
                INSERT INTO positions_history 
                (mmsi, lat, lon, speed, course, true_heading, nav_status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (mmsi, lat, lon, speed, course, true_heading, nav_status, timestamp))
            
            conn.commit()
            print(f"[AIS] Nova Posição: {mmsi} ({lat}, {lon}) às {timestamp}")
            
        except Exception as e:
            print(f"Erro a inserir: {e}")
        finally:
            conn.close()

async def ais_listener():
    print(f"Conectando ao Stream: {AIS_WEBSOCKET_URL}")
    while True:
        try:
            async with websockets.connect(AIS_WEBSOCKET_URL) as websocket:
                subscribe_msg = {
                    "APIKey": AIS_API_KEY,
                    "BoundingBoxes": [[[-90, -180], [90, 180]]], # Global Box para exemplo
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("Subscreveu com sucesso. A escutar...")
                
                async for message in websocket:
                    data = json.loads(message)
                    await process_ais_message(data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("[AIS] Conexão encerrada pelo servidor. Tentando novamente...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[AIS] Erro generalizado: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(ais_listener())
