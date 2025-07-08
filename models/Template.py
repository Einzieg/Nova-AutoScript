import logging

import cv2


class Template:
    def __init__(self, name, threshold, template_path, forbidden=False):
        self.name = name
        self.threshold = threshold
        self.template_path = template_path
        self.cv_tmp = cv2.imread(template_path)
        self.forbidden = forbidden
        print(f"加载模板:{name} {template_path}")
