import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""

# Never crash on missing env in import-time (production safe).
_admin_raw = os.getenv("ADMIN_ID")
try:
    ADMIN_ID = int(_admin_raw) if _admin_raw else 0
except ValueError:
    ADMIN_ID = 0