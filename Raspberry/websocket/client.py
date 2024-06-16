import asyncio
import websockets
import json

from logger.logger import RaspberryPiLogger

class WebSocketClient:
    def __init__(self, uri, logger_level = 'INFO'):
        self.logger    = RaspberryPiLogger(logger_name = "WEBSOCKET", file_name = "websocket.log", level = logger_level)
        self.uri       = uri
        self.websocket = None
        self.send_fail_count = 0 


    async def connect(self, queue):
        connection_retries = 5
        backoff_factor     = 2
        for connection_attempt in range(connection_retries):
            try:
                self.logger.info("Connecting to the server")
                self.websocket = await websockets.connect(self.uri)
                self.logger.info("WebSocket connection successful")
                await self.handle_incoming_data(queue)
            except Exception as e:
                self.logger.error(f"Error connecting to the server: {e}")
                if connection_attempt < connection_retries - 1:
                    wait_time = backoff_factor * (2 ** connection_attempt)
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Failed to connect to the server after multiple attempts.")
                    await self.disconnect()


    async def handle_incoming_data(self, queue):
        while True:
            try:
                message = json.loads(await self.websocket.recv())
                self.logger.debug(f"Received message: {message}")
                await queue.put(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.info("Connection was closed by the server.")
                await self.disconnect()
            except Exception as e:
                self.logger.error(f"Error while receiving messages: {e}")
                await self.disconnect()
    

    async def handle_outgoing_data(self, queue):
        while True:
            message = await queue.get()
            if self.websocket and self.websocket.open:
                await self.websocket.send(message)
                self.logger.debug(f"Sent message: {message}")
                queue.task_done()


    async def disconnect(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
            self.logger.error("Disconnected from the server")   
        exit()

    def __str__(self):
        return f"WebSocketClient(uri={self.uri})"
