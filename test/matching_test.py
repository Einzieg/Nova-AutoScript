import cv2

import cv2
import numpy as np
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


def perform_screencap(controller: ScreenCap):
    return controller.screencap()


def perform_click(controller: Touch, x, y):
    controller.click(x, y)


def matching_one():
    img = perform_screencap(MuMuCap(3))
    # temp = cv2.imread(r"../static/novaimgs/button/btn_close.png")
    temp = cv2.imread("screencap2.png")

    result = cv2.matchTemplate(img, temp, cv2.TM_CCOEFF_NORMED)
    # 获取到小图的尺寸
    icon_w, icon_h = temp.shape[1], temp.shape[0]
    # 返回匹配的最小坐标
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(max_val)

    if max_val > 0.75:
        top_left = max_loc
        bottom_right = (top_left[0] + icon_w, top_left[1] + icon_h)
        cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
        cv2.imshow('result', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("匹配失败")


def non_max_suppression(boxes, overlap_thresh=0.5):
    """
    非极大值抑制，用于去除重叠的边界框。
    :param boxes: 边界框列表，格式为 [x, y, w, h]
    :param overlap_thresh: 重叠阈值，范围为 0 到 1
    :return: 过滤后的边界框列表
    """
    if len(boxes) == 0:
        return []

    # 提取边界框的坐标
    x1 = boxes[:, 0]  # 左上角 x
    y1 = boxes[:, 1]  # 左上角 y
    x2 = boxes[:, 0] + boxes[:, 2]  # 右下角 x
    y2 = boxes[:, 1] + boxes[:, 3]  # 右下角 y

    # 计算每个框的面积
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)

    # 按右下角 y 坐标排序
    indices = np.argsort(y2)

    keep = []  # 保留的框索引
    while len(indices) > 0:
        last = len(indices) - 1
        i = indices[last]
        keep.append(i)

        # 计算当前框与其他框的交集区域
        xx1 = np.maximum(x1[i], x1[indices[:last]])
        yy1 = np.maximum(y1[i], y1[indices[:last]])
        xx2 = np.minimum(x2[i], x2[indices[:last]])
        yy2 = np.minimum(y2[i], y2[indices[:last]])

        # 计算交集宽度和高度
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # 计算交集面积
        overlaps = w * h

        # 计算交并比（IoU）
        ious = overlaps / (areas[i] + areas[indices[:last]] - overlaps)

        # 保留 IoU 小于阈值的框
        indices = indices[np.where(ious <= overlap_thresh)[0]]

    return [boxes[i] for i in keep]


def matching_more():
    img = perform_screencap(MuMuCap(0))
    temp = cv2.imread("screencap.png")
    result = cv2.matchTemplate(img, temp, cv2.TM_CCOEFF_NORMED)
    threshold = 0.75
    locations = np.where(result >= threshold)
    boxes = []
    for pt in zip(*locations[::-1]):
        boxes.append([pt[0], pt[1], temp.shape[1], temp.shape[0]])
        # cv2.rectangle(img, pt, (pt[0] + temp.shape[1], pt[1] + temp.shape[0]), (0, 0, 255), 2)

    # 应用非极大值抑制
    boxes = np.array(boxes)
    filtered_boxes = non_max_suppression(boxes, overlap_thresh=0.5)

    # 绘制过滤后的框
    for box in filtered_boxes:
        x, y, w, h = box
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    print(filtered_boxes)
    cv2.imshow('result', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


matching_one()
# matching_more()
