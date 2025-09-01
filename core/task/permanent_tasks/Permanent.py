from watchfiles import awatch

from core.task.TaskBase import *

TASK_NAME = "常驻任务"


class Permanent(TaskBase):

    def __init__(self, target):
        super().__init__(target)
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
        while True:
            await self.reset_process()
            await self.attack_monsters()
            await self.collect_wreckage()

    async def collect_wreckage(self):
        if self.module.wreckage:
            await self.reset_process()
            for template in Templates.WRECKAGE_LIST:
                wreckage = await self.control.move_coordinates(template)
                if wreckage:
                    for coordinate in wreckage:
                        await self.device.click(coordinate)
                        await asyncio.sleep(0.3)
                        if await self.control.matching_one(Templates.RECALL):
                            await self.device.click_back()
                        await self.control.await_element_appear(Templates.COLLECT, click=True, time_out=2, sleep=1)
                        if await self.control.matching_one(Templates.NO_WORKSHIPS):
                            await self.device.click_back()
                            await asyncio.sleep(0.5)
                            await self.device.click_back()
                            return

    async def attack_monsters(self):
        if self.module.red_monster:
            for template in Templates.MONSTER_RED_LIST:
                if await self.control.matching_one(template, click=True):
                    await self.attack()
                    await self.attack_monsters()
        if self.module.elite_monster:
            for template in Templates.MONSTER_ELITE:
                if await self.control.matching_one(template, click=True):
                    await self.attack()
                    await self.attack_monsters()
        if self.module.normal_monster:
            for template in Templates.MONSTER_NORMAL_LIST:
                if await self.control.matching_one(template, click=True):
                    await self.attack()
                    await self.attack_monsters()

    async def reset_process(self):
        await self.return_home()
        await self.control.await_element_appear(Templates.SPACE_STATION, click=True, time_out=5)
        await self.control.await_element_appear(Templates.STAR_SYSTEM, click=True, time_out=10)
        if await self.control.await_element_appear(Templates.SPACE_STATION, click=False, time_out=10):
            await self.device.zoom_out()
            await asyncio.sleep(5)
