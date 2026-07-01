import asyncio
import logging
import os
import sys

from aiohttp import web
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


async def health(request):
    return web.Response(text="Bot is running")


async def start_http_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info("HTTP server started on port %s", port)


async def start_bot():
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


async def main():
    await start_http_server()
    await start_bot()


if __name__ == "__main__":
    asyncio.run(main())
