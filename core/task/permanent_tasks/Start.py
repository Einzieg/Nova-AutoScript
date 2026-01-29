from core.task.TaskBase import *

TASK_NAME = "启动"


class Start(TaskBase):

    def __init__(self, target, quick_start=False):
        super().__init__(target)
        self.target = target
        self.quick_start = quick_start
        self.hidden_policy = self.module.hidden_policy

    async def prepare(self):
        # await super().prepare()
        self.logging.log(f"任务 {TASK_NAME} 开始执行 >>>", self.target)

    async def execute(self):
        self._update_status(RUNNING)
        await self.start()
        await self.device.async_init()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log(f"任务 {TASK_NAME} 执行完成 <<<", self.target)

    async def start(self):
        if self.module.autostart_simulator and not self.quick_start:
            await self.device.start_simulator()
            await self.device.check_running_status()
            await self.device.check_wm_size()
            if await self.control.await_element_appear(Templates.NEBULA, time_out=120, sleep=3):
                self.logging.log("游戏启动成功", self.target)
            else:
                self.logging.log("游戏启动失败,尝试重启", self.target)
                await self.device.close_app()
                await self.start()
            await self.control.matching_one(Templates.CONFIRM_RELOGIN, click=True)
        else:
            self.logging.log("跳过启动模拟器", self.target)
