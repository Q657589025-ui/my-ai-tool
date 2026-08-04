import os
from datetime import timedelta

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/studio.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_EXPIRATION = timedelta(days=7)
    AIGC_API_KEY = os.getenv("AIGC_API_KEY")
    if not AIGC_API_KEY:
        raise ValueError("Missing AIGC_API_KEY environment variable")
    BASE_URL = "https://api.likeadmin.cn/api/v1"
    OUTPUT_DIR = "outputs"

config = Config()
