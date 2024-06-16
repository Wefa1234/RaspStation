import random
import asyncio
import json

from logger.logger import RaspberryPiLogger


class BME280Manager:
    def __init__(self, location, logger_level = 'INFO'):
        self.logger      = RaspberryPiLogger(logger_name = "BME280", file_name = "bme280.log", level = logger_level)
        self.temperature = 25
        self.location    = location
        self.measure_temperature_event = asyncio.Event()

    def __str__(self):
        return f"BME280Manager(temperature={self.temperature}, location={self.location})"

    async def get_sensor_data(self):
        while True:
            await self.measure_temperature_event.wait()
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
            self.measure_temperature_event.clear()
            yield json.dumps(data)
    

    async def evaluate_command(self, command):
        if command["command"] == "measure_temperature":
            self.measure_temperature_event.set()
            self.logger.debug(f"Activated measure temperature event")


class CameraManager:
    def __init__(self, location, logger_level = 'INFO'):
        self.logger   = RaspberryPiLogger(logger_name = "CAMERA", file_name = "camera.log", level = logger_level)
        self.location = location
        self.take_picture_event = asyncio.Event()
    
    def __str__(self):
        return f"CameraManager(location={self.location})"

    async def get_sensor_data(self):
        while True:
            await self.take_picture_event.wait()
            data = {
                "type"    : "picture",
                "sensor"  : "camera",
                "location": self.location,
                "data": {
                    "picture": "picture.jpg"
                }
            }
            self.logger.debug(f"Taken picture: {data}")
            self.take_picture_event.clear()
            yield json.dumps(data)

    async def evaluate_command(self, command):
        if command["command"] == "take_picture":
            self.take_picture_event.set()
            self.logger.debug(f"Activated take picture event")
