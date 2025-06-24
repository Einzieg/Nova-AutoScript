from peewee import *

from database.db_session import db


class Module(Model):
    id = AutoField(primary_key=True)
    name = CharField()

    # 基础配置 ---------------------------------------------

    simulator_index = IntegerField(default=0)  # 端口

    autostart_simulator = BlobField(default=False)  # 启动时自动启动模拟器

    auto_relogin = BlobField(default=False)  # 自动抢登

    relogin_time = IntegerField(null=True)  # 抢登等待时间

    attack_fleet = CharField(default='["all"]')  # 攻击舰队列表

    task_type = CharField(default='["permanent"]')  # 任务类型

    stop_time = CharField(null=True)  # 停止时间

    # 常驻任务 ---------------------------------------------

    normal_monster = BlobField(default=False)  # 普通清道夫

    elite_monster = BlobField(default=False)  # 精英清道夫

    red_monster = BlobField(default=False)  # 深红入侵

    wreckage = BlobField(default=False)  # 采集残骸

    # 其他任务 ---------------------------------------------

    hidden_switch = BlobField(default=False)  # 隐秘开关

    hidden_policy = CharField(default="不使用能量道具")  # 隐秘策略 (不使用能量道具/使用能量道具/使用GEC购买能量)

    hidden_times = IntegerField(null=True)  # 隐秘次数

    hidden_wreckage = BlobField(default=False)  # 采集残骸

    order_switch = BlobField(default=False)  # 订单开关

    order_policy = CharField(default="使用超空间信标")  # 订单策略

    order_hasten_policy = CharField(default="使用订单电路板")  # 加速策略

    order_times = IntegerField(null=True)  # 订单次数

    class Meta:
        database = db
