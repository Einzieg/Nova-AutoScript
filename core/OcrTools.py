import base64
import hashlib
import json
import logging
import time
import uuid

import cv2
import requests
from aip import AipOcr
from tencentcloud.common import credential
from tencentcloud.ocr.v20181119 import ocr_client, models

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

        resp = client.GeneralAccurateOCR(req)

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
            'imageType': '1',       # 原始图片base64编码
            'langType': 'zh-CHS',   # 中文识别
            'img': image_base64,    # 图片base64数据
            'docType': 'json',      # 返回数据格式
            'signType': 'v3'        # 签名版本
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
            logging.error(f"OCR 错误: {response.json()['errorCode']}")
            return None
        return response.json()


