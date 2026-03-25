import logging
import json
import os
import time
import functools
from config import LOG_FILE, CONFIG_FILE, DATA_DIR
API_KEYS_FILE = os.path.join(DATA_DIR, 'api_keys.json')


def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_api_keys():
    """Load API keys from secure JSON file"""
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load API keys: {e}")
    return {}


def retry_with_recovery(max_retries=3, delay=1, recovery_func=None):
    """
    Decorator to retry a function with a recovery step in between.
    Useful for self-healing automation.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.getLogger('Retry').warning(f"Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise e
                    
                    if recovery_func:
                        try:
                            logging.getLogger('Retry').info("Executing recovery function...")
                            recovery_func()
                        except Exception as rec_e:
                            logging.getLogger('Retry').error(f"Recovery failed: {rec_e}")
                            
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
