import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")

ADMIN_ID_STR = os.getenv('ADMIN_ID')
if not ADMIN_ID_STR:
    raise ValueError("ADMIN_ID not found in environment variables")
ADMIN_ID = int(ADMIN_ID_STR)