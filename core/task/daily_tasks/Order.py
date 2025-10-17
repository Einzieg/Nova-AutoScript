from pathlib import Path

from core.LoadTemplates import Template
from core.NovaException import OrderFinishes
from core.task.TaskBase import *

TASK_NAME = "订单"

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 切换天赋所需模版

TO_TALENT = Template(
    name="天赋按钮",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/talent/to_talent.png"
)
TALENT_CHOICE = Template(
    name="天赋选择",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/talent/special_talent.png"
)
TALENT_RC = Template(
    name="增加RC",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/talent/increase_rc.png"
)
TALENT_TIME = Template(
    name="减少时间",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/talent/reduce_time.png"
)
CONFIRM_TALENT = Template(
    name="天赋确认",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/talent/confirm_replacement_talent.png"
)

# 通过牌子提交订单所需模版
TO_ORDER = Template(
    name="订单按钮",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/to_order.png"
)
PCBA_DELIVERY = Template(
    name="PCBA提交",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/order/PCBA_delivery.png"
)
PCBA_INSUFFICIENT = Template(
    name="PCBA不足",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/order/PCBA_insufficient.png"
)
ORDER_DEPARTURE = Template(
    name="订单离港",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/order/departures.png"
)
DELIVERY_CONFIRM = Template(
    name="提交确认",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/confirm_delivery.png"
)
ORDER_CLOSE = Template(
    name="关闭订单",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/close_order.png"
)
TO_HOME = Template(
    name="回到首页",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/button/to_home.png"
)

# 通过制造提交订单所需模版
TO_CONTROL_PANEL_GOLD = Template(
    name="空间站管理界面金",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/button/button_system_gold.png"
)
TO_CONTROL_PANEL_BLUE = Template(
    name="空间站管理界面蓝",
    threshold=0.75,
    template_path=ROOT_DIR / "static/novaimgs/button/button_system_blue.png"
)
ORDER_IS_HERE = Template(
    name="订单已到",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/order_arrived.png"
)
ECONOMY = Template(
    name="经济",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/economy.png"
)
# ORDER_ONTHEWAY = Template(
#     name="订单未到",
#     threshold=0.85,
#     template_path=ROOT_DIR / "static/novaimgs/order/order_ontheway.png"
# )
QUICK_DELIVER = Template(
    name="快速提交",
    threshold=0.65,
    template_path=ROOT_DIR / "static/novaimgs/order/submit_order.png"
)
PRODUCE_ORDER = Template(
    name="订单获取",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/produce_order.png"
)
DEVELOPMENT = Template(
    name="研发",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/development.png"
)
GOTO_FACTORY = Template(
    name="前往工厂",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/goto_factory.png"
)
BACK_TO_QUEUE = Template(
    name="返回制造",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/return_to_factorymain.png"
)
SMART_PRODUCTION = Template(
    name="智能制造",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/auto_produce.png"
)
SPEEDUP_PRODUCTION = Template(
    name="制造加速",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/speedup_production.png"
)
QHOUR_SPEEDUP = Template(
    name="15分加速",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/15min_speedup.png"
)
QHOUR_SPEEDUP_OFFSET_X = 500
QHOUR_SPEEDUP_OFFSET_Y = 15
USE_SPEEDUP = Template(
    name="批量使用加速",
    threshold=0.9,
    template_path=ROOT_DIR / "static/novaimgs/order/use_speedup.png"
)
USE_SPEEDUP_OFFSET_X = 500
USE_SPEEDUP_OFFSET_Y = 0

CLOSE_FACTORY = Template(
    name="退出工厂",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/button/btn_close1.png"
)
SPEEDUP_DEPLETED = Template(
    name="加速耗尽",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/speedup_depleted.png"
)

# 获取新订单
MORE_ORDER = Template(
    name="更多订单",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/more_order.png"
)
BEACON_ORDER = Template(
    name="信标订单",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/fast_forward.png"
)
GEC_ORDER = Template(
    name="GEC订单",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/gec_speedup.png"
)
BEACON_CONFIRM = Template(
    name="信标确认",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/confirm_delivery.png"
)
COLLECT_ALL = Template(
    name="全部领取",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/collect_all.png"
)


