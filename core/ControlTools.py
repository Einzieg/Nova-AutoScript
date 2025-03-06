import logging
import random
import time

import cv2


class ControlTools:
    def __init__(self, target, device):
        self.target = target
        self.device = device
        self.offset = 3
        self.confidence = 0.8

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

    def matching(self, template, click=False, forbidden=False):
        image = self.device.screencap(self.target)

        if forbidden:
            for zone in self.forbidden_zones:
                left, top, right, bottom = zone
                width = right - left
                height = bottom - top
                image[top:top + height, left:left + width] = 0

        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.confidence:
            icon_w, icon_h = template.shape[1], template.shape[0]
            icon_center_x = max_loc[0] + icon_w // 2
            icon_center_y = max_loc[1] + icon_h // 2
            random_offset_x = random.randint(-self.offset, self.offset)
            random_offset_y = random.randint(-self.offset, self.offset)
            coordinate = icon_center_x + random_offset_x , icon_center_y + random_offset_y
            logging.debug(f"匹配成功，坐标 [{coordinate}]")
            if click:
                self.device.click(coordinate)
            return coordinate
        return None

    def wait_element_appear(self, template, time_out=60):
        times = 0
        while times < time_out:
            if self.matching(template, click=False):
                return True
            time.sleep(1)
            times += 1
        return False

    def wait_element_disappear(self, template, time_out=60):
        times = 0
        while times < time_out:
            if not self.matching(template, click=False):
                return True
            time.sleep(1)
            times += 1
        return False

