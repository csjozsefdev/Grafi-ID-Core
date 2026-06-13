"""SQLite write helpers — commits are owned by the service layer."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


def commit_write(connection: sqlite3.Connection) -> None:
    """
    Persist pending INSERT/UPDATE/DELETE on this connection.

    Call from services after repository writes. Read-only code must not call this.
    """
    connection.commit()


@contextmanager
def write_transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """
    BEGIN IMMEDIATE, commit on success, rollback on any error.

    Use for multi-step writes in one service method.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
