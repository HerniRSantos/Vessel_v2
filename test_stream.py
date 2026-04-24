#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test():
    api_key = "04c9121b3d0d922546eba9e50c616b7d56833011"
    bbox = [[-10, 35], [5, 45]]
    print("Starting AIS test...", flush=True)
    try:
        ws = await websockets.connect("wss://stream.aisstream.io/v0/stream")
        print("Connected to stream", flush=True)
        sub = {"APIKey": api_key, "BoundingBoxes": [bbox]}
        await ws.send(json.dumps(sub))
        print("Sent subscription", flush=True)
        print("Waiting for messages...", flush=True)
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            data = json.loads(msg)
            mt = data.get("MessageType", "?")
            print(f"Got message type: {mt}", flush=True)
            return True
        except asyncio.TimeoutError:
            print("TIMEOUT - no messages in 15 seconds", flush=True)
            return False
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return False

result = asyncio.run(test())
print(f"Test result: {result}")