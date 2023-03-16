from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def default(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
    """Дефолтная клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Личный кабинет")
    builder.button(text="Каталог")
    return builder.as_markup(resize_keyboard=resize_keyboard)
