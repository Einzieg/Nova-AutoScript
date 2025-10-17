from pathlib import Path

from core.NovaException import RadarFinishes
from core.LoadTemplates import Template
from core.task.TaskBase import *

TASK_NAME = "雷达"

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

RADAR = Template(
    name="雷达",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/hidden/radar.png"
)
SEARCH = Template(
    name="搜索",
    threshold=0.80,
    template_path=ROOT_DIR / "static/novaimgs/hidden/search.png"
)
BUTTON_USE = Template(
    name="使用按钮",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/hidden/button_use_prop.png"
)
BUTTON_BUY = Template(
    name="购买按钮",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/hidden/button_buy.png"
)
MAX = Template(
    name="MAX",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/hidden/max.png"
)
RADAR_ENERGY = Template(
    name="雷达能量",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/hidden/energy.png"
)
GEC = Template(
    name="GEC",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/hidden/GEC.png"
)


class Radar(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.target = target
        self.hidden_policy = self.module.hidden_policy

    async def prepare(self):
        await super().prepare()
        self.logging.log(f"任务 {TASK_NAME} 开始执行 >>>", self.target)

    async def execute(self):
        self._update_status(RUNNING)
        await self.start()

    async def cleanup(self):
        await super().cleanup()
        await self.return_home()
        self.logging.log(f"任务 {TASK_NAME} 执行完成 <<<", self.target)

    async def start(self):
        hidden_times = self.module.hidden_times
        # TODO : 每寰宇日把能量打满
        hidden_wreckage = self.module.hidden_wreckage
        try:
            if hidden_times:
                for i in range(hidden_times):
                    await self.radar_process()
            else:
                while True:
                    await self.return_home()
                    await self.radar_process()
        except RadarFinishes:
            self._update_status(SUCCESS)
            return

    async def radar_process(self):
        await self.control.await_element_appear(RADAR, click=True, time_out=3)
        await self.control.await_element_appear(SEARCH, click=True, time_out=3)
        if await self.control.await_element_appear(Templates.ATTACK_BUTTON, time_out=2):
            await self.attack()
            return
        if await self.control.await_element_appear(BUTTON_USE, click=True, time_out=2) | await self.control.await_element_appear(BUTTON_BUY, click=True, time_out=2):
            if self.hidden_policy == "不使用能量道具":
                raise RadarFinishes("不使用道具,雷达结束")
            if self.hidden_policy in ["使用能量道具", "使用GEC购买能量"]:
                await self.control.await_element_appear(MAX, click=True, time_out=1.5, sleep=0.5)
                if not await self.control.await_element_appear(RADAR_ENERGY, click=True, time_out=1, sleep=0.5):
                    if self.hidden_policy == "使用GEC购买能量":
                        await self.control.await_element_appear(GEC, click=True, time_out=1, sleep=1)
                    else:
                        raise RadarFinishes("不使用GEC购买道具,雷达结束")
                await self.control.await_element_appear(SEARCH, click=True, time_out=1, sleep=1)
            else:
                raise RadarFinishes("道具耗尽,雷达结束")
        await self.attack()
