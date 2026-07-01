import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StoredMember:
    user_id: int
    first_name: str
    last_name: str | None
    username: str | None


class MemberDatabase:
    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS members (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    username TEXT,
                    PRIMARY KEY (chat_id, user_id)
                )
                """
            )

    def upsert_member(
        self,
        chat_id: int,
        user_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO members (chat_id, user_id, first_name, last_name, username)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    username = excluded.username
                """,
                (chat_id, user_id, first_name, last_name, username),
            )

    def remove_member(self, chat_id: int, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM members WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            )

    def get_members(self, chat_id: int) -> list[StoredMember]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_id, first_name, last_name, username
                FROM members
                WHERE chat_id = ?
                ORDER BY first_name COLLATE NOCASE
                """,
                (chat_id,),
            ).fetchall()
        return [
            StoredMember(
                user_id=row["user_id"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                username=row["username"],
            )
            for row in rows
        ]

    def count_members(self, chat_id: int) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM members WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return int(row["cnt"])
