import asyncio
import time

import cv2
from msc.minicap import MiniCap
from msc.mumu import MuMuCap
from msc.droidcast import DroidCast
from msc.screencap import ScreenCap
from mtc.maatouch import MaaTouch
from mtc.minitouch import MiniTouch
from mtc.mumu import MuMuTouch
from mtc.touch import Touch


# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)


def perform_screencap(controller: ScreenCap):
    return controller.save_screencap()


def perform_click(controller: Touch, x, y):
    controller.click(x, y)


async def perform_swipe(controller: Touch, points: list, duration: int = 500):
    await controller.swipe(points, duration)


# perform_screencap(DroidCast("127.0.0.1:16384"))

# asyncio.run(perform_swipe(MuMuTouch(6), [(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 500))


# perform_screencap(MuMuCap(0))
#
# img = cv2.imread("screencap.png")
# cv2.imshow("img", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

# device = DeviceUtils("6")
#
# asyncio.run(device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 200))

# control = MiniTouch('127.0.0.1:16384')
# asyncio.run(control.pinch((650, 235), (1265, 840), (900, 480), (1020, 600), duration=400))

control = MaaTouch('127.0.0.1:16384')
asyncio.run(control.swipe([(900, 480), (900, 600), (900, 720), (900, 840)], duration=400))
time.sleep(3)
asyncio.run(control.swipe([(900, 840), (900, 720), (900, 600), (900, 480), (900, 360), (900, 240)], duration=400))
