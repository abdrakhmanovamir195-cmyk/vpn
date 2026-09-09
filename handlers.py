import time
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message

import database as db
import marzban
import payments
import keyboards as kb
import texts
from config import PLANS, CHANNEL_ID, CHANNEL_INVITE_LINK, TRIAL_DAYS, SUPPORT_USERNAME, ADMIN_IDS

router = Router()

def username_for(tg_id: int) -> str:
    return f"tg_{tg_id}"

async def notify_admins(bot: Bot, text: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass

@router.message(CommandStart())
async def start(message: Message):
    await db.create_user(message.from_user.id, username_for(message.from_user.id))
    first_name = message.from_user.first_name or "друг"
    await message.answer(texts.start_text(first_name), reply_markup=kb.main_menu())

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        f"🆘 Если возник вопрос или нужна помощь — напишите нам напрямую: "
        f"<a href='https://t.me/{SUPPORT_USERNAME.lstrip('@')}'>{SUPPORT_USERNAME}</a>",
        disable_web_page_preview=True,
    )

@router.message(Command("legal"))
async def legal_command(message: Message):
    await message.answer(texts.LEGAL_TEXT)

@router.message(Command("currency"))
async def currency_command(message: Message):
    await message.answer(texts.CURRENCY_TEXT)

@router.message(Command("grant"))
async def grant_access(message: Message, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /grant <tg_id> <дней>\nПример: /grant 123456789 30")
        return

    try:
        target_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer("tg_id и дни должны быть числами.")
        return

    username = username_for(target_id)
    await db.create_user(target_id, username)

    existing = await marzban.get_marzban_user(username)
    now = int(time.time())
    if existing and existing.get("expire", 0) > now:
        new_expire = existing["expire"] + days * 86400
        await marzban.update_expire(username, new_expire)
    else:
        new_expire = now + days * 86400
        if existing:
            await marzban.update_expire(username, new_expire)
        else:
            await marzban.create_marzban_user(username, new_expire)

    await db.set_expires(target_id, new_expire)
    link = await marzban.get_subscription_link(username)
    expires_str = time.strftime("%d.%m.%Y", time.localtime(new_expire))

    await message.answer(
        f"✅ Доступ выдан\nПользователь: {target_id}\nДо: {expires_str}\n\nСсылка:\n<code>{link}</code>"
    )

    try:
        await bot.send_message(
            target_id,
            f"🎁 Вам выдан доступ к VPN на {days} дн.!\n\nСсылка:\n<code>{link}</code>\n\n"
            "Инструкцию по подключению смотри в меню бота: /start",
        )
    except Exception:
        await message.answer("⚠️ Не удалось отправить сообщение пользователю.")

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    first_name = call.from_user.first_name or "друг"
    await call.message.edit_text(texts.start_text(first_name), reply_markup=kb.main_menu())

@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await call.message.edit_text(texts.ABOUT_TEXT, reply_markup=kb.back_kb())

@router.callback_query(F.data == "instructions")
async def instructions(call: CallbackQuery):
    await call.message.edit_text(texts.INSTRUCTIONS_TEXT, reply_markup=kb.back_kb())

@router.callback_query(F.data == "plans")
async def plans(call: CallbackQuery):
    await call.message.edit_text(texts.plans_text(), reply_markup=kb.plans_menu())

@router.callback_query(F.data == "trial")
async def trial(call: CallbackQuery, bot: Bot):
    user = await db.get_user(call.from_user.id)
    if user and user["trial_used"]:
        await call.answer("Пробный период уже был использован.", show_alert=True)
        return
    try:
        member = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)
        if member.status not in ("member", "administrator", "creator"):
            raise ValueError
    except Exception:
        await call.message.edit_text(
            f"Чтобы получить пробный период, подпишись на канал:\n{CHANNEL_INVITE_LINK}\n\n"
            "После подписки нажми «Пробный период» ещё раз.",
            reply_markup=kb.back_kb(),
        )
        return

    username = username_for(call.from_user.id)
    expire_ts = int(time.time()) + TRIAL_DAYS * 86400
    await marzban.create_marzban_user(username, expire_ts)
    await db.set_trial_used(call.from_user.id)
    await db.set_expires(call.from_user.id, expire_ts)
    link = await marzban.get_subscription_link(username)

    await notify_admins(
        bot,
        f"🎁 Выдан пробный период\nПользователь: {call.from_user.full_name} (id {call.from_user.id})\n"
        f"Срок: {TRIAL_DAYS} дн.",
    )

    await call.message.edit_text(
        f"🎁 Пробный период на {TRIAL_DAYS} дня активирован!\n\nСсылка подписки:\n<code>{link}</code>\n\n"
        "Инструкцию по подключению смотри в главном меню.",
        reply_markup=kb.back_kb(),
    )

