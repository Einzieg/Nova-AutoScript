import asyncio
import base64
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable

import cv2

from core.tools.RapidOcr import RapidOcr

# from device_operation.Settings import Settings

# settings = Settings()

Box = Tuple[int, int, int, int]
Coordinate = Tuple[int, int]

OcrResult = Dict[str, Any]

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("tencentcloud_sdk_common").setLevel(logging.WARNING)


class OcrTools:
    """
    Simple OCR tools wrapper with unified parsers for Baidu, Tencent and Youdao.

    Each public OCR method returns a dict:
      { 'success': bool, 'texts': List[str] or List[{'text', 'box'}], 'raw': Any, 'error': Optional[str] }
    """

    def __init__(self):

        self._rapid_ocr = RapidOcr()

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
    def _center_from_box(box: Any) -> Optional[Coordinate]:
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            return None
        try:
            left, top, right, bottom = [int(float(value)) for value in box]
            return (left + right) // 2, (top + bottom) // 2
        except Exception:
            logging.warning("解析 OCR 文本中心点时出错.", exc_info=True)
            return None

    @staticmethod
    def _text_matches(candidate: str, target: str, exact: bool, case_sensitive: bool) -> bool:
        if not case_sensitive:
            candidate = candidate.lower()
            target = target.lower()
        if exact:
            return candidate == target
        return target in candidate

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

    def rapid_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        return self._rapid_ocr.ocr(image=image, include_location=include_location)

    def ocr(self, provider: str, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        provider_lower = (provider or '').lower()
        func_map: Dict[str, Callable[..., OcrResult]] = {
            # '腾讯': self.tencent_ocr,
            # '百度': self.baidu_ocr,
            # '有道': self.youdao_ocr,
            # '云析': self.zhyunxi_ocr,
            'rapidocr': self.rapid_ocr,
        }

        fn = func_map.get(provider_lower)
        if fn:
            return fn(image=image, include_location=include_location)

        raise ValueError(f"未知的 OCR 程序: {provider}")

    def get_text_centers(
            self,
            image: cv2.Mat,
            target_text: str,
            provider: str = 'RapidOcr',
            exact: bool = True,
            case_sensitive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Return OCR text matches with center coordinates.

        Coordinates are relative to the image passed in. If the image is a full
        screenshot, centers are screen coordinates; if it is cropped, centers are
        relative to that crop.
        """
        if not target_text:
            return []

        result = self.ocr(provider=provider, image=image, include_location=True)
        if not result.get('success'):
            return []

        matches: List[Dict[str, Any]] = []
        for item in result.get('texts', []):
            if not isinstance(item, dict):
                continue

            text = str(item.get('text') or '')
            if not self._text_matches(text, target_text, exact, case_sensitive):
                continue

            box = item.get('box')
            center = self._center_from_box(box)
            if center is None:
                continue

            matches.append({'text': text, 'box': box, 'center': center})

        return matches

    def get_text_center(
            self,
            image: cv2.Mat,
            target_text: str,
            provider: str = 'RapidOcr',
            exact: bool = True,
            case_sensitive: bool = False,
    ) -> Optional[Coordinate]:
        matches = self.get_text_centers(
            image=image,
            target_text=target_text,
            provider=provider,
            exact=exact,
            case_sensitive=case_sensitive,
        )
        if not matches:
            return None
        return matches[0]['center']

    async def async_rapid_ocr(self, image: cv2.Mat, include_location: bool = False) -> OcrResult:
        """Async wrapper for `rapid_ocr`."""
        return await asyncio.to_thread(self.rapid_ocr, image, include_location)

    async def async_get_text_centers(
            self,
            image: cv2.Mat,
            target_text: str,
            provider: str = 'RapidOcr',
            exact: bool = True,
            case_sensitive: bool = False,
    ) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(
            self.get_text_centers,
            image,
            target_text,
            provider,
            exact,
            case_sensitive,
        )

    async def async_get_text_center(
            self,
            image: cv2.Mat,
            target_text: str,
            provider: str = 'RapidOcr',
            exact: bool = True,
            case_sensitive: bool = False,
    ) -> Optional[Coordinate]:
        return await asyncio.to_thread(
            self.get_text_center,
            image,
            target_text,
            provider,
            exact,
            case_sensitive,
        )

    async def async_parallel_ocr(self, image: cv2.Mat, providers: List[str], include_location: bool = False) -> Dict[str, OcrResult]:
        """Run multiple OCR providers in parallel and return a dict of results."""
        coro_map: Dict[str, Callable[..., Any]] = {
            # '腾讯': self.async_tencent_ocr,
            # '百度': self.async_baidu_ocr,
            # '有道': self.async_youdao_ocr,
            # '云析': self.async_zhyunxi_ocr,
            'rapidocr': self.async_rapid_ocr,
            'RapidOcr': self.async_rapid_ocr,
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
            # '腾讯': self.async_tencent_ocr,
            # '百度': self.async_baidu_ocr,
            # '有道': self.async_youdao_ocr,
            # '云析': self.async_zhyunxi_ocr,
            'rapidocr': self.async_rapid_ocr,
        }

        fn = coro_map.get(provider_lower)
        if fn:
            return await fn(image=image, include_location=include_location)

        raise ValueError(f"未知的 OCR 程序: {provider}")
