import asyncio
import logging
import subprocess
import time
from pathlib import Path


from msc.adbcap import ADBCap
from msc.droidcast import DroidCast
from msc.minicap import MiniCap
from msc.mumu import MuMuCap
from msc.screencap import ScreenCap
from mtc.adb import ADBTouch
from mtc.maatouch import MaaTouch
from mtc.minitouch import MiniTouch
from mtc.mumu import MuMuTouch
from mtc.touch import Touch

from core.LogManager import LogManager
from device_operation.AdbClient import AdbClient
from models import Config, Module


class DeviceUtils:
    CAP_TOOLS = {
        'MuMu': MuMuCap,
        'ADB': ADBCap,
        'MiniCap': MiniCap,
        'DroidCast': DroidCast
    }
    TOUCH_TOOLS = {
        'MuMu': MuMuTouch,
        'ADB': ADBTouch,
        'MiniTouch': MiniTouch,
        'MaaTouch': MaaTouch
    }

    _instances = {}
    _initialized_flags = {}
    _async_initialized_flags = {}

    def __new__(cls, name, *args, **kwargs):
        if name in cls._instances:
            return cls._instances[name]

        instance = super().__new__(cls)
        cls._instances[name] = instance
        cls._initialized_flags[name] = False
        cls._async_initialized_flags[name] = False
        return instance

    def __init__(self, name):
        """
        初始化DeviceUtils实例。
        :param name: 任务名称
        """
        if self._initialized_flags[name]:
            return

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
        type(self)._initialized_flags[name] = True

    async def async_init(self):
        """异步初始化逻辑"""
        name = self.name

        # 如果已异步初始化，跳过
        if self._async_initialized_flags[name]:
            return

        try:
            self.logging.log("正在连接设备...", self.name, logging.DEBUG)
            conn = await self.adb.connect_tcp()
            if not conn:
                raise Exception("连接设备失败,可能原因:序列号填写错误/模拟器未开启/端口被占用")
            await self.push_scripts()
            # 异步初始化成功
            type(self)._async_initialized_flags[name] = True
        except Exception as e:
            self._cleanup_instance(name)
            raise

    def _cleanup_instance(self, name):
        """清理指定 name 的实例状态"""
        type(self)._instances.pop(name, None)
        type(self)._initialized_flags.pop(name, None)
        type(self)._async_initialized_flags.pop(name, None)

    @staticmethod
    def __perform_screencap(controller: ScreenCap):
        return controller.screencap()

    @staticmethod
    def __perform_click(controller: Touch, x, y):
        controller.click(x, y)

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
        """执行缩放操作"""
        try:
            await self.adb.shell("sh /sdcard/zoom_out.sh")
            self.logging.log("已执行缩放操作", self.name, logging.DEBUG)
        except Exception as e:
            self.logging.log(f"执行缩放操作时出错: {str(e)}", self.name, logging.ERROR)
            raise

    def get_screencap(self):
        start_time = time.time()
        max_retries = 3
        for attempt in range(max_retries):
            try:
                tool_class = self.CAP_TOOLS.get(self.conf.cap_tool)
                if not tool_class:
                    raise TypeError("未知的截图工具")
                if tool_class.__name__ == 'MuMuCap':
                    controller = tool_class(instance_index=self.module.simulator_index)
                else:
                    controller = tool_class(serial=f'127.0.0.1:{self.port}')
                screencap = self.__perform_screencap(controller)
                self.logging.log(f"{self.conf.cap_tool} 截图成功,耗时 {time.time() - start_time:.2f}s", self.name, logging.DEBUG)
                return screencap
            except Exception as e:
                self.logging.log(f"{self.conf.cap_tool} 截图失败, 重试次数 {attempt + 1}: {str(e)}", self.name, logging.ERROR)
                if attempt < max_retries:
                    continue
                else:
                    self.logging.log(f"{self.conf.cap_tool} 截图失败: {str(e)}", self.name, logging.ERROR)
                    raise e

    def click(self, coordinate):
        x, y = coordinate
        try:
            tool_class = self.TOUCH_TOOLS.get(self.conf.touch_tool)
            if not tool_class:
                raise ValueError("未知的点击工具")
            if tool_class.__name__ == 'MuMuTouch':
                controller = tool_class(instance_index=self.module.simulator_index)
            else:
                controller = tool_class(serial=f'127.0.0.1:{self.port}')
            self.__perform_click(controller, x, y)
        except Exception as e:
            self.logging.log(f"点击坐标时出错: {str(e)}", self.name, logging.ERROR)
            raise

    async def start_simulator(self):
        try:
            if self.conf.simulator_path:
                subprocess.Popen([self.conf.simulator_path, "-v", str(self.module.simulator_index)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 encoding="utf-8",
                                 shell=False)
                self.logging.log("启动模拟器成功", self.name, logging.INFO)
            else:
                self.logging.log("模拟器路径未设置", self.name, logging.ERROR)
                raise Exception("模拟器路径未设置")
        except Exception as e:
            self.logging.log(f"启动模拟器失败: {str(e)}", self.name, logging.ERROR)
            raise

    async def check_running_status(self):
        """检查应用是否正在运行"""
        try:
            output = self.adb.shell("ps")
            if "com.stone3.ig" in output:
                self.logging.log("应用正在运行", self.name, logging.INFO)
                output = self.adb.shell("dumpsys window | grep mFocusedWindow")
                if "com.stone3.ig" in output:
                    self.logging.log("应用在前台运行", self.name, logging.INFO)
                    return True
                else:
                    self.logging.log("应用未在前台运行,尝试重新打开应用", self.name, logging.INFO)
                    self.close_app()
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

    def close_app(self):
        try:
            self.adb.shell("am force-stop com.stone3.ig")
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
