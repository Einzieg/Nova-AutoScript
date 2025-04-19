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

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DeviceUtilsB, cls).__new__(cls)
        return cls._instance

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
            self._log(f"计算端口号为 {self.port}", logging.DEBUG)
        else:
            self.port = self.module.simulator_index

        self.adb = AdbClient(self.name, port=self.port)
        self.push_scripts()

    @staticmethod
    def __perform_screencap(controller: ScreenCap):
        return controller.screencap()

    @staticmethod
    def __perform_click(controller: Touch, x, y):
        controller.click(x, y)

    def push_scripts(self):
        """推送脚本文件到设备"""
        try:
            self.adb.push(Path(__file__).resolve().parent / "static/zoom_out.sh", "/sdcard/zoom_out.sh")
            self._log("脚本文件推送成功", logging.DEBUG)
        except Exception as e:
            self._log(f"推送脚本文件时出错: {str(e)}", logging.ERROR)
            raise

    def click_back(self):
        """模拟点击返回键"""
        try:
            self.adb.shell("input keyevent 4")
            self._log("已点击返回键", logging.DEBUG)
        except Exception as e:
            self._log(f"点击返回键时出错: {str(e)}", logging.ERROR)
            raise

    def zoom_out(self):
        """执行缩放操作"""
        try:
            self.adb.shell("sh /sdcard/zoom_out.sh")
            self._log("已执行缩放操作", logging.DEBUG)
        except Exception as e:
            self._log(f"执行缩放操作时出错: {str(e)}", logging.ERROR)
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
                self._log(f"截图成功,耗时 {time.time() - start_time:.2f}s", logging.DEBUG)
                return self.__perform_screencap(controller)
            except Exception as e:
                self._log(f"截图失败, 重试次数 {attempt + 1}: {str(e)}", logging.ERROR)
                if attempt < max_retries:
                    continue
                else:
                    self._log(f"截图失败: {str(e)}", logging.ERROR)
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
            self._log(f"点击坐标时出错: {str(e)}", logging.ERROR)
            raise

    def start_simulator(self):
        try:
            if self.conf.simulator_path:
                subprocess.Popen([self.conf.simulator_path, "-v", str(self.module.simulator_index)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 encoding="utf-8",
                                 shell=False)
                self._log("启动模拟器成功", logging.INFO)
            else:
                self._log("模拟器路径未设置", logging.ERROR)
                raise Exception("模拟器路径未设置")
        except Exception as e:
            self._log(f"启动模拟器失败: {str(e)}", logging.ERROR)
            raise

    async def check_running_status(self):
        """检查应用是否正在运行"""
        try:
            output = self.adb.shell("ps")
            if "com.stone3.ig" in output:
                self._log("应用正在运行", logging.INFO)
                output = self.adb.shell("dumpsys window | grep mFocusedWindow")
                if "com.stone3.ig" in output:
                    self._log("应用在前台运行", logging.INFO)
                    return True
                else:
                    self._log("应用未在前台运行,尝试重新打开应用", logging.INFO)
                    self.close_app()
                    await asyncio.sleep(3)
                    self.launch_app()
            else:
                self.launch_app()
        except Exception as e:
            self._log(f"检查应用运行状态时出错: {str(e)}", logging.ERROR)
            raise

    def launch_app(self):
        try:
            self.adb.shell("am start -n com.stone3.ig/com.google.firebase.MessagingUnityPlayerActivity")
            self._log("已启动应用", logging.INFO)
        except Exception as e:
            self._log(f"启动应用时出错: {str(e)}", logging.ERROR)
            raise

    def close_app(self):
        try:
            self.adb.shell("am force-stop com.stone3.ig")
            self._log("已关闭应用", logging.DEBUG)
        except Exception as e:
            self._log(f"关闭应用时出错: {str(e)}", logging.ERROR)
            raise

    def check_wm_size(self):
        # 优化屏幕尺寸解析逻辑
        try:
            output = self.adb.shell("wm size").strip()
            if output.startswith("Physical size:"):
                parts = output.split()
                if len(parts) >= 3:
                    width, height = map(int, parts[2].split('x'))
                    self._log(f"获取屏幕尺寸为 {width}x{height}", logging.DEBUG)
                    return width, height
            self._log("未找到屏幕尺寸信息", logging.DEBUG)
            return None, None
        except Exception as e:
            self._log(f"获取屏幕尺寸时出错: {str(e)}", logging.ERROR)

    # 新增日志封装方法（减少重复代码）
    def _log(self, message, level=logging.INFO):
        self.logging.log(message, self.name, level)
