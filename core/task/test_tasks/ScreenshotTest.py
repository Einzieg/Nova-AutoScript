import asyncio

from core.task.TaskBase import *

TASK_NAME = "截图测试"


class ScreenshotTest(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.target = target

    async def prepare(self):
        await super().prepare()
        self.logging.log(f"{TASK_NAME} 开始执行 >>>", self.target)

    async def cleanup(self):
        await super().cleanup()
        self.logging.log(f"{TASK_NAME} 执行完成 <<<", self.target)

    async def execute(self):
        self._update_status(RUNNING)
        try:
            self.logging.log(f'{TASK_NAME} 执行 >>>', self.target)
            self.device.save_screencap()
        except Exception as e:
            self.logging.log(f'{TASK_NAME} 失败 <<<', self.target)
            self._update_status(FAILED)
            raise e
