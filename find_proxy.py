import asyncio
import re
import subprocess
import sys

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from config import get_settings

COMMON_PORTS = [
    7890, 7891, 7897, 1080, 10808, 10809, 1087, 8080, 8888, 9090,
    12334, 12335, 2334, 2080, 8118, 9050, 6152, 33210,
]

SKIP_PORTS = {5354, 27015, 9930, 9983}  # системные, не прокси


def discover_local_ports() -> list[int]:
    ports: set[int] = set()
    try:
        output = subprocess.check_output(["netstat", "-an"], text=True, errors="ignore")
        for match in re.finditer(r"127\.0\.0\.1:(\d+)\s+.*LISTENING", output):
            port = int(match.group(1))
            if port not in SKIP_PORTS:
                ports.add(port)
    except (subprocess.CalledProcessError, OSError):
        pass
    return sorted(ports)


def build_proxy_candidates() -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(url: str) -> None:
        if url not in seen:
            seen.add(url)
            candidates.append(url)

    for port in COMMON_PORTS:
        add(f"http://127.0.0.1:{port}")
        add(f"socks5://127.0.0.1:{port}")

    for port in discover_local_ports():
        add(f"http://127.0.0.1:{port}")
        add(f"socks5://127.0.0.1:{port}")

    return candidates


async def try_connect(proxy: str | None) -> bool:
    settings = get_settings()
    session = AiohttpSession(proxy=proxy) if proxy else None
    bot = Bot(token=settings.bot_token, session=session)
    try:
        me = await bot.get_me()
        if proxy:
            print(f"@{me.username}", end=" ")
        return True
    except Exception:
        return False
    finally:
        await bot.session.close()


async def main() -> None:
    print("Проверка прямого подключения...")
    if await try_connect(None):
        print("OK: VPN/интернет работает, прокси не нужен.")
        return

    local_ports = discover_local_ports()
    print("Прямое подключение не работает.")
    if local_ports:
        print(f"Найдены локальные порты: {', '.join(map(str, local_ports))}")
    else:
        print("На ПК не запущен VPN/прокси (нет открытых портов).")
    print("\nИщу рабочий прокси...\n")

    for proxy in build_proxy_candidates():
        print(f"  {proxy} ...", end=" ", flush=True)
        if await try_connect(proxy):
            print("OK!")
            print(f"\nДобавьте в файл .env:\nPROXY_URL={proxy}\n")
            print("Затем запустите start.bat снова.")
            return
        print("нет")

    print(
        "\n" + "=" * 50 + "\n"
        "VPN НА ЭТОМ ПК НЕ ЗАПУЩЕН — бот так не заработает.\n\n"
        "ВАРИАНТ А — VPN на компьютере:\n"
        "  1. Скачайте Hiddify: https://github.com/hiddify/hiddify-app/releases\n"
        "  2. Добавьте подписку (ссылку от VPN-провайдера)\n"
        "  3. Нажмите «Подключить» и дождитесь зелёного статуса\n"
        "  4. В настройках найдите «Порт прокси» / Mixed Port\n"
        "  5. Пропишите в .env: PROXY_URL=http://127.0.0.1:ПОРТ\n"
        "  6. Запустите start.bat\n\n"
        "ВАРИАНТ Б — запуск в облаке (без VPN на ПК):\n"
        "  Смотрите файл DEPLOY.txt в папке проекта\n"
        + "=" * 50,
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
