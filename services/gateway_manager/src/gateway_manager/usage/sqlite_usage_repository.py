import sqlite3
from datetime import datetime
from pathlib import Path

from .usage_record import UsageRecord
from .usage_repository import UsageRepository


class SQLiteUsageRepository(UsageRepository):

    def __init__(
        self,
        database_path: Path,
    ) -> None:

        self.database_path = database_path

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:

        return sqlite3.connect(
            self.database_path
        )

    def _initialize(
        self,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_records (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,

                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,

                    cost_amount REAL,
                    cost_currency TEXT,

                    latency_ms INTEGER,

                    capability TEXT,
                    project TEXT,
                    tenant TEXT,

                    success INTEGER NOT NULL,
                    fallback INTEGER NOT NULL,
                    error_type TEXT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_usage_timestamp
                ON usage_records(timestamp)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_usage_currency
                ON usage_records(cost_currency)
                """
            )

    def add(
        self,
        record: UsageRecord,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO usage_records (
                    id,
                    timestamp,
                    provider,
                    model,

                    prompt_tokens,
                    completion_tokens,
                    total_tokens,

                    cost_amount,
                    cost_currency,

                    latency_ms,

                    capability,
                    project,
                    tenant,

                    success,
                    fallback,
                    error_type
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    record.id,
                    record.timestamp.isoformat(),
                    record.provider,
                    record.model,

                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,

                    record.cost_amount,
                    record.cost_currency,

                    record.latency_ms,

                    record.capability,
                    record.project,
                    record.tenant,

                    int(record.success),
                    int(record.fallback),
                    record.error_type,
                ),
            )

    def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[UsageRecord]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    provider,
                    model,

                    prompt_tokens,
                    completion_tokens,
                    total_tokens,

                    cost_amount,
                    cost_currency,

                    latency_ms,

                    capability,
                    project,
                    tenant,

                    success,
                    fallback,
                    error_type

                FROM usage_records

                WHERE timestamp >= ?
                  AND timestamp < ?

                ORDER BY timestamp ASC
                """,
                (
                    start.isoformat(),
                    end.isoformat(),
                ),
            ).fetchall()

        return [
            UsageRecord(
                id=row[0],
                timestamp=datetime.fromisoformat(
                    row[1]
                ),
                provider=row[2],
                model=row[3],

                prompt_tokens=row[4],
                completion_tokens=row[5],
                total_tokens=row[6],

                cost_amount=row[7],
                cost_currency=row[8],

                latency_ms=row[9],

                capability=row[10],
                project=row[11],
                tenant=row[12],

                success=bool(row[13]),
                fallback=bool(row[14]),
                error_type=row[15],
            )
            for row in rows
        ]

    def total_cost_between(
        self,
        start: datetime,
        end: datetime,
        currency: str,
    ) -> float:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COALESCE(
                    SUM(cost_amount),
                    0
                )

                FROM usage_records

                WHERE timestamp >= ?
                  AND timestamp < ?
                  AND success = 1
                  AND cost_currency = ?
                """,
                (
                    start.isoformat(),
                    end.isoformat(),
                    currency,
                ),
            ).fetchone()

        return float(
            row[0]
        )
