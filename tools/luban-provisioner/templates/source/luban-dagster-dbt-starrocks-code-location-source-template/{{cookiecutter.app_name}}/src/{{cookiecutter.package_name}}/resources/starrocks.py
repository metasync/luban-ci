from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import os


@dataclass(frozen=True)
class StarRocksClient:
    host: str
    port: int
    user: str
    password: str
    connect_timeout: int = 10

    def _connect(self):
        import pymysql

        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            connect_timeout=self.connect_timeout,
            read_timeout=self.connect_timeout,
            write_timeout=self.connect_timeout,
            autocommit=True,
        )

    def query_scalar(self, sql: str) -> Any:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
                return row[0] if row else None
        finally:
            connection.close()

    def query_column(self, sql: str) -> list[Any]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        finally:
            connection.close()


def make_starrocks_resource() -> StarRocksClient:
    return StarRocksClient(
        host=os.getenv("STARROCKS_HOST", "localhost"),
        port=int(os.getenv("STARROCKS_PORT", "9030")),
        user=os.getenv("STARROCKS_USER", "root"),
        password=os.getenv("STARROCKS_PASSWORD", ""),
    )

