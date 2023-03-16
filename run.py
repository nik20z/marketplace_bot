import asyncio
from loguru import logger

from bot.tg_module import start_telegram_bot

from bot.database import utils


if __name__ == '__main__':
    logger.add("bot/log/info.log",
               format="{time:HH:mm:ss} {level} {module} {function} {message}",
               level="INFO",
               rotation="00:00",
               compression="zip",
               serialize=False,
               enqueue=True)

    with logger.catch():

        utils.create_extension()
        utils.create_table()
        utils.create_view()
        utils.create_functions()

        asyncio.run(start_telegram_bot())
