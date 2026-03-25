import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
ENV_FILE = BASE_DIR / ".env"
LOG_FILE = LOGS_DIR / "nova.log"
CONFIG_FILE = DATA_DIR / "config.json"



def load_dotenv_file():
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv_file()

APP_NAME = os.getenv("APP_NAME", "Nova")
WAKE_WORD = os.getenv("WAKE_WORD", "nova")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

for directory in (DATA_DIR, LOGS_DIR):
    directory.mkdir(exist_ok=True)
