import asyncio
import logging

import cv2
from msc.mumu import MuMuCap
from msc.screencap import ScreenCap
from msc.droidcast import DroidCast
from mtc.adb import ADBTouch
from mtc.maatouch import MaaTouch
from mtc.minitouch import MiniTouch
from mtc.mumu import MuMuTouch
from mtc.touch import Touch

from device_operation.DeviceUtils import DeviceUtils


# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)


def perform_screencap(controller: ScreenCap):
    return controller.save_screencap()


def perform_click(controller: Touch, x, y):
    controller.click(x, y)


async def perform_swipe(controller: Touch, points: list, duration: int = 500):
    await controller.swipe(points, duration)


perform_screencap(MuMuCap(0))

# asyncio.run(perform_swipe(MuMuTouch(6), [(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 500))
# perform_swipe(ADBTouch('127.0.0.1:16576'), [(830, 850), (830, 590)], 150)
# img = cv2.imread("screencap.png")
# perform_click(MaaTouch('127.0.0.1:16384'), (200, 300), (400, 300))
# touch = MaaTouch("127.0.0.1:16384")
# touch.pinch([(200, 300), (400, 300)], [(150, 300), (450, 300)], duration=500)

# img = perform_screencap(DroidCast('127.0.0.1:16384'))
#
# cv2.imshow("img", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# device = DeviceUtils("6")
#
# asyncio.run(device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 200))