@router.callback_query(F.data.startswith("buy_"))
async def buy(call: CallbackQuery, bot: Bot):
    plan_key = call.data.removeprefix("buy_")
    plan = PLANS.get(plan_key)
    if not plan:
        await call.answer("Тариф недоступен.", show_alert=True)
        return
    bot_info = await bot.get_me()
    payment_id, url = payments.create_payment(
        plan["price"], f"Подписка VPN: {plan['title']}", bot_info.username
    )
    await db.create_payment(payment_id, call.from_user.id, plan_key, plan["price"])
    await call.message.edit_text(
        f"Тариф: {plan['title']} — {plan['price']}₽\n\nОплати по ссылке:\n{url}\n\n"
        "После оплаты нажми кнопку ниже.",
        reply_markup=kb.pay_check_kb(payment_id),
    )

@router.callback_query(F.data.startswith("check_"))
async def check_payment(call: CallbackQuery, bot: Bot):
    payment_id = call.data.removeprefix("check_")
    status = payments.check_payment(payment_id)
    if status != "succeeded":
        await call.answer("Оплата ещё не поступила. Попробуй через минуту.", show_alert=True)
        return

    payment_row = await db.get_payment(payment_id)
    if payment_row["status"] == "succeeded":
        await call.answer("Уже активировано ✅", show_alert=True)
        return

    plan = PLANS[payment_row["plan_key"]]
    tg_id = payment_row["tg_id"]
    username = username_for(tg_id)

    existing = await marzban.get_marzban_user(username)
    now = int(time.time())
    if existing and existing.get("expire", 0) > now:
        new_expire = existing["expire"] + plan["days"] * 86400
        await marzban.update_expire(username, new_expire)
    else:
        new_expire = now + plan["days"] * 86400
        if existing:
            await marzban.update_expire(username, new_expire)
        else:
            await marzban.create_marzban_user(username, new_expire)

    await db.set_expires(tg_id, new_expire)
    await db.set_payment_status(payment_id, "succeeded")
    link = await marzban.get_subscription_link(username)

    await notify_admins(
        bot,
        f"💰 Новая оплата\nПользователь: {call.from_user.full_name} (id {tg_id})\n"
        f"Тариф: {plan['title']} — {plan['price']}₽\n"
        f"Действует до: {time.strftime('%d.%m.%Y', time.localtime(new_expire))}",
    )

    await call.message.edit_text(
        f"✅ Оплата прошла!\n\nПодписка активна до "
        f"{time.strftime('%d.%m.%Y', time.localtime(new_expire))}\n\nСсылка:\n<code>{link}</code>",
        reply_markup=kb.back_kb(),
    )

@router.callback_query(F.data == "mykeys")
async def mykeys(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    if not user or user["expires_at"] == 0:
        await call.message.edit_text("У тебя пока нет активной подписки.", reply_markup=kb.back_kb())
        return
    username = username_for(call.from_user.id)
    link = await marzban.get_subscription_link(username)
    expires = time.strftime("%d.%m.%Y", time.localtime(user["expires_at"]))
    status = "🟢 активна" if user["expires_at"] > time.time() else "🔴 истекла"
    await call.message.edit_text(
        f"🔑 <b>Твой ключ</b>\n\nСтатус: {status}\nДействует до: {expires}\n\n<code>{link}</code>",
        reply_markup=kb.mykeys_kb(),
    )

@router.callback_query(F.data == "reissue")
async def reissue(call: CallbackQuery):
    username = username_for(call.from_user.id)
    link = await marzban.reissue_key(username)
    await call.message.edit_text(
        f"🔄 Ключ перевыпущен, старая ссылка больше не работает.\n\nНовая:\n<code>{link}</code>",
        reply_markup=kb.mykeys_kb(),
    )
