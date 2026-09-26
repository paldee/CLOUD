from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine, text

from app.db.schema_catalog import DATA_WAREHOUSE_SCHEMA


_TYPE_ALIASES = {
    "bigint": "BIGINT",
    "boolean": "BOOLEAN",
    "character varying": "VARCHAR",
    "date": "DATE",
    "decimal": "NUMERIC",
    "double precision": "DOUBLE PRECISION",
    "integer": "INTEGER",
    "numeric": "NUMERIC",
    "real": "REAL",
    "smallint": "SMALLINT",
    "text": "TEXT",
    "timestamp with time zone": "TIMESTAMPTZ",
    "timestamp without time zone": "TIMESTAMP",
}


@dataclass(frozen=True)
class ActualTable:
    columns: dict[str, str]
    primary_key: str | None
    foreign_keys: dict[str, str]


@dataclass(frozen=True)
class SchemaComparison:
    mismatches: tuple[str, ...]

    @property
    def matches(self) -> bool:
        return not self.mismatches


def normalize_data_type(data_type: str) -> str:
    normalized = data_type.strip().lower()
    return _TYPE_ALIASES.get(normalized, normalized.upper())


def inspect_rds_schema(engine: Engine, schema_name: str) -> dict[str, ActualTable]:
    """Read PostgreSQL information_schema without modifying the database."""
    with engine.connect() as connection:
        column_rows = connection.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema_name
                ORDER BY table_name, ordinal_position
                """
            ),
            {"schema_name": schema_name},
        ).mappings()
        primary_key_rows = connection.execute(
            text(
                """
                SELECT
                    source_table.relname AS table_name,
                    source_column.attname AS column_name
                FROM pg_catalog.pg_constraint AS constraint_info
                JOIN pg_catalog.pg_class AS source_table
                  ON source_table.oid = constraint_info.conrelid
                JOIN pg_catalog.pg_namespace AS source_schema
                  ON source_schema.oid = source_table.relnamespace
                JOIN LATERAL unnest(constraint_info.conkey) WITH ORDINALITY
                  AS source_key(attnum, position) ON true
                JOIN pg_catalog.pg_attribute AS source_column
                  ON source_column.attrelid = source_table.oid
                 AND source_column.attnum = source_key.attnum
                WHERE source_schema.nspname = :schema_name
                  AND constraint_info.contype = 'p'
                ORDER BY source_table.relname, source_key.position
                """
            ),
            {"schema_name": schema_name},
        ).mappings()
        foreign_key_rows = connection.execute(
            text(
                """
                SELECT
                    source_table.relname AS table_name,
                    source_column.attname AS column_name,
                    target_table.relname AS foreign_table_name,
                    target_column.attname AS foreign_column_name
                FROM pg_catalog.pg_constraint AS constraint_info
                JOIN pg_catalog.pg_class AS source_table
                  ON source_table.oid = constraint_info.conrelid
                JOIN pg_catalog.pg_namespace AS source_schema
                  ON source_schema.oid = source_table.relnamespace
                JOIN pg_catalog.pg_class AS target_table
                  ON target_table.oid = constraint_info.confrelid
                JOIN LATERAL unnest(constraint_info.conkey) WITH ORDINALITY
                  AS source_key(attnum, position) ON true
                JOIN LATERAL unnest(constraint_info.confkey) WITH ORDINALITY
                  AS target_key(attnum, position)
                  ON target_key.position = source_key.position
                JOIN pg_catalog.pg_attribute AS source_column
                  ON source_column.attrelid = source_table.oid
                 AND source_column.attnum = source_key.attnum
                JOIN pg_catalog.pg_attribute AS target_column
                  ON target_column.attrelid = target_table.oid
                 AND target_column.attnum = target_key.attnum
                WHERE source_schema.nspname = :schema_name
                  AND constraint_info.contype = 'f'
                ORDER BY source_table.relname, source_key.position
                """
            ),
            {"schema_name": schema_name},
        ).mappings()

        columns_by_table: dict[str, dict[str, str]] = {}
        for row in column_rows:
            columns_by_table.setdefault(row["table_name"], {})[row["column_name"]] = (
                normalize_data_type(row["data_type"])
            )

        primary_keys: dict[str, str] = {}
        for row in primary_key_rows:
            table_name = row["table_name"]
            if table_name in primary_keys:
                primary_keys[table_name] += f",{row['column_name']}"
            else:
                primary_keys[table_name] = row["column_name"]

        foreign_keys: dict[str, dict[str, str]] = {}
        for row in foreign_key_rows:
            foreign_keys.setdefault(row["table_name"], {})[row["column_name"]] = (
                f"{row['foreign_table_name']}.{row['foreign_column_name']}"
            )

    return {
        table_name: ActualTable(
            columns=columns,
            primary_key=primary_keys.get(table_name),
            foreign_keys=foreign_keys.get(table_name, {}),
        )
        for table_name, columns in columns_by_table.items()
    }


def compare_schema(
    actual_schema: dict[str, ActualTable],
    expected_schema: dict[str, dict[str, Any]] = DATA_WAREHOUSE_SCHEMA,
) -> SchemaComparison:
    mismatches: list[str] = []
    expected_tables = set(expected_schema)
    actual_tables = set(actual_schema)

    for table_name in sorted(expected_tables - actual_tables):
        mismatches.append(f"missing table: {table_name}")
    for table_name in sorted(actual_tables - expected_tables):
        mismatches.append(f"unexpected table: {table_name}")

    for table_name in sorted(expected_tables & actual_tables):
        expected = expected_schema[table_name]
        actual = actual_schema[table_name]
        expected_columns = set(expected["columns"])
        actual_columns = set(actual.columns)

        for column in sorted(expected_columns - actual_columns):
            mismatches.append(f"missing column: {table_name}.{column}")
        for column in sorted(actual_columns - expected_columns):
            mismatches.append(f"unexpected column: {table_name}.{column}")
        for column in sorted(expected_columns & actual_columns):
            expected_type = normalize_data_type(expected["column_types"][column])
            actual_type = normalize_data_type(actual.columns[column])
            if expected_type != actual_type:
                mismatches.append(
                    f"type mismatch: {table_name}.{column} "
                    f"expected={expected_type} actual={actual_type}"
                )

        if expected["primary_key"] != actual.primary_key:
            mismatches.append(
                f"primary key mismatch: {table_name} "
                f"expected={expected['primary_key']} actual={actual.primary_key or 'none'}"
            )

        expected_foreign_keys = expected.get("foreign_keys", {})
        for column, target in sorted(expected_foreign_keys.items()):
            actual_target = actual.foreign_keys.get(column)
            if actual_target != target:
                mismatches.append(
                    f"foreign key mismatch: {table_name}.{column} "
                    f"expected={target} actual={actual_target or 'none'}"
                )
        for column, target in sorted(actual.foreign_keys.items()):
            if column not in expected_foreign_keys:
                mismatches.append(
                    f"unexpected foreign key: {table_name}.{column} -> {target}"
                )

    return SchemaComparison(tuple(mismatches))
