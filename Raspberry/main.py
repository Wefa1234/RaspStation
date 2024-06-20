import asyncio
import json

from websocket.client import WebSocketClient
from sensors.managers import BME280, Camera
from logger.logger import RaspberryPiLogger
from data.structures import BME280Data, CameraData

# Configs
WS_URI          = "ws://localhost:8765"
CLIENT_LOCATION = 'Olohuone'
LOGGER_LEVEL    = 'INFO'

async def main():
    logger = RaspberryPiLogger(logger_name="MAIN", file_name="main.log", level = LOGGER_LEVEL)
    
    sensor_queue  = asyncio.Queue()
    command_queue = asyncio.Queue()

    client = WebSocketClient(WS_URI, LOGGER_LEVEL)
    logger.info(f"WebSocketClient initialized: {client}")

    bme280 = BME280(CLIENT_LOCATION, LOGGER_LEVEL)
    logger.info(f"BME280 initialized: {bme280}")

    camera = Camera(CLIENT_LOCATION, LOGGER_LEVEL)
    logger.info(f"Camera initialized: {camera}")

    tasks = [
        asyncio.create_task(
            client.main(
                incoming_queue = command_queue, 
                outgoing_queue = sensor_queue
            )
        ),
        asyncio.create_task(
            bme280.main(
                incoming_queue = command_queue, 
                outgoing_queue = sensor_queue
            )
        ),
        asyncio.create_task(
            camera.main(
                incoming_queue = command_queue, 
                outgoing_queue = sensor_queue
            )
        ),
    ]   
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())