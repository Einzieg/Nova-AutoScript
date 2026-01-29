import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

import cv2

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:  # pragma: no cover - 运行环境缺失依赖时兜底
    RapidOCR = None


Box = Tuple[int, int, int, int]
OcrResult = Dict[str, Any]


class RapidOcr:
    """RapidOCR(onnxruntime) 的轻量封装，统一输出格式以便集成到 OcrTools。"""

    def __init__(self, config_path: Optional[str] = None, **rapidocr_kwargs: Any) -> None:
        self._config_path = config_path
        self._rapidocr_kwargs = rapidocr_kwargs
        self._engine: Optional[Any] = None
        self._lock = threading.Lock()

    @staticmethod
    def _make_result(
        success: bool,
        texts: Optional[List[Any]] = None,
        raw: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> OcrResult:
        return {"success": bool(success), "texts": texts or [], "raw": raw, "error": error}

    @staticmethod
    def _box_from_points(points: Any) -> Optional[Box]:
        """Convert [[x,y], ...] to (l,t,r,b)."""
        if not isinstance(points, list) or not points:
            return None
        try:
            xs = [int(float(p[0])) for p in points if isinstance(p, (list, tuple)) and len(p) >= 2]
            ys = [int(float(p[1])) for p in points if isinstance(p, (list, tuple)) and len(p) >= 2]
            if not xs or not ys:
                return None
            return min(xs), min(ys), max(xs), max(ys)
        except Exception:
            logging.warning("RapidOCR: 解析检测框失败。", exc_info=True)
            return None

    def _get_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        if RapidOCR is None:
            raise RuntimeError("missing_rapidocr_onnxruntime")
        self._engine = RapidOCR(self._config_path, **self._rapidocr_kwargs)
        return self._engine

    def ocr(self, image: cv2.Mat, include_location: bool = False, **kwargs: Any) -> OcrResult:
        if image is None:
            return self._make_result(False, error="empty_image")

        try:
            engine = self._get_engine()
        except Exception as e:
            return self._make_result(False, error=str(e))

        try:
            with self._lock:
                ocr_res, elapse = engine(image, **kwargs)
        except Exception as e:
            logging.exception("RapidOCR 调用失败。")
            return self._make_result(False, error=str(e))

        raw = {"result": ocr_res, "elapse": elapse}
        if not ocr_res:
            return self._make_result(True, texts=[], raw=raw)

        texts: List[Any] = []
        for item in ocr_res:
            # 典型结构: [box_points, text, score(, ...)]
            if not isinstance(item, (list, tuple)) or len(item) == 0:
                continue

            box_points = None
            text = None

            if len(item) >= 2 and isinstance(item[0], list):
                box_points = item[0]
                text = item[1]
            elif len(item) >= 1 and isinstance(item[0], str):
                # 不含检测框的模式: [text, score]
                text = item[0]

            text_str = "" if text is None else str(text)
            if include_location:
                texts.append({"text": text_str, "box": self._box_from_points(box_points)})
            else:
                texts.append(text_str)

        return self._make_result(True, texts=texts, raw=raw)
