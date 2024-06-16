import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("websockets")

connected_clients                = set()
temperature_measurement_interval = 0.1
camera_picture_interval          = 1

async def server():
    async def echo(websocket, path):
        connected_clients.add(websocket)
        logger.info(f"New client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                logger.info(f"Received message: {message} from {websocket.remote_address}")
                await broadcast(message, websocket)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connection closed with {websocket.remote_address}: {e}")
        finally:
            connected_clients.remove(websocket)
            logger.info(f"Client disconnected: {websocket.remote_address}")

    async with websockets.serve(echo, "localhost", 8765):
        logger.info("Server started on ws://localhost:8765")
        await asyncio.Future() 

async def broadcast(message, sender):
    for client in connected_clients:
        if client != sender and client.open:
            try:
                await client.send(message)
                logger.info(f"Sent {message} to {client.remote_address}")
            except Exception as e:
                logger.error(f"Error sending message to {client.remote_address}: {e}")
        elif not client.open:
            connected_clients.remove(client)

async def client():
    async def send_camera_commands(websocket):
        while True:
            command = {
                "type"   : "command",
                "command": "take_picture"
            }
            await websocket.send(json.dumps(command))
            await asyncio.sleep(camera_picture_interval)

    async def send_temperature_commands(websocket):
        while True:
            command = {
                "type"   : "command",
                "command": "measure_temperature"
            }
            await websocket.send(json.dumps(command))
            await asyncio.sleep(temperature_measurement_interval)

    async def receive_messages(websocket):
        try:
            async for message in websocket:
                logger.info(f"Test client received message: {message}")
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")

    async with websockets.connect("ws://localhost:8765") as websocket:
        receive_task = asyncio.create_task(receive_messages(websocket))
        send_camera_task = asyncio.create_task(send_camera_commands(websocket))
        send_temperature_task = asyncio.create_task(send_temperature_commands(websocket))
        await asyncio.gather(receive_task, send_camera_task, send_temperature_task)

async def main():
    server_task = asyncio.create_task(server())
    client_task = asyncio.create_task(client())
    await asyncio.gather(server_task, client_task)

if __name__ == "__main__":
    asyncio.run(main())