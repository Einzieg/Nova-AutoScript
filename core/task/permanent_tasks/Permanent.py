import asyncio
import logging

from core.ControlTools import ControlTools
from core.load_templates import Templates
from core.task.TaskBase import *
from device_operation.DeviceUtils import DeviceUtils
from models.Module import Module


class Permanent(TaskBase):

    def __init__(self, target):
        super().__init__()
        self.name = 'Permanent'
        self.target = target
        self.device = DeviceUtils(self.target)
        self.control = ControlTools(self.target, self.device)
        self.module = Module.get(Module.name == self.target)

    async def execute(self):
        self._update_status(RUNNING)
        while True:
            try:
                self.logging.log('Permanent Starting...', self.target)
                for template in Templates.MONSTER_ELITE:
                    await self.control.matching(template, sleep=1)
            except Exception as e:
                self.logging.log('Permanent Failed.', self.target)
                self._update_status(FAILED)
                raise e

    async def combat_checks(self, callback):

        self.logging.log("检查是否进入战斗 >>>", self.target, logging.DEBUG)
        if await self.control.wait_element_appear(Templates.IN_BATTLE, time_out=180):
            self.logging.log("进入战斗<<<")
            self.logging.log("检查战斗是否结束>>>", self.target, logging.DEBUG)
            if await self.control.wait_element_disappear(Templates.IN_BATTLE, time_out=120):
                self.logging.log("战斗结束<<<")
                callback()
