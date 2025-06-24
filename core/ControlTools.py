import asyncio
import logging
import random
import time

import cv2
import numpy as np

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

    async def matching_one(self, template: Template, click=False, sleep=0.3):
        image = self.device.get_screencap()
        cv_tmp = template.cv_tmp

        if template.forbidden:
            for zone in self.forbidden_zones:
                left, top, right, bottom = zone
                width = right - left
                height = bottom - top
                image[top:top + height, left:left + width] = 0
        try:
            result = cv2.matchTemplate(image, cv_tmp, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= template.threshold:
                icon_w, icon_h = cv_tmp.shape[1], cv_tmp.shape[0]
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
                self.logging.log(f"{template.name} 未匹配，置信度 {max_val:.2%}", self.target, logging.DEBUG)
                return None
        except Exception as e:
            self.logging.log(f"{template.name} 匹配失败: {e}", self.target, logging.ERROR)
            return None
        finally:
            if sleep is not None and sleep > 0:
                await asyncio.sleep(sleep)

    async def matching_all(self, template: Template):
        image = self.device.get_screencap()
        cv_tmp = template.cv_tmp
        if template.forbidden:
            for zone in self.forbidden_zones:
                left, top, right, bottom = zone
                width = right - left
                height = bottom - top
                image[top:top + height, left:left + width] = 0
        try:
            result = cv2.matchTemplate(image, cv_tmp, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= template.threshold)
            boxes = []
            for pt in zip(*locations[::-1]):
                boxes.append([pt[0], pt[1], cv_tmp.shape[1], cv_tmp.shape[0]])
            boxes = np.array(boxes)
            filtered_boxes = self.__non_max_suppression(boxes, overlap_thresh=0.5)
            if filtered_boxes:
                coordinates = []
                for box in filtered_boxes:
                    x, y, w, h = box
                    coordinates.append([x + w // 2, y + h // 2])
                return coordinates
            return None
        except Exception as e:
            self.logging.log(f"{template.name} 匹配失败: {e}", self.target, logging.ERROR)
            return None

    async def move_coordinates(self, template: Template):
        """
        获取筛选后的坐标组
        :param template:
        :return:
        """
        results = await self.matching_all(template)
        if not results:
            return
        start_index = 0
        while start_index < len(results) and self.__is_within_no_click_zone(results[start_index][0], results[start_index][1]):
            start_index += 1
        if start_index >= len(results):
            return False
        new_coordinates = [results[start_index]]
        offset = [960 - results[start_index][0], 540 - results[start_index][1]]
        for res in range(start_index + 1, len(results)):
            new_x = results[res][0] + offset[0]
            new_y = results[res][1] + offset[1]
            if (0 <= new_x <= 1920 and 0 <= new_y <= 1080) and not self.__is_within_no_click_zone(new_x, new_y):
                offset = [960 - results[res][0], 540 - results[res][1]]
                new_coordinates.append([new_x, new_y])
        return new_coordinates

    async def await_element_appear(self, template: Template, click=False, time_out=60, sleep=0.3):
        start_time = time.time()
        while time.time() - start_time < time_out:
            coordinate = await self.matching_one(template, click=click, sleep=sleep)
            if coordinate:
                return True
        return False

    async def await_element_disappear(self, template: Template, time_out=60):
        start_time = time.time()
        while time.time() - start_time < time_out:
            if not await self.matching_one(template, click=False, sleep=1):
                return True
        return False

    @staticmethod
    def __non_max_suppression(boxes, overlap_thresh=0.5):
        """
        非极大值抑制，用于去除重叠的边界框。
        :param boxes: 边界框列表，格式为 [x, y, w, h]
        :param overlap_thresh: 重叠阈值，范围为 0 到 1
        :return: 过滤后的边界框列表
        """
        if len(boxes) == 0:
            return []

        x1 = boxes[:, 0]  # 左上角 x
        y1 = boxes[:, 1]  # 左上角 y
        x2 = boxes[:, 0] + boxes[:, 2]  # 右下角 x
        y2 = boxes[:, 1] + boxes[:, 3]  # 右下角 y

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)

        indices = np.argsort(y2)

        keep = []
        while len(indices) > 0:
            last = len(indices) - 1
            i = indices[last]
            keep.append(i)

            w = np.maximum(0, np.minimum(x2[i], x2[indices[:last]]) - np.maximum(x1[i], x1[indices[:last]]) + 1)
            h = np.maximum(0, np.minimum(y2[i], y2[indices[:last]]) - np.maximum(y1[i], y1[indices[:last]]) + 1)

            overlaps = w * h

            indices = indices[np.where((overlaps / (areas[i] + areas[indices[:last]] - overlaps)) <= overlap_thresh)[0]]

        return [boxes[i] for i in keep]

    def __is_within_no_click_zone(self, x, y):
        for (x1, y1, x2, y2) in self.forbidden_zones:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False
