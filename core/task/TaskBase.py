import asyncio
import logging
import time

from core.ControlTools import ControlTools
from core.LogManager import LogManager
from core.NovaException import TaskFinishes
from core.LoadTemplates import Templates
from device_operation.DeviceUtils import DeviceUtils
from models.Module import Module

WAITING = 0
RUNNING = 1
SUCCESS = 2
FAILED = -1


class TaskBase:
    def __init__(self, target):
        self.revenge = False
        self.target = target
        self.status = WAITING
        self.logging = LogManager()
        self.device = DeviceUtils(target)

        self.control = ControlTools(target, self.device)
        self.module = Module.get(Module.name == target)

    async def prepare(self):
        """任务前置操作"""
        await self.device.async_init()
        self._update_status(WAITING)

    async def execute(self):
        """主执行逻辑（需子类实现）"""
        raise NotImplementedError

    async def cleanup(self):
        """任务后置操作"""
        self._update_status(SUCCESS)

    def _update_status(self, status):
        """更新任务状态"""
        self.status = status

    async def return_home(self):
        await self.relogin_check()
        await self.close_check()
        await self.recall_check()
        await self.shortcut_check()
        await self.select_fleet_check()
        await self.none_available_check()
        await self.control.matching_one(Templates.TO_HOME, click=True, sleep=2)

    async def relogin_check(self):
        """检查是否需要重新登录"""
        if await self.control.matching_one(Templates.SIGN_BACK_IN):
            if self.module.auto_relogin:
                relogin_time = self.module.relogin_time
                self.logging.log(f"检测到已登出，等待 {relogin_time} 秒后重新登录...", self.target, logging.INFO)
                if relogin_time is None:
                    relogin_time = 600
                await asyncio.sleep(relogin_time)
                await self.control.matching_one(Templates.CONFIRM_RELOGIN, click=True, sleep=10)
                self.logging.log("重新登录成功！", self.target, logging.INFO)
            else:
                raise TaskFinishes("检测到已登出, 未开启自动抢登, 执行结束")

    async def close_check(self):
        for template in Templates.CLOSE_BUTTONS:
            await self.control.matching_one(template, click=True)

    async def recall_check(self):
        if await self.control.matching_one(Templates.RECALL):
            await self.device.click_back()

    async def shortcut_check(self):
        if await self.control.matching_one(Templates.IN_SHORTCUT):
            await self.device.click_back()

    async def select_fleet_check(self):
        if await self.control.matching_one(Templates.SELECTALL):
            await self.device.click_back()

    async def none_available_check(self):
        if await self.control.matching_one(Templates.NO_WORKSHIPS):
            await self.device.click_back()

    async def attack(self):
        await self.control.await_element_appear(Templates.ATTACK_BUTTON, click=True, time_out=3)
        if await self.control.await_element_appear(Templates.REVENGE, time_out=2):
            self.revenge = True
            await self.control.matching_one(Templates.REVENGE_ATTACK, click=True, sleep=1)
        await self.control.matching_one(Templates.REPAIR, click=True, sleep=1)
        await self.control.await_element_appear(Templates.SELECTALL, click=True, time_out=3, sleep=0.5)

        if await self.control.await_element_appear(Templates.CONFIRM_ATTACK, click=True, time_out=0.5):
            await self.combat_checks()
            if self.revenge:
                await self.recall_fleets()
                self.logging.log("等待复仇", self.target)
                await self.combat_checks()
                self.revenge = False

    async def combat_checks(self):
        self.logging.log("检查是否进入战斗 >>>", self.target, logging.DEBUG)
        if await self.control.await_element_appear(Templates.IN_BATTLE, time_out=180):
            self.logging.log("进入战斗<<<", self.target, logging.DEBUG)
            self.logging.log("检查战斗是否结束>>>", self.target, logging.DEBUG)
            if await self.control.await_element_disappear(Templates.IN_BATTLE, time_out=120, sleep=3):
                self.logging.log("战斗结束<<<", self.target, logging.DEBUG)

    async def recall_fleets(self):
        await self.control.await_element_appear(Templates.MENUS, click=True, time_out=2)
        await self.control.await_element_appear(Templates.FLEETS_MENU, click=True, time_out=3, sleep=2)
        coordinate = await self.control.matching_one(Templates.HOVER_RECALL, click=False, offset_y=-1000)
        await self.control.await_element_appear(Templates.HOVER_RECALL, click=True, time_out=3)
        self.device.click(coordinate)
        time.sleep(1)

    # async def collect_wreckage(self):
    #     self.logging.log("开始采集残骸>>>", self.target, logging.DEBUG)
    #     while True:
    #         for wreckage in Templates.WRECKAGE_LIST:
    #             coords = await self.control.move_coordinates(wreckage)
    #             coordinates.append(coords)
    #         self.logging.log(f"got coordinates: {coordinates}", self.target, logging.DEBUG)
    #         for coordinate in coordinates:
    #             self.control.device.click(coordinate)
    #             await self.control.await_element_appear(Templates.COLLECT, click=True, time_out=3)
    #             if await self.control.await_element_appear(Templates.NO_WORKSHIPS, click=False, time_out=2):
    #                 await self.control.await_element_appear(Templates.CONFIRM_RELOGIN, click=True, time_out=2)
    #                 self.logging.log("采集残骸结束<<<", self.target, logging.DEBUG)
    #                 return

    async def collect_wreckage(self):
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
                        self.control.device.click(coordinate)
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
