import logging
import os

class RaspberryPiLogger(logging.Logger):
    def __init__(self, logger_name, file_name, level='INFO', path="logs"):
        super().__init__(logger_name, level)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # Set up the console handler
        handler   = logging.StreamHandler()
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.addHandler(handler)
        self.propagate = False

        # Set up the file handler
        if not os.path.exists(path):
            os.makedirs(path)
        file_handler   = logging.FileHandler(os.path.join(path, file_name))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        self.addHandler(file_handler)

        # Prevents log messages from being propagated to the root logger
        self.propagate = False