import time
from pathlib import Path

from device_operation.RapidOcr import RapidOcr

ocr = RapidOcr()

# result = ocr.detect(Path('screencap.png'))

result = ocr.region_detect('screencap.png', 240, 860, 1300, 1550)
print(result.boxes)
print(result.txts)


# re = ocr.get_text_coordinates(Path('screencap.png'), '剩余时间')
# print(re)