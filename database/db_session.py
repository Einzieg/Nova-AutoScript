import os
from pathlib import Path

from peewee import SqliteDatabase

db_path = os.path.join(Path(__file__).resolve().parent.parent, 'database', 'nova_auto_script.db')
print(db_path)
if not os.path.exists(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SqliteDatabase(db_path)


def init_database():
    db.connect()
    from models import Config, Module

    db.create_tables([Module], safe=True)
    db.create_tables([Config], safe=True)
