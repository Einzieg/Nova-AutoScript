import json
from pathlib import Path
from typing import List, Any, Optional

from core.LoadTemplates import Template
from core.NovaException import OrderFinishes
from core.task.TaskBase import *
from core.tools.OcrTools import OcrTools
from core.tools.TimeTools import TimeTools
from core.tools.ImageTools import ImageTools

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 切换天赋所需模版

TO_TALENT = Template(
    name="天赋按钮",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/system/talent.png"
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
    template_path=ROOT_DIR / "static/novaimgs/system/orders.png"
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
SPEEDUP_15_MIN = Template(
    name="15分钟加速",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/seppdup_15_min.png"
)
SPEEDUO_1_HOUR = Template(
    name="1小时加速",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/speedup_1_hour.png"
)
SPEEDUO_3_HOUR = Template(
    name="3小时加速",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/order/speedup_3_hour.png"
)
QUEUE_SPEEDUP = Template(
    name="批量使用加速",
    threshold=0.9,
    template_path=ROOT_DIR / "static/novaimgs/order/quick_speedup.png"
)
CLOSE_FACTORY = Template(
    name="退出工厂",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/button/btn_close1.png"
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
ORDER_FINISH = Template(
    name="订单完成",
    threshold=0.95,
    template_path=ROOT_DIR / "static/novaimgs/order/order_finish.png"
)

QHOUR_SPEEDUP_OFFSET_X = 410
QHOUR_SPEEDUP_OFFSET_Y = 10
SPEEDUP_MASK = {
    "retain": [(1300, 130, 1870, 870)],
    "remove": [(1560, 240, 1840, 870), (1300, 130, 1625, 200)]
}
SPEEDUP_SECOND = {
    "15_min": 15 * 60,
    "1_hour": 60 * 60,
    "3_hour": 3 * 60 * 60
}

TASK_NAME = "订单"


class Order(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.target = target
        self.order_policy = self.module.order_policy
        self.order_hasten_policy = self.module.order_hasten_policy
        self.order_speeduo_policy = json.loads(self.module.order_speeduo_policy)
        self.ocr_tool = self.config.ocr_tool
        self.ocr = OcrTools()
        self.time_tools = TimeTools()
        self.image_tool = ImageTools()

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
                for _ in range(order_times):
                    await self.order_process()
            else:
                while True:
                    await self.return_home()
                    await self.order_process()
        except OrderFinishes as e:
            self.logging.log(e, self.target)
            self._update_status(SUCCESS)
            return

    @staticmethod
    def get_next_element(data_list: List[Any], target: Any) -> Optional[Any]:
        """
        在列表中查找目标元素，并返回其紧邻的下一个元素。

        Args:
            data_list: 要搜索的列表。
            target: 要查找的目标元素。

        Returns:
            下一个元素的值，如果未找到目标或目标是列表的最后一个元素，则返回 0。
        """
        try:
            index_of_target = data_list.index(target)
            next_index = index_of_target + 1

            if next_index < len(data_list):
                return data_list[next_index]
            else:
                return 0

        except ValueError:
            return 0

    @staticmethod
    def str2int(s: str) -> int:
        try:
            return int(s)
        except ValueError:
            return 0

    async def order_process(self):
        # 第一步：切换天赋至 +RC
        await self.change_talent(TALENT_RC)

        # 第二步： 执行生产 / 提交
        if '订单电路板' in self.order_hasten_policy:
            await self._process_pcba()

        if '使用制造加速' in self.order_hasten_policy:
            await self._process_manufacture_speedup()

        # 第三步： 切换天赋至 -Time
        await self.change_talent(TALENT_TIME)

        # 第四步： 获取新订单
        await self._fetch_new_order()

    async def _process_pcba(self):
        self.logging.log(f"{TASK_NAME} 使用电路板 <<<", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_ORDER, click=True, time_out=3)
        await self.control.await_element_appear(PCBA_DELIVERY, click=True, time_out=3)
        if await self.control.await_element_appear(PCBA_INSUFFICIENT, time_out=2):
            await self.return_home()
            raise OrderFinishes("PCBA道具不足")
        await self.control.await_element_appear(DELIVERY_CONFIRM, click=True, time_out=3)
        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)

    async def _process_manufacture_speedup(self):
        self.logging.log(f"{TASK_NAME} 使用制造加速 <<<", self.target, logging.DEBUG)
        # 打开制造界面
        has_panel = await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=1) | await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=1)
        if not has_panel:
            await self.return_home()
            return

        await self.control.await_element_appear(ECONOMY, click=True, time_out=1)
        if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
            await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
            if await self.control.await_element_appear(PRODUCE_ORDER, click=True, time_out=2):
                await self.control.await_element_appear(GOTO_FACTORY, click=True, time_out=2)
                if await self.control.await_element_appear(DEVELOPMENT, click=False, time_out=2):
                    raise OrderFinishes("无部件图纸")
                await self.control.await_element_appear(BACK_TO_QUEUE, click=True, time_out=2)
                # 加速循环
                speedup_running = True
                while speedup_running:
                    await self.control.await_element_appear(SMART_PRODUCTION, click=True, time_out=2, sleep=1.5)
                    # TODO 看有没有资源不够的弹窗

                    if not await self.control.await_element_appear(SPEEDUP_PRODUCTION, click=True, time_out=2):
                        break
                    while True:
                        img = self.image_tool.apply_mask(self.device.get_screencap(), SPEEDUP_MASK)
                        fabricate_ocr = await self.ocr.async_ocr(provider=self.ocr_tool, image=img)
                        if not fabricate_ocr['success']:
                            break
                        print(fabricate_ocr)
                        try:
                            fabricate_time = self.time_tools.parse_duration_to_seconds(fabricate_ocr['texts'][0])
                        except IndexError:
                            break
                        props_remaining = {
                            "15_min": self.str2int(self.get_next_element(fabricate_ocr['texts'], "15分钟部件加速")),
                            "1_hour": self.str2int(self.get_next_element(fabricate_ocr['texts'], "1小时部件加速")),
                            "3_hour": self.str2int(self.get_next_element(fabricate_ocr['texts'], "3小时部件加速"))
                        }
                        self.logging.log(props_remaining, self.target, logging.DEBUG)

                        for speeduo_policy in self.order_speeduo_policy:
                            if fabricate_time >= SPEEDUP_SECOND[speeduo_policy]:
                                if speeduo_policy == "15_min" and props_remaining['15_min']:
                                    await self.control.await_element_appear(SPEEDUP_15_MIN, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                elif speeduo_policy == "1_hour" and props_remaining['1_hour']:
                                    await self.control.await_element_appear(SPEEDUO_1_HOUR, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                elif speeduo_policy == "3_hour" and props_remaining['3_hour']:
                                    await self.control.await_element_appear(SPEEDUO_3_HOUR, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                # 如果当前策略阈值满足但对应道具没有库存，尝试下一个策略
                                continue

                        await self.control.await_element_appear(QUEUE_SPEEDUP, click=True, time_out=2, sleep=1)

                        img = self.image_tool.apply_mask(self.device.get_screencap(), SPEEDUP_MASK)
                        fabricate_ocr = await self.ocr.async_ocr(provider=self.ocr_tool, image=img)
                        if not fabricate_ocr['success']:
                            speedup_running = False
                            break
                        try:
                            fabricate_time = self.time_tools.parse_duration_to_seconds(fabricate_ocr['texts'][0])
                        except IndexError:
                            speedup_running = False
                            break

                        if fabricate_time and fabricate_time <= SPEEDUP_SECOND['15_min']:
                            await self.control.await_element_appear(SPEEDUP_15_MIN, click=True, time_out=2, offset_x=QHOUR_SPEEDUP_OFFSET_X, offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                            speedup_running = False
                            break
                        if fabricate_time == 0:
                            speedup_running = False
                            break
                if not speedup_running:
                    await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                    # 提交剩余订单
                    await self._submit_remaining_orders()
                    return
                await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                # 提交剩余订单
                await self._submit_remaining_orders()
            else:
                await self.device.click_back()
                await self.return_home()
        else:
            if self.order_policy == "不使用超空间信标":
                await self.return_home()
                raise OrderFinishes("不使用超空间信标,订单结束 <<<")
            else:
                await self.device.click_back()

    async def _submit_remaining_orders(self):
        # 如果还能打开制造面板说明还有订单未提交，尝试收集并继续
        if await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=2) | await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=2):
            if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
                if not await self.control.await_element_appear(PRODUCE_ORDER, click=False, time_out=2):
                    if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                else:
                    await self.device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 200)
                    await asyncio.sleep(2)
                    await self.control.matching_one(COLLECT_ALL, click=True, sleep=1)
                    await self.device.swipe([(1000, 100), (1000, 110), (1000, 150), (1000, 950)], 200)
                    await asyncio.sleep(2)
                    await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=3)

    async def _fetch_new_order(self):
        self.logging.log(f"{TASK_NAME} 获取新订单 >>>", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_ORDER, click=True, time_out=3, sleep=3)
        if await self.control.matching_one(ORDER_FINISH):
            raise OrderFinishes("今日订单已完成 <<<")
        await self.control.await_element_appear(ORDER_DEPARTURE, click=True, time_out=3)
        await self.control.await_element_appear(ORDER_CLOSE, click=True, time_out=3)

        if await self.control.await_element_appear(MORE_ORDER, click=True, time_out=3):
            await self._handle_more_order()

    async def _handle_more_order(self):
        if self.order_policy == "不使用超空间信标":
            await self.return_home()
            raise OrderFinishes("不使用超空间信标,订单结束 <<<")

        if self.order_policy == "使用超空间信标" or self.order_policy == "使用GEC购买信标":
            await self.control.await_element_appear(BEACON_ORDER, click=True, time_out=3)

        if await self.control.await_element_appear(GEC_ORDER, click=False, time_out=3):
            if self.order_policy == "使用GEC购买信标":
                await self.control.await_element_appear(GEC_ORDER, click=True, time_out=1)
            else:
                await self.return_home()
                raise OrderFinishes("超空间信标不足,订单结束 <<<")

        await self.control.await_element_appear(BEACON_CONFIRM, click=True, time_out=3)

    async def change_talent(self, mode):
        self.logging.log(f"{TASK_NAME} 修改天赋至{mode.name} <<<", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(Templates.MORE_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_TALENT, click=True, time_out=3)
        await self.control.await_element_appear(TALENT_CHOICE, click=True, time_out=3)
        await self.control.await_element_appear(mode, click=True, time_out=3)
        await self.control.await_element_appear(CONFIRM_TALENT, click=True, time_out=3, sleep=1)
        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3, sleep=1)
