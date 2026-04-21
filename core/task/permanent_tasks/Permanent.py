from core.task.TaskBase import *

TASK_NAME = "常驻任务"

NORMAL_MONSTER_CAP_PER_CYCLE = 10

swipes = [
    None,  # 不划
    [(900, 480), (900, 600), (900, 720), (900, 840), (900, 960)],  # 上划
    [(900, 840), (900, 720), (900, 600), (900, 480), (900, 360), (900, 240), (900, 120)],  # 下划
]


class Permanent(TaskBase):

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
        while True:
            await self.device.check_running_status()
            await self.attack_monsters()
            await self.collect_planet_resource()
            await self.collect_wreckage()

    async def collect_wreckage(self):
        if not self.module.wreckage:
            return

        await self.reset_process()

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
                await asyncio.sleep(0.5)

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
        self.logging.log("未找到残骸", self.target, logging.INFO)
        return False

    async def _collect_planet_wait(self, step: str, template, **kwargs):
        self.logging.log(
            f"采集星球资源 | 开始等待 | {step} | 模板={template.name}",
            self.target,
            logging.INFO,
        )
        ok = await self.control.await_element_appear(template, **kwargs)
        level = logging.INFO if ok else logging.WARNING
        self.logging.log(
            f"采集星球资源 | 等待结束 | {step} | {'已找到' if ok else '超时未找到'} | 模板={template.name}",
            self.target,
            level,
        )
        return ok

    async def _collect_planet_close(self, step: str, template):
        self.logging.log(
            f"采集星球资源 | 尝试关闭 | {step} | 模板={template.name}",
            self.target,
            logging.INFO,
        )
        hit = await self.control.matching_one(template, click=True)
        level = logging.INFO if hit else logging.WARNING
        self.logging.log(
            f"采集星球资源 | 关闭结束 | {step} | {'已匹配' if hit else '未匹配'} | 模板={template.name}",
            self.target,
            level,
        )
        return hit

    async def collect_planet_resource(self):
        if not self.module.planet_resource:
            return

        self.logging.log("采集星球资源 | 流程开始", self.target, logging.INFO)
        await self.reset_process()
        self.logging.log("采集星球资源 | reset_process 完成", self.target, logging.INFO)

        await self._collect_planet_wait("进入星系(TO_SYSTEM)", Templates.TO_SYSTEM, click=True, time_out=3)
        await self._collect_planet_wait("更多星系(MORE_SYSTEM)", Templates.MORE_SYSTEM, click=True, time_out=3)
        await self._collect_planet_wait(
            "行星改造(PLANET_TRANSFORM)", Templates.PLANET_TRANSFORM, click=True, time_out=5, sleep=1
        )
        await self._collect_planet_wait("资源枢纽(RESOURCE_HUB)", Templates.RESOURCE_HUB, click=True, time_out=5, sleep=1)
        await self._collect_planet_wait(
            "采集行星(COLLECT_PLANET) 第一段", Templates.COLLECT_PLANET, click=True, time_out=2, sleep=1
        )
        for i, template in enumerate(Templates.CLOSE_BUTTONS):
            await self._collect_planet_close(f"关闭按钮 第一段 #{i + 1}", template)

        self.logging.log("采集星球资源 | 第一次返回(back) + 等待 3s", self.target, logging.INFO)
        await self.device.click_back()
        await asyncio.sleep(3)

        await self._collect_planet_wait(
            "异常观测(ANOMALY_WATCH)", Templates.ANOMALY_WATCH, click=True, time_out=5, sleep=1
        )
        await self._collect_planet_wait(
            "采集行星(COLLECT_PLANET) 第二段", Templates.COLLECT_PLANET, click=True, time_out=2, sleep=1
        )
        for i, template in enumerate(Templates.CLOSE_BUTTONS):
            await self._collect_planet_close(f"关闭按钮 第二段 #{i + 1}", template)

        self.logging.log("采集星球资源 | 第二次返回(back) + 等待 2s", self.target, logging.INFO)
        await self.device.click_back()
        await asyncio.sleep(2)
        self.logging.log("采集星球资源 | 第三次返回(back) + 等待 5s", self.target, logging.INFO)
        await self.device.click_back()
        await asyncio.sleep(5)
        self.logging.log("采集星球资源 | 流程结束", self.target, logging.INFO)
        return

    async def attack_monsters(self, normal_attacked: int = 0):
        await self.reset_process()

        skip_normal = normal_attacked >= NORMAL_MONSTER_CAP_PER_CYCLE

        monster_configs = [
            (self.module.red_monster, Templates.MONSTER_RED_LIST, False),
            (self.module.elite_monster, Templates.MONSTER_ELITE_LIST, False),
            (
                self.module.normal_monster and not skip_normal,
                Templates.MONSTER_NORMAL_LIST,
                True,
            ),
        ]

        for swipe in swipes:
            if swipe:
                await self.device.swipe(swipe, duration=400 if len(swipe) > 2 else 200)
                await asyncio.sleep(1)

            for enabled, template_list, counts_as_normal in monster_configs:
                if not enabled:
                    continue

                for template in template_list:
                    if await self.control.matching_one(template, click=True):
                        await self.attack()
                        if counts_as_normal:
                            normal_attacked += 1
                        return await self.attack_monsters(
                            normal_attacked=normal_attacked
                        )

    async def reset_process(self):
        await self.return_home()
        await self.control.await_element_appear(Templates.SPACE_STATION, click=True, time_out=5)
        await self.control.await_element_appear(Templates.STAR_SYSTEM, click=True, time_out=10)
        if await self.control.await_element_appear(Templates.SPACE_STATION, click=False, time_out=10):
            await self.device.zoom_out()
            await asyncio.sleep(5)
