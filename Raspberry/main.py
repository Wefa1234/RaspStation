import asyncio
import json

from websocket.client import WebSocketClient
from sensors.managers import BME280Manager, CameraManager
from logger.logger import RaspberryPiLogger
from data.structures import BME280Data, CameraData

# Configs
WS_URI          = "ws://localhost:8765"
CLIENT_LOCATION = 'Olohuone'
LOGGER_LEVEL    = 'INFO'

async def populate_sensor_queue(queue, manager):
    async for data in manager.get_sensor_data():
        await queue.put(data)

async def command_dispatcher(command_queue, bme280_manager, camera_manager):
    while True:
        command = await command_queue.get()
        await bme280_manager.evaluate_command(command)
        await camera_manager.evaluate_command(command)
        command_queue.task_done()

async def main():
    logger = RaspberryPiLogger(logger_name="MAIN", file_name="main.log", level = LOGGER_LEVEL)
    
    sensor_queue  = asyncio.Queue()
    command_queue = asyncio.Queue()

    client = WebSocketClient(WS_URI, LOGGER_LEVEL)
    logger.info(f"WebSocketClient initialized: {client}")

    bme280 = BME280Manager(CLIENT_LOCATION, LOGGER_LEVEL)
    logger.info(f"BME280Manager initialized: {bme280}")

    camera = CameraManager(CLIENT_LOCATION, LOGGER_LEVEL)
    logger.info(f"CameraManager initialized: {camera}")

    tasks = [
        asyncio.create_task(client.connect(command_queue)),
        asyncio.create_task(populate_sensor_queue(sensor_queue, bme280)),
        asyncio.create_task(populate_sensor_queue(sensor_queue, camera)),
        asyncio.create_task(client.handle_outgoing_data(sensor_queue)),
        asyncio.create_task(command_dispatcher(command_queue, bme280, camera))
    ]   
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())