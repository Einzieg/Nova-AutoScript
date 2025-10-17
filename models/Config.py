from peewee import *

from database.db_session import db


class Config(Model):

    id = AutoField(primary_key=True)
    dark_mode = BlobField(default=True)
    email = CharField(null=True)
    password = CharField(null=True)
    receiver = CharField(null=True)
    simulator_path = CharField(null=True)
    cap_tool = CharField(default='MuMu')
    touch_tool = CharField(default='MaaTouch')

    class Meta:
        database = db
