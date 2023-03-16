from aiogram import Bot
from aiogram import Dispatcher
# from aiogram.methods.set_my_commands import BotCommand

# My Modules
from bot.misc.env import Keys

from bot.tg_module.handlers import admin
from bot.tg_module.handlers import user


'''
async def set_default_commands(bot_tg: Bot) -> None:
    print(await bot_tg.set_my_commands(commands=[
        BotCommand(command="start", descriptions="Запуск бота"),
        BotCommand(command="personal_area", descriptions="Личный кабинет"),
        BotCommand(command="help", descriptions="Помощь"),
        BotCommand(command="show_keyboard", descriptions="Показать клавиатуру")
    ]))
'''


async def start_telegram_bot() -> None:
    """Запускаем бота"""

    bot_tg = Bot(token=Keys.TG_TOKEN, parse_mode='HTML')
    dp = Dispatcher()

    # await set_default_commands(bot_tg)

    dp.include_router(admin.router)
    dp.include_router(user.router)

    await bot_tg.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot_tg)