class Order(TaskBase):
    def __init__(self, target):
        super().__init__(target)
        self.target = target
        self.order_policy = self.module.order_policy
        self.order_hasten_policy = self.module.order_hasten_policy
        # from device_operation.RapidOcr import RapidOcr
        # self.ocr = RapidOcr()

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
        order_times = self.module.order_times
        try:
            if order_times:
                for i in range(order_times):
                    await self.order_process()
            else:
                for i in range(100):  # 100 orders max per day
                    await self.return_home()
                    await self.order_process()
        except OrderFinishes as e:
            self.logging.log(e, self.target)
            self._update_status(SUCCESS)
            return

    async def order_process(self):
        # 使用超空间信标、不使用超空间信标、使用GEC购买信标
        # 使用订单电路板、使用制造加速
        # 先确定是订单电路板还是制造加速：
        # 如果是订单电路板，则直接进入订单页面；否则，进入右侧系统页面操作
        self.logging.log(f"{TASK_NAME} Order Process, Order Policy:{self.order_policy}, Order Hasten Policy:{self.order_hasten_policy}", self.target, logging.DEBUG)
        # 第一步：切换天赋至 +RC
        await self.change_talent(TALENT_RC)

        # 第二步： 进行订单（生产）及提交 (需要手动确认加速足够多？)
        if '订单电路板' in self.order_hasten_policy:  # 需要提前计算好PCBA的数量？
            self.logging.log(f"{TASK_NAME} 使用电路板 <<<", self.target, logging.DEBUG)
            await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
            await self.control.await_element_appear(TO_ORDER, click=True, time_out=3)
            await self.control.await_element_appear(PCBA_DELIVERY, click=True, time_out=3)
            if await self.control.await_element_appear(PCBA_INSUFFICIENT, time_out=2):
                await self.return_home()
                raise OrderFinishes("PCBA道具不足")
            await self.control.await_element_appear(DELIVERY_CONFIRM, click=True, time_out=3)
            await self.control.await_element_appear(TO_HOME, click=True, time_out=3)

        if '使用制造加速' in self.order_hasten_policy:
            self.logging.log(f"{TASK_NAME} 使用制造加速 <<<", self.target, logging.DEBUG)
            if not (await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=1) | await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=1)):
                await self.return_home()
            await self.control.await_element_appear(ECONOMY, click=True, time_out=1)
            if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
                if await self.control.await_element_appear(PRODUCE_ORDER, click=True, time_out=2):
                    await self.control.await_element_appear(GOTO_FACTORY, click=True, time_out=2)
                    if await self.control.await_element_appear(DEVELOPMENT, click=False, time_out=2):
                        raise OrderFinishes("无部件图纸")
                    await self.control.await_element_appear(BACK_TO_QUEUE, click=True, time_out=2)
                    while True:
                        await self.control.await_element_appear(SMART_PRODUCTION, click=True, time_out=2, sleep=1.5)
                        if not await self.control.await_element_appear(SPEEDUP_PRODUCTION, click=True, time_out=2):
                            break  # 智能生产后依然工厂为空闲，判定为无需继续生产
                        if await self.control.await_element_appear(SPEEDUP_DEPLETED, click=False, time_out=2):
                            raise OrderFinishes("加速道具耗尽,订单结束")
                        await self.control.await_element_appear(QHOUR_SPEEDUP, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                        await self.control.await_element_appear(USE_SPEEDUP, click=True, time_out=2, offset_x=0, offset_y=0, sleep=1)
                        await self.control.await_element_appear(QHOUR_SPEEDUP, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                    await self.control.await_element_appear(TO_HOME, click=True, time_out=3)
                    # 提交剩余订单
                    if await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=2) | await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=2):
                        if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                            await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
                            if not await self.control.await_element_appear(PRODUCE_ORDER, click=False, time_out=2):
                                if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                                    await self.control.await_element_appear(TO_HOME, click=True, time_out=3)
                            else:
                                await self.device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 200)
                                await asyncio.sleep(2)
                                await self.control.matching_one(COLLECT_ALL, click=True)
                                await self.device.swipe([(1000, 100), (1000, 110), (1000, 150), (1000, 950)], 200)
                                await asyncio.sleep(2)
                                await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=3)
                else:
                    await self.device.click_back()
                    await self.return_home()
            else:
                if self.order_policy == "不使用超空间信标":
                    await self.return_home()
                    raise OrderFinishes("不使用超空间信标,订单结束 <<<")
                else:
                    await self.device.click_back()

        # 第三步： 切换天赋至 -Time
        await self.change_talent(TALENT_TIME)

        # 第四步： 获取新订单 （需要确认加速获取订单的规则）
        self.logging.log(f"{TASK_NAME} 获取新订单 >>>", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_ORDER, click=True, time_out=3)
        await self.control.await_element_appear(ORDER_DEPARTURE, click=True, time_out=3)
        await self.control.await_element_appear(ORDER_CLOSE, click=True, time_out=3)

        if await self.control.await_element_appear(MORE_ORDER, click=True, time_out=3):
            if self.order_policy == "不使用超空间信标":
                await self.return_home()
                raise OrderFinishes("不使用超空间信标,订单结束 <<<")
            if await self.control.await_element_appear(GEC_ORDER, click=False, time_out=3):
                if self.order_policy == "使用GEC购买信标":
                    await self.control.await_element_appear(GEC_ORDER, click=True, time_out=1)
                else:
                    await self.return_home()
                    raise OrderFinishes("超空间信标不足,订单结束 <<<")
            if self.order_policy == "使用超空间信标":
                await self.control.await_element_appear(BEACON_ORDER, click=True, time_out=3)
            await self.control.await_element_appear(BEACON_CONFIRM, click=True, time_out=3)

    async def change_talent(self, mode):
        self.logging.log(f"{TASK_NAME} 修改天赋至{mode.name} <<<", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(Templates.MORE_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_TALENT, click=True, time_out=3)
        await self.control.await_element_appear(TALENT_CHOICE, click=True, time_out=3)
        await self.control.await_element_appear(mode, click=True, time_out=3)
        await self.control.await_element_appear(CONFIRM_TALENT, click=True, time_out=3, sleep=1)
        await self.control.await_element_appear(TO_HOME, click=True, time_out=3, sleep=1)
