import aiosqlite
import time
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    marzban_username TEXT UNIQUE,
    trial_used INTEGER DEFAULT 0,
    expires_at INTEGER DEFAULT 0,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    tg_id INTEGER,
    plan_key TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending',
    created_at INTEGER
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

async def get_user(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
        return await cur.fetchone()

async def create_user(tg_id: int, marzban_username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tg_id, marzban_username, created_at) VALUES (?, ?, ?)",
            (tg_id, marzban_username, int(time.time())),
        )
        await db.commit()

async def set_trial_used(tg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET trial_used=1 WHERE tg_id=?", (tg_id,))
        await db.commit()

async def set_expires(tg_id: int, expires_at: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET expires_at=? WHERE tg_id=?", (expires_at, tg_id))
        await db.commit()

async def create_payment(payment_id: str, tg_id: int, plan_key: str, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (id, tg_id, plan_key, amount, created_at) VALUES (?, ?, ?, ?, ?)",
            (payment_id, tg_id, plan_key, amount, int(time.time())),
        )
        await db.commit()

async def set_payment_status(payment_id: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE payments SET status=? WHERE id=?", (status, payment_id))
        await db.commit()

async def get_payment(payment_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE id=?", (payment_id,))
        return await cur.fetchone()

async def get_all_active_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE expires_at > 0")
        return await cur.fetchall()
