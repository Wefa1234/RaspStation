import random
import asyncio
import json
from abc import ABC, abstractmethod

from logger.logger import RaspberryPiLogger

class Manager:
    def __init__(
            self, 
            location, 
            logger_name, 
            file_name, 
            command_to_match,
            logger_level = 'INFO'):
        
        self.logger   = RaspberryPiLogger(
            logger_name = logger_name,
            file_name   = file_name,
            level       = logger_level
        )
        self.location         = location
        self.logger_name      = logger_name
        self.file_name        = file_name
        self.logger_level     = logger_level
        self.command_to_match = command_to_match
        self.command_trigger  = asyncio.Event()


    async def main(self, incoming_queue, outgoing_queue):
        connection_retries = 5
        backoff_factor     = 2

        for connection_attempt in range(connection_retries):
            try:
                tasks = [
                    self._get_sensor_data(outgoing_queue),
                    self._evaluate_command(incoming_queue, self.command_to_match),
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
                    asyncio.get_running_loop().stop()


    @abstractmethod 
    async def _get_sensor_data(self, queue):
        pass


    async def _evaluate_command(self, queue, command_to_match):
        while True:
            command = await queue.get()
            if command["command"] == command_to_match:
                self.command_trigger.set()
                self.logger.debug(f"Activated {command_to_match} event")


    def __str__(self):
        attributes = ", ".join(f"{key}={value}" for key, value in vars(self).items())
        return f"Manager({attributes})"




class BME280(Manager):
    def __init__(self, location, logger_level = 'INFO'):
        super().__init__(
            location, 
            logger_name      = "BME280",
            file_name        = "bme280.log",
            command_to_match = "measure_temperature",
            logger_level     = logger_level
        )

    async def _get_sensor_data(self, queue):
        while True:
            await self.command_trigger.wait()
            data = {
                "type"    : "sensor_data",
                "sensor"  : "BME280",
                "location": self.location,
                "data": {
                    "temperature": 25 + random.uniform(-0.5, 0.5),
                    "humidity": 50 + random.uniform(-5, 5)
                }
            }
            self.logger.debug(f"Measured temperature: {data}")
            self.command_trigger.clear()
            await queue.put(json.dumps(data))
    


class Camera(Manager):
    def __init__(self, location, logger_level = 'INFO'):
        super().__init__(
            location, 
            logger_name      = "CAMERA",
            file_name        = "camera.log",
            command_to_match = "take_picture",
            logger_level     = logger_level
        )

    async def get_sensor_data(self, queue):
        while True:
            await self.command_trigger.wait()
            data = {
                "type"    : "picture",
                "sensor"  : "camera",
                "location": self.location,
                "data": {
                    "picture": "picture.jpg"
                }
            }
            self.logger.debug(f"Taken picture: {data}")
            self.command_trigger.clear()
            await queue.put(json.dumps(data))
