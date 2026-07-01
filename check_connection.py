import asyncio
import sys

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

load_dotenv()

from config import get_settings


async def main() -> None:
    settings = get_settings()
    session = AiohttpSession(proxy=settings.proxy_url) if settings.proxy_url else None
    bot = Bot(token=settings.bot_token, session=session)

    try:
        me = await bot.get_me()
        print(f"OK: @{me.username} ({me.first_name})")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        print(
            "\nНет доступа к api.telegram.org. Включите VPN или добавьте в .env:\n"
            "PROXY_URL=http://127.0.0.1:ПОРТ",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
