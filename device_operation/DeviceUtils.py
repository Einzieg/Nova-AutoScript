import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path

import cv2
from mmumu.api import get_mumu_path
from msc.adbcap import ADBCap
from msc.droidcast import DroidCast
from msc.minicap import MiniCap

if sys.platform != 'darwin':
    from msc.mumu import MuMuCap
from msc.screencap import ScreenCap
from mtc.adb import ADBTouch
from mtc.maatouch import MaaTouch
from mtc.minitouch import MiniTouch

if sys.platform != 'darwin':
    from mtc.mumu import MuMuTouch
from mtc.touch import Touch

from core.LogManager import LogManager
from device_operation.AdbClient import AdbClient
from models import Config, Module


class DeviceUtils:
    CAP_TOOLS = {
        'ADB': ADBCap,
        'MiniCap': MiniCap,
        'DroidCast': DroidCast
    }
    TOUCH_TOOLS = {
        'ADB': ADBTouch,
        'MiniTouch': MiniTouch,
        'MaaTouch': MaaTouch
    }
    if sys.platform != 'darwin':
        CAP_TOOLS['MuMu'] = MuMuCap
        TOUCH_TOOLS['MuMu'] = MuMuTouch

    _instances = {}
    _initialized_flags = {}
    _async_initialized_flags = {}

    def __init__(self, name):
        """
        初始化DeviceUtils实例。
        :param name: 任务名称
        """
        self.conf = Config.get_or_create(id=1)[0]
        self.module = Module.get_or_none(Module.name == name)
        self.name = name
        self.logging = LogManager()

        if self.module.simulator_index < 5555:
            self.port = 16384 + 32 * self.module.simulator_index
            self.logging.log(f"计算端口号为 {self.port}", self.name, logging.DEBUG)
        else:
            self.port = self.module.simulator_index

        self.adb = AdbClient(self.name, port=self.port)

        # 延迟初始化
        self.capture_tool = None
        self.touch_tool = None

        type(self)._initialized_flags[name] = True

    def _init_capture_tool(self):
        try:
            tool_class = self.CAP_TOOLS.get(self.conf.cap_tool)
            if not tool_class:
                raise TypeError("未知的截图工具")
            if tool_class.__name__ == 'MuMuCap':
                self.capture_tool = tool_class(instance_index=self.module.simulator_index)
            else:
                self.capture_tool = tool_class(serial=f'127.0.0.1:{self.port}')
            self.logging.log(f"截图工具 {tool_class.__name__} 初始化成功", self.name, logging.INFO)
        except Exception as e:
            self.logging.log(f"初始化截图工具失败: {str(e)}", self.name, logging.ERROR)
            self.capture_tool = None

    def _init_touch_tool(self):
        """初始化触摸工具"""
        try:
            tool_class = self.TOUCH_TOOLS.get(self.conf.touch_tool)
            if not tool_class:
                raise ValueError("未知的点击工具")
            if tool_class.__name__ == 'MuMuTouch':
                self.touch_tool = tool_class(instance_index=self.module.simulator_index)
            else:
                self.touch_tool = tool_class(serial=f'127.0.0.1:{self.port}')
            self.logging.log(f"点击工具 {tool_class.__name__} 初始化成功", self.name, logging.INFO)
        except Exception as e:
            self.logging.log(f"初始化触摸工具失败: {str(e)}", self.name, logging.ERROR)
            self.touch_tool = None

    async def async_init(self):
        """异步初始化逻辑"""
        self.logging.log("正在执行工具初始化...", self.name, logging.INFO)
        if self._async_initialized_flags.get(self.name, False):
            self.logging.log("工具已初始化, 跳过初始化", self.name, logging.INFO)
            return

        try:
            self.logging.log("正在连接设备...", self.name, logging.DEBUG)
            conn = await self.adb.connect_tcp(max_retries=10)
            if not conn:
                raise Exception("连接设备失败,可能原因:序列号填写错误/模拟器未开启/端口被占用")

            # 连接成功后初始化工具
            self._init_capture_tool()
            self._init_touch_tool()

            type(self)._async_initialized_flags[self.name] = True
            self.logging.log("工具初始化完成", self.name, logging.INFO)
        except Exception as e:
            self.logging.log("工具初始化失败", self.name, logging.ERROR)
            self._cleanup_instance(self.name)
            raise Exception("工具初始化失败") from e

    def _cleanup_instance(self, name):
        """清理指定 name 的实例状态"""
        type(self)._instances.pop(name, None)
        type(self)._initialized_flags.pop(name, None)
        type(self)._async_initialized_flags.pop(name, None)

    def __perform_screencap(self, controller: ScreenCap):
        self.logging.log(f"正在使用 {controller.__class__.__name__} 截图...", self.name, logging.DEBUG)
        return controller.screencap()

    async def __perform_click(self, controller: Touch, x, y):
        self.logging.log(f"正在使用 {controller.__class__.__name__} 点击坐标 {x}, {y}...", self.name, logging.DEBUG)
        await controller.click(x, y)

    async def __perform_swipe(self, controller: Touch, points: list, duration: int):
        self.logging.log(f"正在使用 {controller.__class__.__name__} 滑动...", self.name, logging.DEBUG)
        await controller.swipe(points, duration)

    async def __perform_pinch(self, controller: Touch, start1, start2, end1, end2, duration: int):
        self.logging.log(f"正在使用 {controller.__class__.__name__} 缩放...", self.name, logging.DEBUG)
        await controller.pinch(start1, start2, end1, end2, duration)

    async def push_scripts(self):
        """推送脚本文件到设备"""
        try:
            await self.adb.push(str(Path(__file__).resolve().parent.parent / "static/zoom_out.sh"), "/sdcard/zoom_out.sh")
            self.logging.log("脚本文件推送成功", self.name, logging.DEBUG)
        except Exception as e:
            self.logging.log(f"推送脚本文件时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def click_back(self):
        """模拟点击返回键"""
        try:
            await self.adb.shell("input keyevent 4")
            self.logging.log("已点击返回键", self.name, logging.DEBUG)
        except Exception as e:
            self.logging.log(f"点击返回键时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def zoom_out(self):
        """
        执行缩放操作
        该操作只支持 MiniTouch和 MaaTouch
        """
        try:
            self.logging.log("开始执行缩小操作...", self.name, logging.DEBUG)
            if not self.touch_tool:
                raise ValueError("触摸工具未初始化")
            await self.__perform_pinch(self.touch_tool, (650, 235), (1265, 840), (900, 480), (1020, 600), duration=400)
            self.logging.log("已执行缩放操作", self.name, logging.DEBUG)
        except Exception as e:
            self.logging.log(f"执行缩放操作时出错: {str(e)}", self.name, logging.ERROR)
            raise

    def get_screencap(self, max_retries: int = 3):
        if not self.capture_tool:
            self._init_capture_tool()

        start_time = time.time()
        for attempt in range(max_retries):
            try:
                if not self.capture_tool:
                    raise TypeError("截图工具未初始化")
                screencap = self.__perform_screencap(self.capture_tool)
                self.logging.log(f"{self.conf.cap_tool} 截图成功,耗时 {time.time() - start_time:.2f}s", self.name, logging.DEBUG)
                return screencap
            except Exception as e:
                self.logging.log(f"{self.conf.cap_tool} 截图失败, 重试 {attempt + 1}: {str(e)}", self.name, logging.ERROR)
                if attempt == max_retries - 1:
                    raise

    def save_screencap(self, filename: str = "screenshot.png"):
        """保存截图到指定路径"""
        try:
            screencap = self.get_screencap()
            cv2.imwrite(filename, screencap)
            self.logging.log(f"已保存截图", self.name, logging.INFO)
        except Exception as e:
            self.logging.log(f"保存截图时出错: {str(e)}", self.name, logging.ERROR)
            raise Exception from e

    async def click(self, coordinate):
        if not self.touch_tool:
            self._init_touch_tool()

        x, y = coordinate
        try:
            if not self.touch_tool:
                raise ValueError("点击工具未初始化")
            await self.__perform_click(self.touch_tool, x, y)
        except Exception as e:
            self.logging.log(f"点击坐标时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def swipe(self, points: list, duration: int):
        if not self.touch_tool:
            self._init_touch_tool()

        try:
            if not self.touch_tool:
                raise ValueError("触摸工具未初始化")
            await self.__perform_swipe(self.touch_tool, points, duration)
        except Exception as e:
            self.logging.log(f"滑动时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def start_simulator(self):
        try:
            # "D:/Software/MuMuPlayer-12.0/nx_main/MuMuManager.exe control -v 0 launch"
            mumu_path = get_mumu_path()
            if mumu_path:
                manager_path = Path(mumu_path) / 'nx_main/MuMuManager.exe'
                if not manager_path.exists():
                    raise FileNotFoundError(f"文件 {manager_path} 不存在")
                subprocess.Popen([manager_path, "control", "-v", str(self.module.simulator_index), "launch"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 encoding="utf-8",
                                 shell=False)
                self.logging.log("启动模拟器成功", self.name, logging.INFO)
                await asyncio.sleep(10)
                await self.async_init()
            else:
                self.logging.log("未找到模拟器路径", self.name, logging.ERROR)
                raise Exception("未找到模拟器路径")
        except Exception as e:
            self.logging.log(f"启动模拟器失败: {str(e)}", self.name, logging.ERROR)
            raise

    async def check_running_status(self):
        """检查应用是否正在运行"""
        try:
            output = await self.adb.shell("ps")
            if "com.stone3.ig" in output:
                self.logging.log("应用正在运行", self.name, logging.INFO)
                output = await self.adb.shell("dumpsys window | grep mFocusedWindow")
                if "com.stone3.ig" in output:
                    self.logging.log("应用在前台运行", self.name, logging.INFO)
                    return True
                else:
                    self.logging.log("应用未在前台运行,尝试重新打开应用", self.name, logging.INFO)
                    await self.close_app()
                    await asyncio.sleep(3)
                    await self.launch_app()
            else:
                await self.launch_app()
        except Exception as e:
            self.logging.log(f"检查应用运行状态时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def launch_app(self):
        try:
            await self.adb.shell("am start -n com.stone3.ig/com.google.firebase.MessagingUnityPlayerActivity")
            self.logging.log("已启动应用", self.name, logging.INFO)
        except Exception as e:
            self.logging.log(f"启动应用时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def close_app(self):
        try:
            await self.adb.shell("am force-stop com.stone3.ig")
            self.logging.log("已关闭应用", self.name, logging.DEBUG)
        except Exception as e:
            self.logging.log(f"关闭应用时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def check_wm_size(self):
        try:
            resource = await self.adb.shell("wm size")
            output = resource.strip()
            if output.startswith("Physical size:"):
                parts = output.split()
                if len(parts) >= 3:
                    width, height = map(int, parts[2].split('x'))
                    self.logging.log(f"获取屏幕尺寸为 {width}x{height}", self.name, logging.DEBUG)
                    return width, height
            self.logging.log("未找到屏幕尺寸信息", self.name, logging.DEBUG)
            return None, None
        except Exception as e:
            self.logging.log(f"获取屏幕尺寸时出错: {str(e)}", self.name, logging.ERROR)


if __name__ == '__main__':
    from mmumu.manger import get_mumu_path

    print(get_mumu_path())
    # device = DeviceUtils("6")
    # asyncio.run(device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 500))
