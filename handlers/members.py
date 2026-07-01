import asyncio
import logging

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message, User

from mentions import build_mention_messages

router = Router(name="members")
logger = logging.getLogger(__name__)

SEND_DELAY_SEC = 0.35


def _save_user(chat_id: int, user: User | None, db) -> None:
    if not user or user.is_bot:
        return
    db.upsert_member(
        chat_id=chat_id,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
    )


def _save_users_from_message(message: Message, db) -> None:
    if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return

    chat_id = message.chat.id
    _save_user(chat_id, message.from_user, db)

    if message.reply_to_message:
        _save_user(chat_id, message.reply_to_message.from_user, db)

    if message.new_chat_members:
        for user in message.new_chat_members:
            _save_user(chat_id, user, db)

    if message.entities and message.text:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                _save_user(chat_id, entity.user, db)


@router.message(Command("all"), F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def cmd_mention_all(message: Message, db) -> None:
    for admin in await message.bot.get_chat_administrators(message.chat.id):
        _save_user(message.chat.id, admin.user, db)

    members = db.get_members(message.chat.id)
    if message.from_user:
        members = [m for m in members if m.user_id != message.from_user.id]

    if not members:
        await message.answer(
            "Пока нет участников для упоминания.\n"
            "Попросите людей написать в чат — бот запоминает всех, кто пишет."
        )
        return

    custom_text = (message.text or "").split(maxsplit=1)
    suffix = ""
    if len(custom_text) > 1:
        suffix = f"\n\n{custom_text[1]}"

    mention_messages = build_mention_messages(members, suffix=suffix)
    sent = 0

    try:
        for i, (text, entities) in enumerate(mention_messages):
            if i > 0:
                await asyncio.sleep(SEND_DELAY_SEC)
            await message.answer(
                text,
                entities=entities,
                parse_mode=None,
                disable_notification=False,
            )
            sent += 1
    except Exception as exc:
        logger.exception("Ошибка при отправке упоминаний")
        await message.answer(f"Ошибка после {sent} упоминаний: {exc}")
        return

    total_in_chat = await message.bot.get_chat_member_count(message.chat.id)
    await message.answer(
        f"Готово: упомянуто {sent} из {total_in_chat} участников.",
        disable_notification=True,
    )
    logger.info("/all: упомянуто %d участников в чате %s", sent, message.chat.id)


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def track_message_author(message: Message, db) -> None:
    _save_users_from_message(message, db)


@router.chat_member()
async def on_chat_member_update(event: ChatMemberUpdated, db) -> None:
    chat = event.chat
    if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return

    new = event.new_chat_member
    user = new.user
    if user.is_bot:
        return

    if new.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
        db.upsert_member(
            chat_id=chat.id,
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )
    elif new.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED, ChatMemberStatus.BANNED}:
        db.remove_member(chat.id, user.id)
