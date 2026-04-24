import asyncio
import websockets
import json
import sys

async def test():
    api_key = "04c9121b3d0d922546eba9e50c616b7d56833011"
    bbox = [[-10, 35], [5, 45]]
    
    print("Starting...", flush=True, file=sys.stderr)
    
    try:
        ws = await websockets.connect("wss://stream.aisstream.io/v0/stream")
        print("Connected", flush=True, file=sys.stderr)
        
        sub = {"APIKey": api_key, "BoundingBoxes": bbox}
        await ws.send(json.dumps(sub))
        print("Sent subscription", flush=True, file=sys.stderr)
        
        print("Waiting for message...", flush=True, file=sys.stderr)
        
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            print(f"Got: {msg[:200]}", flush=True, file=sys.stderr)
            return True
        except asyncio.TimeoutError:
            print("TIMEOUT after 15s", flush=True, file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error: {e}", flush=True, file=sys.stderr)
        return False

result = asyncio.run(test())
print(f"Result: {result}", flush=True, file=sys.stderr)