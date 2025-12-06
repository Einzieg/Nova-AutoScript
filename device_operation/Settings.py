import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    BAIDU_APP_ID: str
    BAIDU_API_KEY: str
    BAIDU_SECRET_KEY: str

    TENCENT_SECRET_ID: str
    TENCENT_SECRET_KEY: str

    YOUDAO_APP_ID: str
    YOUDAO_APP_SECRET: str

    ZHYUNXI_API_KEY: str
    ZHYUNXI_API_ID: int
    ZHYUNXI_API_URL: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
