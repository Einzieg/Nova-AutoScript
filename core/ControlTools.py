import asyncio
import logging
import random

import cv2

from core.LogManager import LogManager
from models.Template import Template


class ControlTools:
    def __init__(self, target, device):
        self.target = target
        self.device = device
        self.offset = 3
        self.confidence = 0.8
        self.logging = LogManager()

        self.forbidden_zones = [
            (0, 0, 500, 260),  # 左上角人物
            (490, 0, 680, 130),  # 3D
            (800, 0, 1920, 100),  # 上方资源栏
            (910, 0, 1920, 250),  # 右上角活动
            (1700, 270, 1920, 400),  # 极乐入口
            (0, 950, 1300, 1080),  # 下方聊天栏
            (1350, 870, 1920, 1080),  # 星云按钮
            (1680, 250, 1920, 750)  # 右侧活动及快捷菜单
        ]

    async def matching(self, template: Template, click=False, sleep=0):
        image = self.device.get_screencap()
        template = template.cv_tmp

        if template.forbidden:
            for zone in self.forbidden_zones:
                left, top, right, bottom = zone
                width = right - left
                height = bottom - top
                image[top:top + height, left:left + width] = 0
        try:
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= template.threshold:
                icon_w, icon_h = template.shape[1], template.shape[0]
                icon_center_x = max_loc[0] + icon_w // 2
                icon_center_y = max_loc[1] + icon_h // 2
                random_offset_x = random.randint(-self.offset, self.offset)
                random_offset_y = random.randint(-self.offset, self.offset)
                coordinate = icon_center_x + random_offset_x, icon_center_y + random_offset_y
                self.logging.log(f"{template.name} 匹配成功，坐标 [{coordinate}]", self.target)
                if click:
                    self.device.click(coordinate)
                return coordinate
            else:
                self.logging.log(f"{template.name} 未匹配，置信度 {max_val}", self.target, logging.DEBUG)
                return None
        except Exception as e:
            self.logging.log(f"{template.name} 匹配失败: {e}", self.target, logging.ERROR)
            return None
        finally:
            if sleep > 0:
                await asyncio.sleep(sleep)

    async def wait_element_appear(self, template: Template, click=False, time_out=60):
        times = 0
        while times < time_out:
            coordinate = await self.matching(template, click=False, sleep=1)
            if coordinate:
                if click:
                    self.device.click(coordinate)
                return True
            times += 1
        return False

    async def wait_element_disappear(self, template: Template, time_out=60):
        times = 0
        while times < time_out:
            if not await self.matching(template, click=False, sleep=1):
                return True
            times += 1
        return False
