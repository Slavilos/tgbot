from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="commands")

PRIVATE_START_TEXT = (
    "Привет! Я бот для упоминания всех участников группы.\n\n"
    "Как пользоваться:\n"
    "1. Добавьте меня в группу\n"
    "2. Выдайте права на чтение сообщений (и желательно — на просмотр участников)\n"
    "3. В группе любой участник может вызвать:\n"
    "   • /all — упомянуть всех известных участников\n"
    "   • /all текст — упомянуть всех с вашим сообщением\n"
    "   • /count — сколько участников я знаю\n\n"
    "Бот запоминает участников, когда они пишут в чат, отвечают на сообщения или входят в группу.\n"
    "Уведомление получают только те, кого бот уже знает."
)

GROUP_HELP_TEXT = (
    "Команды:\n"
    "/all — упомянуть всех участников\n"
    "/all ваш текст — упомянуть всех с сообщением\n"
    "/count — количество участников в базе\n"
    "/help — эта справка"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(PRIVATE_START_TEXT)
    else:
        await message.answer(GROUP_HELP_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(GROUP_HELP_TEXT)


@router.message(Command("count"))
async def cmd_count(message: Message, db) -> None:
    if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        await message.answer("Эта команда работает только в группах.")
        return

    count = db.count_members(message.chat.id)
    await message.answer(f"Я знаю {count} участник(ов) в этом чате.")
