import logging
import os
from ..config.settings import settings

def setup_logging():
    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(settings.LOG_DIR, "system.log")),
            logging.StreamHandler()
        ]
    )
    # Silence noisy libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
