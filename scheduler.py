import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database as db
import marzban

async def check_expirations(bot):
    users = await db.get_all_active_users()
    now = int(time.time())
    for user in users:
        if user["expires_at"] < now:
            username = user["marzban_username"]
            existing = await marzban.get_marzban_user(username)
            if existing and existing["status"] != "disabled":
                await marzban.disable_user(username)
                try:
                    await bot.send_message(
                        user["tg_id"],
                        "⛔ Твоя подписка истекла. Продли её в разделе «Тарифы».",
                    )
                except Exception:
                    pass

def start_scheduler(bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expirations, "interval", minutes=10, args=[bot])
    scheduler.start()
    return scheduler
