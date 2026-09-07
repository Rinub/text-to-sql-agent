"""
Database connection and query execution.

Provides:
- SQLAlchemy engine creation
- Schema introspection (get_db_schema)
- Safe query execution (execute_query)
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Create engine — handle SQLite's check_same_thread requirement
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_schema() -> list[dict]:
    """
    Introspect the database and return schema information.

    Returns a list of dicts, each representing a table:
    [
        {
            "table_name": "customers",
            "columns": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                {"name": "name", "type": "VARCHAR(100)", "primary_key": False, "nullable": False},
                ...
            ]
        },
        ...
    ]
    """
    inspector = inspect(engine)
    tables = []

    for table_name in inspector.get_table_names():
        columns = []
        pk_columns = inspector.get_pk_constraint(table_name).get("constrained_columns", [])

        for col in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "primary_key": col["name"] in pk_columns,
                    "nullable": col.get("nullable", True),
                }
            )

        # Also get foreign keys for relationship context
        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append(
                {
                    "column": fk["constrained_columns"],
                    "references": f"{fk['referred_table']}({', '.join(fk['referred_columns'])})",
                }
            )

        tables.append(
            {
                "table_name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
            }
        )

    return tables


def get_schema_as_text() -> str:
    """
    Return the database schema formatted as human-readable text
    suitable for including in an LLM prompt.
    """
    schema = get_db_schema()
    lines = []

    for table in schema:
        lines.append(f"TABLE: {table['table_name']}")
        for col in table["columns"]:
            pk_marker = " [PRIMARY KEY]" if col["primary_key"] else ""
            null_marker = "" if col["nullable"] else " NOT NULL"
            lines.append(f"  - {col['name']} ({col['type']}{pk_marker}{null_marker})")

        if table.get("foreign_keys"):
            for fk in table["foreign_keys"]:
                lines.append(
                    f"  FOREIGN KEY ({', '.join(fk['column'])}) REFERENCES {fk['references']}"
                )
        lines.append("")  # blank line between tables

    return "\n".join(lines)


def execute_query(sql: str) -> list[dict]:
    """
    Execute a SQL query and return results as a list of dicts.

    Args:
        sql: The SQL query string to execute.

    Returns:
        List of dicts, where each dict is a row {column_name: value}.

    Raises:
        Exception: If the query fails (syntax error, missing table, etc.)
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return rows
