from peewee import *

from database.db_session import db


class Config(Model):

    id = AutoField(primary_key=True)
    dark_mode = BlobField(default=True)
    email = CharField(null=True)
    password = CharField(null=True)
    receiver = CharField(null=True)
    cap_tool = CharField(default='MuMu')
    touch_tool = CharField(default='MaaTouch')
    ocr_tool = CharField(default='RapidOcr')
    window_size = IntegerField(default=0)   # 0: 1280, 720, 1: 960, 1040
    on_air = BlobField(default=False)
    on_air_token = CharField(null=True)

    class Meta:
        database = db
