import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from app.GuiApp import GuiApp
from database.db_session import init_database


def log_init():
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(filename=os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log"), mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    root_logger.addHandler(file_handler)


def environ_init():
    # 初始化ADB
    adb_path = Path(__file__).resolve().parent / "static/platform-tools"
    os.environ["PATH"] = str(adb_path) + os.pathsep + os.environ["PATH"]
    try:
        subprocess.run(["adb", "version"], check=True)
        logging.info(f"ADB 环境设置成功 {adb_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"ADB 环境变量设置失败: {e}")


if __name__ == "__main__":
    # 初始化日志
    log_init()
    # 初始化环境变量
    environ_init()
    # 初始化数据库
    init_database()

if __name__ in {"__main__", "__mp_main__"}:
    application = GuiApp()
    application.run()
