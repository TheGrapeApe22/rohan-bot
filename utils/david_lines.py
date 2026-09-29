import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_PATH = Path("david_lines.sqlite3")


def initialize():
    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS david_lines (
                id INTEGER PRIMARY KEY,
                cited_by INTEGER NOT NULL,
                line TEXT NOT NULL,
                source TEXT NOT NULL
            )"""
        )


def add_line(cited_by: int, line: str, source: str) -> bool:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection, connection:
        cursor = connection.execute(
            """INSERT INTO david_lines (cited_by, line, source)
               SELECT ?, ?, ?
               WHERE NOT EXISTS (SELECT 1 FROM david_lines WHERE line = ?)""",
            (cited_by, line, source, line),
        )
        return cursor.rowcount == 1


def all_lines() -> list[dict]:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        rows = connection.execute(
            "SELECT cited_by, line, source FROM david_lines ORDER BY id"
        ).fetchall()
    return [dict(cited_by=cited_by, line=line, source=source) for cited_by, line, source in rows]


def random_line() -> dict | None:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        row = connection.execute(
            "SELECT cited_by, line, source FROM david_lines ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    return dict(cited_by=row[0], line=row[1], source=row[2])
