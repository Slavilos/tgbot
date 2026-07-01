import os
from dataclasses import dataclass

from dotenv import load_dotenv

# На Windows используем winreg, на Linux его нет
try:
    import winreg
except ImportError:
    winreg = None

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    db_path: str = "members.db"
    proxy_url: str | None = None


def _windows_system_proxy() -> str | None:
    if winreg is None:
        return None

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        ) as key:
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if not enabled:
                return None

            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            if not server:
                return None

            if "://" not in server:
                server = f"http://{server}"

            return server

    except OSError:
        return None


def _resolve_proxy() -> str | None:
    for key in ("PROXY_URL", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    return _windows_system_proxy()


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()

    if not token:
        raise ValueError("BOT_TOKEN не задан")

    return Settings(
        bot_token=token,
        db_path=os.getenv("DB_PATH", "members.db"),
        proxy_url=_resolve_proxy(),
    )
