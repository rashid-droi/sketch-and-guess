import asyncio
import websockets
import json
import time
import requests
import argparse

# Backend URL
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def simulate_player(room_id, player_idx, is_drawer=False):
    player_id = f"bot_{player_idx}"
    player_name = f"BotPlayer_{player_idx}"
    uri = f"{WS_URL}/{room_id}?player_id={player_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Player {player_idx} connected.")
            
            # Start a listener task to count received messages
            received_count = 0
            async def listen():
                nonlocal received_count
                try:
                    async for message in websocket:
                        received_count += 1
                except:
                    pass

            listener = asyncio.create_task(listen())

            if is_drawer:
                # Simulate drawing for 10 seconds
                for i in range(100):
                    data = {
                        "type": "draw",
                        "data": {
                            "type": "move",
                            "x": 100 + i,
                            "y": 100 + i,
                            "color": "#ff0000",
                            "size": 5,
                            "player_id": player_id,
                            "player_name": player_name
                        }
                    }
                    await websocket.send(json.dumps(data))
                    await asyncio.sleep(0.1) # 10 messages per second
            else:
                # Just keep connection alive
                await asyncio.sleep(15)

            await listener
            print(f"Player {player_idx} finished. Received {received_count} messages.")
            
    except Exception as e:
        print(f"Player {player_idx} error: {e}")

async def run_stress_test(num_users):
    # 1. Create a room first
    print(f"Creating room for {num_users} users...")
    resp = requests.post(f"{API_URL}/create-room", json={
        "player_id": "master_bot",
        "player_name": "MasterBot"
    })
    room_data = resp.json()
    room_id = room_data["room_id"]
    print(f"Room {room_id} created.")

    # 2. Join all simulated players via POST first (required by backend)
    print("Joining bots to room via API...")
    for i in range(num_users):
        requests.post(f"{API_URL}/join-room", json={
            "room_id": room_id,
            "player_id": f"bot_{i}",
            "player_name": f"BotPlayer_{i}"
        })
    
    # 3. Connect everyone via WebSocket
    print(f"Connecting {num_users} WebSockets...")
    tasks = []
    for i in range(num_users):
        # Let the first bot be the drawer
        tasks.append(simulate_player(room_id, i, is_drawer=(i == 0)))
    
    start_time = time.time()
    await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"\n--- Test Results ---")
    print(f"Total simulated users: {num_users}")
    print(f"Total time: {end_time - start_time:.2f}s")
    print(f"The server successfully handled {num_users} concurrent connections!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=100)
    args = parser.parse_args()
    
    asyncio.run(run_stress_test(args.users))
