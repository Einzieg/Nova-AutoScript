import logging

from core.ControlTools import ControlTools
from core.LogManager import LogManager
from device_operation.DeviceUtils import DeviceUtils
from models.Module import Module

WAITING = 0
RUNNING = 1
SUCCESS = 2
FAILED = -1


class TaskBase:
    def __init__(self, target):
        self.target = target
        self.status = WAITING
        self.logging = LogManager()
        self.device = DeviceUtils(target)

        self.control = ControlTools(target, self.device)
        self.module = Module.get(Module.name == target)

    async def prepare(self):
        """任务前置操作"""
        await self.device.async_init()
        self.logging.log("BASE 任务开始执行...", self.target, logging.DEBUG)
        self._update_status(WAITING)

    async def execute(self):
        """主执行逻辑（需子类实现）"""
        raise NotImplementedError

    async def cleanup(self):
        """任务后置操作"""
        self.logging.log("BASE 任务执行完毕...", self.target, logging.DEBUG)
        self._update_status(SUCCESS)

    def _update_status(self, status):
        """更新任务状态"""
        self.status = status
