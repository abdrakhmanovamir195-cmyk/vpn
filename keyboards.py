from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from config import PLANS, SUPPORT_USERNAME

def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Тарифы", callback_data="plans")
    kb.button(text="🎁 Пробный период", callback_data="trial")
    kb.button(text="🔑 Мои ключи", callback_data="mykeys")
    kb.button(text="📖 Инструкция", callback_data="instructions")
    kb.button(text="ℹ️ О нас", callback_data="about")
    kb.button(text="❓ Помощь", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")
    kb.adjust(1)
    return kb.as_markup()

def plans_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, plan in PLANS.items():
        kb.button(text=f"{plan['title']} — {plan['price']}₽", callback_data=f"buy_{key}")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def pay_check_kb(payment_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Я оплатил", callback_data=f"check_{payment_id}")
    kb.adjust(1)
    return kb.as_markup()

def mykeys_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Перевыпустить ключ", callback_data="reissue")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="back_main")
    return kb.as_markup()
