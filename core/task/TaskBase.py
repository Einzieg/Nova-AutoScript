import asyncio
import json
import logging

from core.tools.ControlTools import ControlTools
from core.LoadTemplates import Templates
from core.LogManager import LogManager
from core.NovaException import TaskFinishes
from device_operation.DeviceUtils import DeviceUtils
from models.Module import Module
from models.Config import Config

WAITING = 0
RUNNING = 1
SUCCESS = 2
FAILED = -1

fleet_map = {
    "fleet1": (1290, 200),
    "fleet2": (1290, 325),
    "fleet3": (1290, 450),
    "fleet4": (1290, 575),
    "fleet5": (1290, 700),
    "fleet6": (1290, 825),
}


class TaskBase:
    def __init__(self, target):
        self.revenge = False
        self.target = target
        self.status = WAITING
        self.logging = LogManager()
        self.device = DeviceUtils(target)

        self.control = ControlTools(target, self.device)
        self.module = Module.get(Module.name == target)
        self.config = Config.get_or_create(id=1)[0]

    async def prepare(self):
        """任务前置操作"""
        self._update_status(WAITING)

    async def execute(self):
        """主执行逻辑（需子类实现）"""
        await self.device.async_init()
        # 可能需要增加检查游戏运行状态,防止游戏闪退
        raise NotImplementedError

    async def cleanup(self):
        """任务后置操作"""
        self._update_status(SUCCESS)

    def _update_status(self, status):
        """更新任务状态"""
        self.status = status

    @staticmethod
    def _enabled(value):
        if isinstance(value, memoryview):
            value = value.tobytes()
        if isinstance(value, bytes):
            return value not in (b'', b'\x00', b'0', b'False', b'false')
        return bool(value)

    async def return_home(self, optimize = False):
        if optimize:
            image = self.device.get_screencap()
        else:
            image = None
            
        await self.relogin_check(image)
        await self.close_check(image)
        await self.recall_check(image)
        await self.shortcut_check(image)
        await self.select_fleet_check(image)
        await self.none_available_check(image)
        await self.disconnected_check(image)
        await self.control.matching_one(Templates.TO_HOME, click=True, image=image)

    async def relogin_check(self, image = None):
        """检查是否需要重新登录"""

        # if not await self.control.matching_one(Templates.SIGN_BACK_IN):
        #    return False

        if not await self.control.matching_text("请重新登录", click=False, exact=False, image=image):
            return False

        self.module = Module.get(Module.name == self.target)
        if not self._enabled(self.module.auto_relogin):
            raise TaskFinishes("检测到已登出, 未开启自动抢登, 执行结束")

        relogin_time = self.module.relogin_time
        if relogin_time is None:
            relogin_time = 600

        self.logging.log(f"检测到已登出，等待 {relogin_time} 秒后重新登录...", self.target, logging.INFO)
        await asyncio.sleep(relogin_time)

        if not await self.control.await_text_appear("确定", click=True, time_out=30, sleep=1):
            raise TaskFinishes("检测到已登出, 但未找到重新登录确认按钮")

        # await asyncio.sleep(30)

        self.logging.log("重新登录成功！", self.target, logging.INFO)
        return True

    async def close_check(self, image = None):
        for template in Templates.CLOSE_BUTTONS:
            await self.control.matching_one(template, click=True, image=image)

    async def recall_check(self, image = None):
        if await self.control.matching_one(Templates.RECALL, image=image):
            await self.device.click_back()

    async def shortcut_check(self, image = None):
        if await self.control.matching_one(Templates.IN_SHORTCUT, image=image):
            await self.device.click_back()

    async def select_fleet_check(self, image = None):
        if await self.control.matching_one(Templates.SELECTALL, image=image):
            await self.device.click_back()

    async def none_available_check(self, image = None):
        if await self.control.matching_one(Templates.NO_WORKSHIPS, image=image):
            await self.device.click_back()

    async def sign_back_check(self):
        await self.relogin_check()

    async def disconnected_check(self, image = None):
        if await self.control.matching_one(Templates.DISCONNECTED, image=image):
            raise TaskFinishes("无法连接到网络")

    async def attack(self, sleet_all=False):
        self.revenge = False
        await self.control.await_text_appear("攻击", click=True, time_out=3)
        if await self.control.await_text_appear("仇恨值已满", exact=False, time_out=2):
            self.revenge = True
            await self.control.await_text_appear("攻击", click=True, sleep=1)
        await self.control.matching_text("快速维修", click=True, sleep=1)
        fleets = json.loads(self.module.attack_fleet)
        if "all" in fleets or sleet_all:
            await self.control.await_text_appear("选择全部", click=True, time_out=3, sleep=0.5)
        else:
            for fleet in fleets:
                await self.device.click(fleet_map[fleet])

        if await self.control.await_text_appear("确定", click=True, time_out=0.5):
            await self.combat_checks()
            if self.revenge:
                await self.recall_fleets()
                self.logging.log("等待复仇", self.target)
                await self.combat_checks()
                self.revenge = False

    async def combat_checks(self):
        self.logging.log("检查是否进入战斗 >>>", self.target, logging.DEBUG)
        if await self.control.await_text_appear("战斗中", time_out=180, exact=False):
            self.logging.log("进入战斗<<<", self.target, logging.DEBUG)
            self.logging.log("检查战斗是否结束>>>", self.target, logging.DEBUG)
            if await self.control.await_text_disappear("战斗中", time_out=120, sleep=3, exact=False):
                self.logging.log("战斗结束<<<", self.target, logging.DEBUG)

    async def recall_fleets(self):
        for template in Templates.MENUS:
            await self.control.await_element_appear(template, click=True, time_out=2)
        await self.control.await_text_appear("舰队", click=True, time_out=3, sleep=2)
        await self.control.await_text_appear("悬停召回", click=True, time_out=2)
        await self.device.click_back()
        await asyncio.sleep(1)

    async def collect_wreckage_b(self):
        """Collects wreckage by iterating through predefined templates."""
        self.logging.log("开始采集残骸>>>", self.target, logging.DEBUG)
        coordinates = []  # Initialize coordinates list
        total_retry = 8
        try:
            wreckage_attempted = 0
            while True:
                # Phase 1: Find all wreckage locations
                for wreckage in Templates.WRECKAGE_LIST:
                    coords = await self.control.move_coordinates(wreckage)
                    if coords:  # Only append if coordinates were found
                        for coord in coords:
                            coordinates.append(coord)

                self.logging.log(f"Found {len(coordinates)} wreckage coordinates: {coordinates}", self.target, logging.DEBUG)

                if not coordinates:  # No wreckage found
                    self.logging.log("未发现残骸<<<", self.target, logging.DEBUG)
                    return

                # Phase 2: Process each wreckage
                for coordinate in coordinates.copy():  # Use copy to avoid modifying during iteration
                    try:
                        await self.control.device.click(coordinate)
                        wreckage_attempted += 1
                        # Attempt collection
                        if await self.control.await_element_appear(Templates.COLLECT, click=True, time_out=3):
                            coordinates.remove(coordinate)  # Successfully processed
                            continue

                        if await self.control.await_element_appear(Templates.RECALL, time_out=2):
                            coordinates.remove(coordinate)
                            continue

                        # Check for no workships condition
                        if await self.control.await_element_appear(Templates.NO_WORKSHIPS, click=False, time_out=2):
                            await self.control.await_element_appear(Templates.CONFIRM_RELOGIN, click=True, time_out=2)
                            self.logging.log("采集残骸结束: 没有工作舰<<<", self.target, logging.DEBUG)
                            return

                    except Exception as e:
                        self.logging.log(f"处理残骸时出错 {coordinate}: {str(e)}", self.target, logging.ERROR)
                        continue

                # Exit condition when all wreckage processed
                if not coordinates:
                    self.logging.log("所有残骸采集完成<<<", self.target, logging.DEBUG)
                    return
                if wreckage_attempted >= total_retry:
                    self.logging.log("已尝试8次残骸采集<<<", self.target, logging.DEBUG)
                    return

        except Exception as e:
            self.logging.log(f"采集残骸过程中发生严重错误: {str(e)}", self.target, logging.ERROR)
        finally:
            self.logging.log("采集残骸结束<<<", self.target, logging.DEBUG)
