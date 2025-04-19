import cv2
from rapidocr import RapidOCR


class RapidOcr:

    def __init__(self):
        self.engine = RapidOCR()

    def detect(self, image):
        return self.engine(image)

    def region_detect(self, image, y_start, y_end, x_start, x_end):
        img_region = cv2.imread(image)[y_start:y_end, x_start:x_end]
        return self.engine(img_region)

    def get_text_coordinates(self, image, text):
        result = self.engine(image)
        for i in result.txts:
            print(i)
            if text in i:
                return result.boxes[i.index(text)]
        return False
