from aiogram.types import MessageEntity, User

from database import StoredMember


def _utf16_len(text: str) -> int:
    """Telegram считает offset/length в UTF-16, не в символах Python."""
    return len(text.encode("utf-16-le")) // 2


def _display_name(member: StoredMember) -> str:
    if member.last_name:
        return f"{member.first_name} {member.last_name}"
    return member.first_name


def _member_to_user(member: StoredMember) -> User:
    return User(
        id=member.user_id,
        is_bot=False,
        first_name=member.first_name,
        last_name=member.last_name,
        username=member.username,
    )


def build_mention_messages(
    members: list[StoredMember],
    suffix: str = "",
) -> list[tuple[str, list[MessageEntity]]]:
    """Одно сообщение = одно text_mention — максимум push-уведомлений."""
    if not members:
        return []

    messages: list[tuple[str, list[MessageEntity]]] = []
    for i, member in enumerate(members):
        name = _display_name(member)
        text = name
        if i == len(members) - 1 and suffix:
            text = f"{name}{suffix}"

        messages.append((
            text,
            [
                MessageEntity(
                    type="text_mention",
                    offset=0,
                    length=_utf16_len(name),
                    user=_member_to_user(member),
                )
            ],
        ))

    return messages
