import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError

from config import get_settings
from database import MemberDatabase
from handlers import commands, members

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

NETWORK_HELP = (
    "Нет связи с api.telegram.org.\n"
    "1) Включите VPN на этом ПК\n"
    "2) Или добавьте в .env: PROXY_URL=http://127.0.0.1:7890\n"
    "3) Подбор прокси: python find_proxy.py"
)


async def main() -> None:
    settings = get_settings()
    db = MemberDatabase(settings.db_path)

    session = AiohttpSession(proxy=settings.proxy_url) if settings.proxy_url else None
    bot = Bot(
        token=settings.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    if settings.proxy_url:
        logger.info("Используется прокси: %s", settings.proxy_url)

    try:
        me = await bot.get_me()
    except TelegramNetworkError as exc:
        logger.error(NETWORK_HELP)
        raise SystemExit(1) from exc

    dp = Dispatcher()
    dp["db"] = db

    dp.include_router(commands.router)
    dp.include_router(members.router)

    logger.info("Бот запущен: @%s", me.username)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
