import asyncio
import base64
import hashlib
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Callable

import cv2
import requests
from aip import AipOcr
from tencentcloud.common import credential
from tencentcloud.ocr.v20181119 import ocr_client, models

from device_operation.Settings import Settings

settings = Settings()

Box = Tuple[int, int, int, int]

OcrResult = Dict[str, Any]

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("tencentcloud_sdk_common").setLevel(logging.WARNING)


class OcrTools:
    """
    Simple OCR tools wrapper with unified parsers for Baidu, Tencent and Youdao.

    Each public OCR method returns a dict:
      { 'success': bool, 'texts': List[str] or List[{'text', 'box'}], 'raw': Any, 'error': Optional[str] }
    """

    def __init__(self, setting: Settings = settings):
        self.settings = setting
        self._baidu_client = AipOcr(
            setting.BAIDU_APP_ID,
            setting.BAIDU_API_KEY,
            setting.BAIDU_SECRET_KEY
        )

    # --- 静态辅助方法 ---

    @staticmethod
    def _make_result(success: bool, texts: Optional[List[Any]] = None, raw: Optional[Any] = None, error: Optional[str] = None) -> OcrResult:
        return {'success': bool(success), 'texts': texts or [], 'raw': raw, 'error': error}

    @staticmethod
    def mat2base64(image: Optional[cv2.Mat]) -> Optional[str]:
        if image is None:
            return None
        return base64.b64encode(cv2.imencode('.png', image)[1]).decode('utf-8')

    @staticmethod
    def _box_from_polygon_points(points: List[Dict[str, Any]]) -> Optional[Box]:
        """Convert list of point dicts [{'X':.,'Y':.}, ...] to (l,t,r,b)."""
        if not points:
            return None
        xs = []
        ys = []
        try:
            for p in points:
                # 统一 key 访问逻辑
                x = p.get('X', p.get('x'))
                y = p.get('Y', p.get('y'))
                if x is None or y is None:
                    return None
                xs.append(int(float(x)))
                ys.append(int(float(y)))
            return min(xs), min(ys), max(xs), max(ys)
        except Exception:
            logging.warning("解析多边形点到框时出错.", exc_info=True)
            return None

    @staticmethod
    def _box_from_itempolygon(item: Dict[str, Any]) -> Optional[Box]:
        """Convert ItemPolygon like {X, Y, Width, Height} to (l,t,r,b)."""
        if not isinstance(item, dict):
            return None
        try:
            # 统一 key 访问逻辑
            x = item.get('X') or item.get('x')
            y = item.get('Y') or item.get('y')
            w = item.get('Width') or item.get('width')
            h = item.get('Height') or item.get('height')
            if x is None or y is None or w is None or h is None:
                return None
            l = int(float(x))
            t = int(float(y))
            r = l + int(float(w))
            b = t + int(float(h))
            return l, t, r, b
        except Exception:
            logging.warning("将项多边形解析到框时出错.", exc_info=True)
            return None

    @staticmethod
    def _box_from_boundingbox_str(s: str) -> Optional[Box]:
        """Convert youdao boundingBox string 'x1,y1,x2,y2,...' to (l,t,r,b)."""
        if not isinstance(s, str):
            return None
        parts = [p.strip() for p in s.split(',') if p.strip()]
        if len(parts) < 4:
            return None
        try:
            nums = [int(float(x)) for x in parts]
            # 使用切片简化 x, y 分离
            xs = nums[0::2]
            ys = nums[1::2]
            return min(xs), min(ys), max(xs), max(ys)
        except Exception:
            logging.warning("解析边界框字符串时出错.", exc_info=True)
            return None

    @staticmethod
    def _generate_youdao_sign(app_key: str, app_secret: str, image_b64: str) -> Tuple[str, str, str]:
        """将 Youdao 的签名生成逻辑独立出来。"""
        size = len(image_b64)
        # Youdao 要求的截断逻辑，保持不变
        truncated_image = image_b64 if size <= 20 else image_b64[0:10] + str(size) + image_b64[size - 10:size]
        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        sign_str = app_key + truncated_image + salt + curtime + app_secret

        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(sign_str.encode('utf-8'))
        sign = hash_algorithm.hexdigest()

        return sign, curtime, salt

    # --- 统一的结果解析器 ---

    @staticmethod
    def parse_baidu_resp(resp: Dict[str, Any], include_location: bool = False):
        if not isinstance(resp, dict):
            return []
        out = []
        for w in resp.get('words_result', []) or []:
            text = w.get('words') if isinstance(w, dict) else str(w)
            if include_location:
                out.append({'text': text, 'box': None})
            else:
                out.append(text)
        return out

    @staticmethod
    def parse_tencent_resp(resp: Dict[str, Any], include_location: bool = False):
        if not isinstance(resp, dict):
            return []
        out = []
        for d in resp.get('TextDetections', []) or []:
            text = d.get('DetectedText')
            box = None
            if include_location:
                box = OcrTools._box_from_itempolygon(d.get('ItemPolygon') or {})
                if not box:
                    poly = d.get('Polygon') or d.get('polygon')
                    if isinstance(poly, list):
                        box = OcrTools._box_from_polygon_points(poly)
            if include_location:
                out.append({'text': text, 'box': box})
            else:
                out.append(text)
        return out

    @staticmethod
    def parse_youdao_resp(resp: Dict[str, Any], include_location: bool = False):
        if not isinstance(resp, dict): return []
        out = []
        result = resp.get('Result') or resp.get('result')
        if not isinstance(result, dict): return out
        regions = result.get('regions', []) or []
        for region in regions:
            lines = region.get('lines', []) or []
            for line in lines:
                text = line.get('text') or line.get('Text')
                box = None
                if include_location:
                    box = OcrTools._box_from_boundingbox_str(line.get('boundingBox') or region.get('boundingBox') or '')
                    out.append({'text': text, 'box': box})
                else:
                    out.append(text)
        return out

    @staticmethod
    def parse_zhyunxi_resp(resp: Dict[str, Any], include_location: bool = False):
        if not isinstance(resp, dict):
            return []
        out: List[Any] = []
        records = resp.get('data') or resp.get('Data') or []
        if not isinstance(records, list):
            return out
        for row in records:
            if not isinstance(row, dict):
                continue
            text_value = row.get('text')
            text = str(text_value) if text_value is not None else ''
            if include_location:
                points = []
                for idx in range(1, 5):
                    x = row.get(f'x{idx}')
                    y = row.get(f'y{idx}')
                    if x is None or y is None:
                        continue
                    points.append({'x': x, 'y': y})
                box = OcrTools._box_from_polygon_points(points)
                out.append({'text': text, 'box': box})
            else:
                out.append(text)
        return out

    # --- 核心同步方法包装器 ---

    def _ocr_api_wrapper(self, ocr_func: Callable[..., OcrResult], image: cv2.Mat, include_location: bool) -> OcrResult:
        """
        统一处理 OCR 调用的前置条件（Base64 编码、空图检查）和异常捕获。
        :param ocr_func: 实际执行 API 调用的方法（如 self._tencent_ocr_impl）
        """
        image_b64 = self.mat2base64(image)
        if image_b64 is None:
            return self._make_result(False, error='empty_image')

        func_name = ocr_func.__name__
        try:
            return ocr_func(image_b64, include_location)
        except Exception as e:
            logging.exception(f'OCR provider "{func_name}" failed.')
            return self._make_result(False, error=str(e))

    def _tencent_ocr_impl(self, image_b64: str, include_location: bool) -> OcrResult:
        """实现 Tencent OCR 调用的实际逻辑。"""
        cred = credential.Credential(self.settings.TENCENT_SECRET_ID, self.settings.TENCENT_SECRET_KEY)
        client = ocr_client.OcrClient(cred, "ap-guangzhou")
        req = models.GeneralAccurateOCRRequest()
        req.ImageBase64 = image_b64
        resp = client.GeneralAccurateOCR(req)
        resp_json = json.loads(resp.to_json_string())

        texts = self.parse_tencent_resp(resp_json, include_location=include_location)
        return self._make_result(True, texts=texts, raw=resp_json)

    def _baidu_ocr_impl(self, image_b64: str, include_location: bool) -> OcrResult:
        """实现 Baidu OCR 调用的实际逻辑。"""
        img_bytes = base64.b64decode(image_b64.encode('utf-8'))
        result = self._baidu_client.basicGeneral(img_bytes)

        texts = self.parse_baidu_resp(result, include_location=include_location)
        return self._make_result(True, texts=texts, raw=result)

    def _youdao_ocr_impl(self, image_b64: str, include_location: bool) -> OcrResult:
        """实现 Youdao OCR 调用的实际逻辑。"""
        app_key = self.settings.YOUDAO_APP_ID
        app_secret = self.settings.YOUDAO_APP_SECRET

        sign, curtime, salt = self._generate_youdao_sign(app_key, app_secret, image_b64)

        data = {
            'detectType': '10012',  # 通用识别
            'imageType': '1',  # Base64
            'langType': 'zh-CHS',  # 中文优先
            'img': image_b64,
            'docType': 'json',
            'signType': 'v3',
            'appKey': app_key,
            'salt': salt,
            'curtime': curtime,
            'sign': sign,
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post('https://openapi.youdao.com/ocrapi', data=data, headers=headers, timeout=10)
        resp_json = response.json()

        if resp_json.get('errorCode') != '0':
            return self._make_result(False, raw=resp_json, error=f"Youdao Error: {resp_json.get('errorCode')}")

        texts = self.parse_youdao_resp(resp_json, include_location=include_location)
        return self._make_result(True, texts=texts, raw=resp_json)

    def _zhyunxi_ocr_impl(self, image_b64: str, include_location: bool) -> OcrResult:
        """实现智云曦 OCR 调用的实际逻辑。"""
        api_key = getattr(self.settings, 'ZHYUNXI_API_KEY', None)
        if not api_key:
            return self._make_result(False, error='missing_zhyunxi_api_key')

        api_id = getattr(self.settings, 'ZHYUNXI_API_ID', 15) or 15
        api_url = getattr(self.settings, 'ZHYUNXI_API_URL', "http://api.zhyunxi.com/api.php") or "http://api.zhyunxi.com/api.php"

        payload = {
            'api': api_id,
            'key': api_key,
            'imgbase64': image_b64
        }

        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        resp_json = response.json()

        if resp_json.get('code') not in (0, '0'):
            return self._make_result(False, raw=resp_json, error=f"Zhyunxi Error: {resp_json.get('msg')}")

        texts = self.parse_zhyunxi_resp(resp_json, include_location=include_location)
        return self._make_result(True, texts=texts, raw=resp_json)

    # --- 对外暴露的同步方法：使用包装器 ---

    def tencent_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        return self._ocr_api_wrapper(self._tencent_ocr_impl, image, include_location)

    def baidu_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        return self._ocr_api_wrapper(self._baidu_ocr_impl, image, include_location)

    def youdao_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        return self._ocr_api_wrapper(self._youdao_ocr_impl, image, include_location)

    def zhyunxi_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        return self._ocr_api_wrapper(self._zhyunxi_ocr_impl, image, include_location)

    # --- 异步支持 ---

    async def async_tencent_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Async wrapper for `tencent_ocr` using a thread so callers can await it."""
        return await asyncio.to_thread(self.tencent_ocr, image, include_location)

    async def async_baidu_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Async wrapper for `baidu_ocr`."""
        return await asyncio.to_thread(self.baidu_ocr, image, include_location)

    async def async_youdao_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Async wrapper for `youdao_ocr`."""
        return await asyncio.to_thread(self.youdao_ocr, image, include_location)

    async def async_zhyunxi_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Async wrapper for `zhyunxi_ocr`."""
        return await asyncio.to_thread(self.zhyunxi_ocr, image, include_location)

    async def async_parallel_ocr(self, image: cv2.Mat, providers: List[str], include_location: bool = False) -> Dict[str, OcrResult]:
        """Run multiple OCR providers in parallel and return a dict of results."""
        coro_map: Dict[str, Callable[..., Any]] = {
            '腾讯': self.async_tencent_ocr,
            '百度': self.async_baidu_ocr,
            '有道': self.async_youdao_ocr,
            '云析': self.async_zhyunxi_ocr,
        }

        tasks_map = {
            p: coro_map[p](image=image, include_location=include_location)
            for p in providers if p in coro_map
        }

        if not tasks_map:
            return {}

        names = list(tasks_map.keys())
        tasks = list(tasks_map.values())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                logging.exception(f'{name} 的并行 OCR 任务失败，出现未处理的异常.')
                output[name] = self._make_result(False, error=f"Unhandled async exception: {type(result).__name__}")
            else:
                output[name] = result
        return output

    async def async_ocr(self, provider: str, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Convenience dispatcher: awaitable OCR call for a single provider."""
        provider_lower = (provider or '').lower()
        coro_map: Dict[str, Callable[..., Any]] = {
            '腾讯': self.async_tencent_ocr,
            '百度': self.async_baidu_ocr,
            '有道': self.async_youdao_ocr,
            '云析': self.async_zhyunxi_ocr,
        }

        fn = coro_map.get(provider_lower)
        if fn:
            return await fn(image=image, include_location=include_location)

        raise ValueError(f"未知的 OCR 程序: {provider}")
