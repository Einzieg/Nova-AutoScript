import base64
import hashlib
import json
import os
import time
import uuid

import cv2
import requests
from tencentcloud.common import credential
from tencentcloud.ocr.v20181119 import ocr_client, models

from aip import AipOcr
from msc.screencap import ScreenCap
from msc.mumu import MuMuCap

from device_operation.Settings import Settings

settings = Settings()


class OcrTools:

    def __init__(self):
        pass

    @staticmethod
    def mat2base64(image):
        if image is None:
            return None
        return base64.b64encode(cv2.imencode('.png', image)[1]).decode()

    def tencent_ocr(self, image: cv2.Mat):
        image = self.mat2base64(image)
        if image is None:
            return None

        cred = credential.Credential(settings.TENCENT_SECRET_ID, settings.TENCENT_SECRET_KEY)
        client = ocr_client.OcrClient(cred, "ap-guangzhou")
        req = models.GeneralAccurateOCRRequest()
        req.ImageBase64 = image
        try:
            resp = client.GeneralAccurateOCR(req)
        except Exception as e:
            print(f"OCR 错误: {e}")
            return None
        resp_json = json.loads(resp.to_json_string())
        text_detections = resp_json.get("TextDetections", [])
        detections = [text_detection.get("DetectedText") for text_detection in text_detections]

        return detections

    def baidu_ocr(self, image: cv2.Mat):
        image = self.mat2base64(image)
        if image is None:
            return None

        client = AipOcr(settings.BAIDU_APP_ID, settings.BAIDU_API_KEY, settings.BAIDU_SECRET_KEY)
        img_bytes = base64.b64decode(image.encode('utf-8'))
        result = client.basicGeneral(img_bytes)

        return result

    def youdao_ocr(self, image: cv2.Mat):
        image_base64 = self.mat2base64(image)
        if image_base64 is None:
            return None

        app_key = settings.YOUDAO_APP_ID
        app_secret = settings.YOUDAO_APP_SECRET
        size = len(image_base64)
        truncated_image = image_base64 if size <= 20 else image_base64[0:10] + str(size) + image_base64[size - 10:size]

        data = {
            'detectType': '10012',  # 文字识别
            'imageType': '1',  # 原始图片base64编码
            'langType': 'zh-CHS',  # 中文识别
            'img': image_base64,  # 图片base64数据
            'docType': 'json',  # 返回数据格式
            'signType': 'v3'  # 签名版本
        }

        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())

        sign_str = app_key + truncated_image + salt + curtime + app_secret
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(sign_str.encode('utf-8'))
        sign = hash_algorithm.hexdigest()

        data['appKey'] = app_key
        data['salt'] = salt
        data['sign'] = sign

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post('https://openapi.youdao.com/ocrapi', data=data, headers=headers)
        if response.json()['errorCode'] != '0':
            return None
        return response.json()


def perform_screencap(controller: ScreenCap):
    return controller.screencap()


def crop_screencap(controller: ScreenCap, x1: int, y1: int, x2: int, y2: int):
    try:
        image = controller.screencap()
    except Exception as e:
        print(f"OCR 错误: {e}")
        return None
    x_start, x_end = min(x1, x2), max(x1, x2)
    y_start, y_end = min(y1, y2), max(y1, y2)
    cropped_img = image[y_start:y_end, x_start:x_end]
    return cropped_img


# img = crop_screencap(MuMuCap(0), 1630, 140, 1780, 175)
img = crop_screencap(MuMuCap(0), 1165, 90, 1870, 990)
# img = perform_screencap(MuMuCap(0))
# print(OcrTools().tencent_ocr(img))
print(OcrTools().baidu_ocr(img))
