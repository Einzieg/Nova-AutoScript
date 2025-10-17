from pathlib import Path

from core.LoadTemplates import Template
from core.task.TaskBase import *

import time

TASK_NAME = "残骸"

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Wreckage(TaskBase):
    def __init__(self, target):
        super().__init__(target)
        self.callback = False
        self.target = target

    async def prepare(self):
        await super().prepare()
        self.logging.log(f"{TASK_NAME} 开始执行 >>>", self.target)

    async def execute(self):
        self._update_status(RUNNING)
        await self.start()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log(f"{TASK_NAME} 执行完成 <<<", self.target)

    async def start(self):
        try:
            for i in range(2):
                await self.collect_wreckage()
                await asyncio.sleep(400)
            return
        except Exception as e:
            self.logging.log(f"{TASK_NAME} 失败: {e}", self.target, logging.ERROR)
            return
    
        