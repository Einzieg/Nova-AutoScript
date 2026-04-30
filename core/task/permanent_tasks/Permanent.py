from core.task.TaskBase import *
from core.task.daily_tasks.Order import Order

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
            await self.attack_red_elite_monsters()
            await self.collect_wreckage()
            await self.attack_normal_monsters()
            await self.process_orders()
            await self.collect_planet_resource()

    async def process_orders(self):
        if not self.module.permanent_order:
            return

        self.logging.log("常驻任务 | 订单阶段开始（不使用超空间信标）", self.target, logging.INFO)
        order = Order(self.target)
        order.order_policy = "不使用超空间信标"
        order.module.order_times = None

        await order.start()
        self.logging.log("常驻任务 | 订单阶段结束", self.target, logging.INFO)

    async def collect_wreckage(self):
        if not self.module.wreckage:
            return

        await self.reset_process()

        while True:
            found_wreckage = False
            for swipe in swipes:
                if swipe:
                    await self.device.swipe(swipe, duration=400 if len(swipe) > 3 else 200)
                    await asyncio.sleep(1)

                result = await self._search_and_collect()
                if result == "no_workships":
                    return
                if result == "collected":
                    found_wreckage = True

            if not found_wreckage:
                return

    async def _search_and_collect(self) -> str:
        wreckage = await self._visible_wreckage_coordinates()
        if not wreckage:
            self.logging.log("当前屏幕未找到残骸", self.target, logging.INFO)
            return "not_found"

        self.logging.log(f"当前屏幕找到 {len(wreckage)} 个残骸坐标: {wreckage}", self.target, logging.INFO)
        collected = False

        for coordinate in wreckage:
            await self.device.click(coordinate)
            await asyncio.sleep(0.5)

            if await self.control.matching_one(Templates.RECALL):
                await self.device.click_back()
                continue

            collect_clicked = await self.control.await_element_appear(
                Templates.COLLECT, click=True, time_out=2, sleep=1
            )
            collected = collected or bool(collect_clicked)

            if await self.control.matching_one(Templates.NO_WORKSHIPS):
                await self.device.click_back()
                await asyncio.sleep(0.5)
                await self.device.click_back()
                await asyncio.sleep(30)
                self.logging.log("没有可用工程船，残骸采集阶段结束", self.target, logging.INFO)
                return "no_workships"

        return "collected" if collected else "not_found"

    async def _visible_wreckage_coordinates(self):
        coordinates = []
        seen = set()

        for template in Templates.WRECKAGE_LIST:
            matches = await self.control.matching_all(template)
            if not matches:
                continue

            for x, y in matches:
                key = (int(x), int(y))
                if key in seen:
                    continue
                seen.add(key)
                coordinates.append([int(x), int(y)])

        ordered_coordinates = self._order_coordinates_by_collection_path(coordinates)
        return self.control.shift_coordinates_after_centering(ordered_coordinates)

    @staticmethod
    def _order_coordinates_by_collection_path(coordinates, center=(960, 540)):
        remaining = coordinates.copy()
        ordered = []
        current = center

        while remaining:
            next_coordinate = min(
                remaining,
                key=lambda coordinate: (coordinate[0] - current[0]) ** 2 + (coordinate[1] - current[1]) ** 2,
            )
            remaining.remove(next_coordinate)
            ordered.append(next_coordinate)
            current = next_coordinate

        return ordered

    async def attack_red_elite_monsters(self):
        monster_configs = [
            (self.module.red_monster, Templates.MONSTER_RED_LIST),
            (self.module.elite_monster, Templates.MONSTER_ELITE_LIST),
        ]
        if not any(enabled for enabled, _ in monster_configs):
            return

        while await self._attack_one_from_configs(monster_configs):
            pass

        self.logging.log("未找到深红/精英海盗，进入下一阶段", self.target, logging.INFO)

    async def attack_normal_monsters(self):
        if not self.module.normal_monster:
            return

        normal_attacked = 0
        monster_configs = [(True, Templates.MONSTER_NORMAL_LIST)]

        while normal_attacked < NORMAL_MONSTER_CAP_PER_CYCLE:
            attacked = await self._attack_one_from_configs(monster_configs)
            if not attacked:
                self.logging.log("未找到普通海盗，进入下一阶段", self.target, logging.INFO)
                return

            normal_attacked += 1
            self.logging.log(
                f"普通海盗攻击计数 {normal_attacked}/{NORMAL_MONSTER_CAP_PER_CYCLE}",
                self.target,
                logging.INFO,
            )

        self.logging.log("普通海盗本轮已达上限，进入下一阶段", self.target, logging.INFO)

    async def _attack_one_from_configs(self, monster_configs) -> bool:
        await self.reset_process()

        for swipe in swipes:
            if swipe:
                await self.device.swipe(swipe, duration=400 if len(swipe) > 2 else 200)
                await asyncio.sleep(1)

            for enabled, template_list in monster_configs:
                if not enabled:
                    continue

                for template in template_list:
                    if await self.control.matching_one(template, click=True):
                        await self.attack()
                        return True

        return False

    async def collect_planet_resource(self):
        if not self.module.planet_resource:
            return

        self.logging.log("采集星球资源 | 流程开始", self.target, logging.INFO)
        await self.reset_process()
        self.logging.log("采集星球资源 | reset_process 完成", self.target, logging.INFO)

        await self._collect_planet_resource_section("资源枢纽")

        await asyncio.sleep(3)
        self.logging.log("采集星球资源 | 资源枢纽完成，重置视角", self.target, logging.INFO)
        await self.reset_process()

        await self._collect_planet_resource_section("异象观测站")

        await asyncio.sleep(3)
        self.logging.log("采集星球资源 | 流程结束", self.target, logging.INFO)
        return

    async def _collect_planet_resource_section(self, resource_name: str):
        await self._open_planet_transform()
        await self.control.await_text_appear(resource_name, click=True, time_out=5, sleep=1)
        await self.control.await_text_appear("全部收取", click=True, time_out=2, sleep=1)
        await self.control.await_text_appear("关闭", click=True, time_out=5, sleep=1)

    async def _open_planet_transform(self):
        await self.control.await_text_appear("系统", click=True, time_out=3)
        await self.control.await_text_appear("更多", click=True, time_out=3)
        await self.control.await_text_appear("行星改造", click=True, time_out=5, sleep=1)

    async def reset_process(self):
        await self.return_home()
        await self.control.await_text_appear("空间站", click=True, time_out=5, exact=True)
        await self.control.await_text_appear("星系", click=True, time_out=10, exact=True)
        if await self.control.await_text_appear("空间站", click=False, time_out=10, exact=True):
            await self.device.zoom_out()
            await asyncio.sleep(5)
