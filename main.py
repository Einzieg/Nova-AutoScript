import logging
import os
from datetime import datetime

from core.GuiApp import GuiApp
from device_operation.SQLInitialization import SQLInitialization

log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(level=logging.INFO)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(root_logger.level)

log_file_handler = logging.FileHandler(filename=os.path.join(log_dir, f"AutoNova_{datetime.now().strftime('%Y-%m-%d')}.log"), mode='a', encoding='utf-8')
log_file_handler.setFormatter(log_formatter)
root_logger.addHandler(log_file_handler)

if __name__ == "__main__":
    # 初始化数据库
    sql_init = SQLInitialization()
    sql_init.initialization()

if __name__ in {"__main__", "__mp_main__"}:
    application = GuiApp()
    application.run()
