import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@dump1991")

MARZBAN_API_URL = os.getenv("MARZBAN_API_URL", "").rstrip("/")
MARZBAN_ADMIN_USER = os.getenv("MARZBAN_ADMIN_USER")
MARZBAN_ADMIN_PASS = os.getenv("MARZBAN_ADMIN_PASS")

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK")

TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "3"))

DB_PATH = "vpnbot.db"

PLANS = {
    "1m":  {"title": "1 месяц",    "days": 30,  "price": 200},
    "3m":  {"title": "3 месяца",   "days": 90,  "price": 600},
    "6m":  {"title": "6 месяцев",  "days": 180, "price": 1200},
    "12m": {"title": "12 месяцев", "days": 365, "price": 2300},
}
