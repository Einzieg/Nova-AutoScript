from core.task.TaskBase import *

TASK_NAME = "联盟商店"


class AllianceShop(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.target = target

    async def prepare(self):
        await super().prepare()
        self.logging.log(f"任务 {TASK_NAME} 开始执行 >>>", self.target)

    async def execute(self):
        self._update_status(RUNNING)
        await self.start()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log(f"任务 {TASK_NAME} 执行完成 <<<", self.target)

    async def start(self):
        pass

    async def goto_shop(self):
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, timeout=3)
        await self.control.await_element_appear(Templates.ALLIANCE, click=True, timeout=3)

