import time

from mmumu import get_mumu_path
from msc.minicap import MiniCap
from msc.mumu import MuMuScreenCap

# 初始化 MuMuScreenCap
# mumu_s = MuMuScreenCap(instance_index=0, emulator_install_path=get_mumu_path())
# for i in range(100):
#     start = time.time()
#     mumu_s.save_screencap("screencap.png")
#     print("save_screencap time:", time.time() - start)

# touch = MuMuTouch(instance_index=0, emulator_install_path=get_mumu_path())
# touch.click(1, 1)

cap = MiniCap("127.0.0.1:16384")
for i in range(100):
    start = time.time()
    cap.save_screencap("screencap.png")
    print("save_screencap time:", time.time() - start)
