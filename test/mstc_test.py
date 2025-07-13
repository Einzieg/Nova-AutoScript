import logging

import cv2
from msc.mumu import MuMuCap
from msc.screencap import ScreenCap
from msc.droidcast import DroidCast
from mtc.maatouch import MaaTouch
from mtc.touch import Touch

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)


def perform_screencap(controller: ScreenCap):
    return controller.save_screencap()


def perform_click(controller: Touch, x, y):
    controller.click(x, y)


def perform_swipe(controller: Touch, points: list, duration: int = 500):
    controller.swipe(points, duration)


perform_screencap(MuMuCap(0))
# img = cv2.imread("screencap.png")
# perform_click(MaaTouch('127.0.0.1:16384'), (200, 300), (400, 300))
# touch = MaaTouch("127.0.0.1:16384")
# touch.pinch([(200, 300), (400, 300)], [(150, 300), (450, 300)], duration=500)

# img = perform_screencap(DroidCast('127.0.0.1:16384'))
#
# cv2.imshow("img", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
