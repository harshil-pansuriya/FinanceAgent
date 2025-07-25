import logging
import os

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG) 
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler('logs/app.log') 
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
    
    return logger

# Initiate the logger instance
logger = setup_logger()