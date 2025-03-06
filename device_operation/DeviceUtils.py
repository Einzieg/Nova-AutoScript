import logging
import time

import cv2
from msc.minicap import MiniCap
from msc.mumu import MuMuScreenCap, get_mumu_path
from mtc.mumu import MuMuTouch

from AdbClient import AdbClient
from path_util import resource_path


class DeviceUtils:
    def __init__(self, ip="127.0.0.1", port=5555, instance_index=None, mumu_path=None):
        """
        初始化DeviceUtils实例。
        :param ip: 设备IP地址，默认为"127.0.0.1"。
        :param port: 设备端口号，默认为5555。
        :param instance_index: 实例索引，用于计算多开设备的端口号，默认为None。
        """
        self.ip = ip
        self.port = port
        self.instance_index = instance_index
        self.mumu_path = mumu_path

        if instance_index is not None:
            self.port = 16384 + 32 * instance_index
            logging.info(f"计算端口号为 {self.port}")

        self.adb = AdbClient(ip=self.ip, port=self.port)

        # 初始化截图工具
        self.screencap_tool = self._initialize_screencap()

        # 初始化点击工具
        self.click_tool = self._initialize_click_tool()

    def _initialize_screencap(self):
        """根据优先顺序初始化截图工具"""
        try:
            # 尝试使用MuMu进行截图
            if get_mumu_path():
                self.mumu_path = get_mumu_path()  # 获取MuMu路径
                mumu_screencap = MuMuScreenCap(self.instance_index, emulator_install_path=self.mumu_path)
                logging.info("使用MuMu进行屏幕截图")
                return mumu_screencap
            else:
                raise Exception("MuMu路径未找到")

        except Exception as e:
            logging.error(f"MuMu初始化失败: {str(e)}")
            try:
                # 如果MuMu失败，尝试使用Minicap
                minicap = MiniCap(f"{self.ip}:{self.port}")
                logging.info("使用Minicap进行屏幕截图")
                return minicap
            except Exception as e:
                logging.error(f"Minicap初始化失败: {str(e)}")
                # 如果Minicap也失败，则使用ADB进行截图
                logging.info("使用ADB进行屏幕截图")
                return self.adb

    def _initialize_click_tool(self):
        """初始化点击工具"""
        try:
            # 尝试使用MuMu进行点击
            if get_mumu_path():
                self.mumu_path = get_mumu_path()  # 获取MuMu路径
                mumu_touch = MuMuTouch(self.instance_index, emulator_install_path=self.mumu_path)
                logging.info("使用MuMu进行点击操作")
                return mumu_touch
            else:
                raise Exception("MuMu路径未找到")

        except Exception as e:
            logging.error(f"MuMu点击初始化失败: {str(e)}")
            try:
                # 如果MuMu失败，尝试使用ADB进行点击
                logging.info("使用ADB进行点击操作")
                return self.adb
            except Exception as e:
                logging.error(f"ADB点击初始化失败: {str(e)}")
                raise

    def adb_shell(self, command):
        """执行ADB shell命令"""
        try:
            return self.adb.shell(command)
        except Exception as e:
            logging.error(f"执行命令 {command} 时出错: {str(e)}")
            raise

    def push_scripts(self):
        """推送脚本文件到设备"""
        try:
            self.adb.push(resource_path("static/zoom_in.sh"), "/sdcard/zoom_in.sh")
            self.adb.push(resource_path("static/zoom_out.sh"), "/sdcard/zoom_out.sh")
            logging.debug("脚本文件推送成功")
        except Exception as e:
            logging.error(f"推送脚本文件时出错: {str(e)}")
            raise

    def click_back(self):
        """模拟点击返回键"""
        try:
            self.adb.shell("input keyevent 4")
            logging.debug("已点击返回键")
        except Exception as e:
            logging.error(f"点击返回键时出错: {str(e)}")
            raise

    def zoom_out(self):
        """执行缩放操作"""
        try:
            self.adb.shell("sh /sdcard/zoom_out.sh")
            logging.debug("已执行缩放操作")
        except Exception as e:
            logging.error(f"执行缩放操作时出错: {str(e)}")
            raise

    def screencap(self, file_name: str = "screenshot.png"):
        """
        使用已经初始化的截图工具进行屏幕截图。
        :param file_name: 保存的文件名，默认为"screenshot.png"
        """
        start_time = time.time()
        try:
            if isinstance(self.screencap_tool, MuMuScreenCap):
                self.screencap_tool.save_screencap(file_name)
                logging.debug(f"使用MuMu屏幕截图，保存为 {file_name} ,耗时 {time.time() - start_time:.2f}s")
            elif isinstance(self.screencap_tool, MiniCap):
                self.screencap_tool.save_screencap(file_name)
                logging.debug(f"使用Minicap屏幕截图，保存为 {file_name} ,耗时 {time.time() - start_time:.2f}s")
            else:
                self.screencap_tool.shell(f"screencap -p /sdcard/{file_name}")
                self.screencap_tool.pull(f"/sdcard/{file_name}", file_name)
                logging.debug(f"使用ADB屏幕截图，保存为 {file_name} ,耗时 {time.time() - start_time:.2f}s")
        except Exception as e:
            logging.error(f"截图时出错: {str(e)}")
            raise
        return cv2.imread(file_name)

    def click(self, coordinate):
        """使用已经初始化的点击工具进行点击操作"""
        x, y = coordinate
        try:
            if isinstance(self.click_tool, MuMuTouch):
                self.click_tool.click(x, y)
                logging.debug(f"MuMu点击坐标 ({x}, {y})")
            else:
                self.click_tool.shell(f"input tap {x} {y}")
                logging.debug(f"ADB点击坐标 ({x}, {y})")
        except Exception as e:
            logging.error(f"点击坐标 ({x}, {y}) 时出错: {str(e)}")
            raise
