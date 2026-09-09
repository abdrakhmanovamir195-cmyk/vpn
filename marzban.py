import aiohttp
import time
import uuid as uuid_lib
from config import MARZBAN_API_URL, MARZBAN_ADMIN_USER, MARZBAN_ADMIN_PASS

_token_cache = {"token": None, "expires": 0}

async def _get_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{MARZBAN_API_URL}/api/admin/token",
            data={"username": MARZBAN_ADMIN_USER, "password": MARZBAN_ADMIN_PASS},
        ) as resp:
            data = await resp.json()
            _token_cache["token"] = data["access_token"]
            _token_cache["expires"] = time.time() + 3000
            return _token_cache["token"]

async def _headers():
    token = await _get_token()
    return {"Authorization": f"Bearer {token}"}

async def create_marzban_user(username: str, expire_ts: int) -> dict:
    new_uuid = str(uuid_lib.uuid4())
    payload = {
        "username": username,
        "proxies": {"vless": {"id": new_uuid, "flow": "xtls-rprx-vision"}},
        "inbounds": {"vless": ["VLESS-Reality"]},
        "expire": expire_ts,
        "data_limit": 0,
        "status": "active",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{MARZBAN_API_URL}/api/user", json=payload, headers=await _headers()
        ) as resp:
            return await resp.json()

async def get_marzban_user(username: str) -> dict | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MARZBAN_API_URL}/api/user/{username}", headers=await _headers()
        ) as resp:
            if resp.status == 404:
                return None
            return await resp.json()

async def update_expire(username: str, expire_ts: int):
    async with aiohttp.ClientSession() as session:
        await session.put(
            f"{MARZBAN_API_URL}/api/user/{username}",
            json={"expire": expire_ts, "status": "active"},
            headers=await _headers(),
        )

async def disable_user(username: str):
    async with aiohttp.ClientSession() as session:
        await session.put(
            f"{MARZBAN_API_URL}/api/user/{username}",
            json={"status": "disabled"},
            headers=await _headers(),
        )

async def reissue_key(username: str) -> str:
    new_uuid = str(uuid_lib.uuid4())
    async with aiohttp.ClientSession() as session:
        async with session.put(
            f"{MARZBAN_API_URL}/api/user/{username}",
            json={"proxies": {"vless": {"id": new_uuid, "flow": "xtls-rprx-vision"}}},
            headers=await _headers(),
        ) as resp:
            data = await resp.json()
            return data["links"][0] if data.get("links") else ""

async def get_subscription_link(username: str) -> str:
    user = await get_marzban_user(username)
    if not user:
        return ""
    return f"{MARZBAN_API_URL}{user.get('subscription_url', '')}"
