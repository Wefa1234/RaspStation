import asyncio
import websockets
import json
import ssl

from logger.logger import RaspberryPiLogger

class WebSocketClient:
    def __init__(self, uri, path_to_certs = None, logger_level = 'INFO'):
        self.logger    = RaspberryPiLogger(logger_name = "WEBSOCKET", file_name = "websocket.log", level = logger_level)
        self.uri       = uri
        self.websocket = None
        self.path_to_certs = path_to_certs
        self.ssl_context = None


    async def main(self, incoming_queue, outgoing_queue):
        connection_retries = 5
        backoff_factor     = 2

        if self.path_to_certs:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_verify_locations(f'{self.path_to_certs}/ca.crt')
            ssl_context.load_cert_chain(f'{self.path_to_certs}/client.crt', f'{self.path_to_certs}/client.key')
            self.ssl_context = ssl_context            
        
        for connection_attempt in range(connection_retries):
            try:
                tasks = [
                    self._connect(),
                    self._handle_incoming_data(incoming_queue),
                    self._handle_outgoing_data(outgoing_queue)
                ]
                await asyncio.gather(*tasks)
                break 
            except Exception as e:
                self.logger.error(f"Error in main function: {e}")
                if connection_attempt < connection_retries - 1:
                    wait_time = backoff_factor * (2 ** connection_attempt)
                    self.logger.info(f"Retrying main function in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Main function failed after multiple attempts.")
                    await self.disconnect()
                    asyncio.get_running_loop().stop()


    async def _connect(self):
        connection_retries = 5
        backoff_factor     = 0.1

        for connection_attempt in range(connection_retries):
            try:
                self.logger.info("Connecting to the server")
                self.websocket = await websockets.connect(self.uri, ssl=self.ssl_context)
                self.logger.info("WebSocket connection successful")
                break
            except Exception as e:
                self.logger.error(f"Error connecting to the server: {e}")
                if connection_attempt < connection_retries - 1:
                    wait_time = backoff_factor * (2 ** connection_attempt)
                    self.logger.info(f"Retrying connection in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Failed to connect to the server after multiple attempts.")
                    raise e
                    

    async def _handle_incoming_data(self, queue):
        while True:
            try:
                if self.websocket and self.websocket.open:
                    message = json.loads(await self.websocket.recv())
                    self.logger.debug(f"Received message: {message}")
                    await queue.put(message)
                else:
                    self.logger.debug("Waiting incoming data")
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in _handle_incoming_data: {e}")    
                raise e


    async def _handle_outgoing_data(self, queue):
        while True:
            message = await queue.get()
            try:
                if self.websocket and self.websocket.open:
                    await self.websocket.send(message)
                    self.logger.debug(f"Sent message: {message}")
                    queue.task_done()
                else:
                    self.logger.debug("Waiting in sending data")
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in _handle_outgoing_data: {e}")
                raise e


    async def disconnect(self):
        if self.websocket and self.websocket.open:
            await self.websocket.close()
            self.logger.error("Disconnected from the server")   
    
    def __str__(self):
        attributes = ", ".join(f"{key}={value}" for key, value in vars(self).items())
        return f"WebSocketClient({attributes})"
