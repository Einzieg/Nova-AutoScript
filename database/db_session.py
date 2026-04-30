import os
from pathlib import Path

from peewee import SqliteDatabase

db_path = os.path.join(Path(__file__).resolve().parent.parent, 'database', 'nova_auto_script.db')
print(db_path)
if not os.path.exists(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SqliteDatabase(db_path)


def _migrate_module_columns():
    """Add columns introduced after the table was first created (SQLite has no ALTER for full schema sync)."""
    from models import Module

    table = Module._meta.table_name
    cur = db.execute_sql(f'PRAGMA table_info("{table}")')
    columns = {row[1] for row in cur.fetchall()}
    if "planet_resource" not in columns:
        db.execute_sql(
            f'ALTER TABLE "{table}" ADD COLUMN planet_resource BLOB DEFAULT 0'
        )
    if "permanent_order" not in columns:
        db.execute_sql(
            f'ALTER TABLE "{table}" ADD COLUMN permanent_order BLOB DEFAULT 0'
        )


def init_database():
    db.connect()
    from models import Config, Module

    db.create_tables([Module], safe=True)
    db.create_tables([Config], safe=True)
    _migrate_module_columns()
