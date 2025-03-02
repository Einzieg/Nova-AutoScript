import cv2
import numpy as np


def non_max_suppression(boxes, scores, overlap_thresh=0.3):
    if len(boxes) == 0:
        return []

    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float32")

    idx_ls = np.argsort(scores)[::-1]

    pick = []

    while len(idx_ls) > 0:
        i = idx_ls[0]
        pick.append(i)

        suppress = [i]
        for pos in range(1, len(idx_ls)):
            j = idx_ls[pos]
            xx1 = max(boxes[i][0], boxes[j][0])
            yy1 = max(boxes[i][1], boxes[j][1])
            xx2 = min(boxes[i][0] + boxes[i][2], boxes[j][0] + boxes[j][2])
            yy2 = min(boxes[i][1] + boxes[i][3], boxes[j][1] + boxes[j][3])

            w = max(0, xx2 - xx1)
            h = max(0, yy2 - yy1)
            inter_area = w * h

            box_area = (boxes[i][2] * boxes[i][3])
            box_area2 = (boxes[j][2] * boxes[j][3])

            # 计算重叠比率
            overlap = inter_area / float(box_area + box_area2 - inter_area)

            # 如果重叠度大于阈值, 进行抑制
            if overlap > 0.3:
                suppress.append(j)

        # 删除已经抑制的框 移除 suppress 中的索引
        idx_ls = [idx for idx in idx_ls if idx not in suppress]

    return pick


def get_coordinate(template):
    # original = cv2.imread("screenshot.png")

    img = cv2.imread("screenshot.png")
    h, w = template.shape[:2]
    ret = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    # 筛选出匹配程度大于 believe 的坐标
    threshold = 0.75
    locations = np.where(ret >= threshold)
    boxes = []

    # 记录每个坐标的位置和分数
    for pt in zip(*locations[::-1]):
        boxes.append([pt[0], pt[1], w, h])

    results = []

    # 使用 NMS 进行重叠去除
    if len(boxes) > 0:
        boxes = np.array(boxes)
        scores = ret[locations]
        picks = non_max_suppression(boxes, scores)

        for pick in picks:
            pt = boxes[pick]
            results.append([pt[0], pt[1]])
    # =============== DEBUG ==============
    #         cv2.rectangle(original, (pt[0], pt[1]), (pt[0] + pt[2], pt[1] + pt[3]), (0, 0, 255), 1)
    # print(results)
    # # 显示结果图像
    # cv2.imshow('rect', original)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # ====================================
    return results


def is_within_no_click_zone(x, y, no_click):
    for (x1, y1, x2, y2) in no_click:
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False


def move_coordinates(template, no_click):
    results = get_coordinate(template)
    if not results:
        return

    # 找到第一个不在禁用区的坐标
    start_index = 0
    while start_index < len(results) and is_within_no_click_zone(results[start_index][0], results[start_index][1], no_click):
        start_index += 1

    # 如果没有找到不在禁用区的坐标，返回 False
    if start_index >= len(results):
        return False

    # 从第一个不在禁用区的坐标开始
    new_coordinates = [results[start_index]]
    target = [960, 540]
    # 计算第一个坐标移动到目标点的偏移
    offset = [target[0] - results[start_index][0], target[1] - results[start_index][1]]

    for res in range(start_index + 1, len(results)):
        new_x = results[res][0] + offset[0]
        new_y = results[res][1] + offset[1]

        # 确保新坐标在屏幕范围内并且不在禁止点击区域内
        if (0 <= new_x <= 1920 and 0 <= new_y <= 1080) and not is_within_no_click_zone(new_x, new_y, no_click):
            new_coordinates.append([new_x, new_y])
            # 更新偏移量
            offset = [target[0] - results[res][0], target[1] - results[res][1]]

    return new_coordinates

