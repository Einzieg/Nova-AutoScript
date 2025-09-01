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
            await self.attack_monsters()
            await self.collect_wreckage()

    async def collect_wreckage(self):
        if not self.module.wreckage:
            return

        await self.reset_process()

        swipes = [
            None,  # 初始不滑动
            [(900, 480), (900, 600), (900, 720)],  # 小滑动
            [(900, 840), (900, 720), (900, 600), (900, 480), (900, 360), (900, 240)],  # 大滑动
        ]

        for swipe in swipes:
            if swipe:
                await self.device.swipe(swipe, duration=400 if len(swipe) > 3 else 200)
                await asyncio.sleep(1)

            found = await self._search_and_collect()
            if found:
                return

    async def _search_and_collect(self) -> bool:
        """搜索残骸并尝试收集，成功返回 True，否则 False"""
        for template in Templates.WRECKAGE_LIST:
            wreckage = await self.control.move_coordinates(template)
            if not wreckage:
                continue

            for coordinate in wreckage:
                await self.device.click(coordinate)
                await asyncio.sleep(0.3)

                if await self.control.matching_one(Templates.RECALL):
                    await self.device.click_back()

                await self.control.await_element_appear(
                    Templates.COLLECT, click=True, time_out=2, sleep=1
                )

                if await self.control.matching_one(Templates.NO_WORKSHIPS):
                    await self.device.click_back()
                    await asyncio.sleep(0.5)
                    await self.device.click_back()
                    await asyncio.sleep(30)
                    return True

            return True
        return False

    async def attack_monsters(self):
        await self.reset_process()
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
