import os

# ===== API & 安全 =====
API_KEY = "sk-a2c7a62fa5b7d75dff72f6b02eca78d1d63b7b35a72256a8"
SECRET_KEY = "my-fixed-secret-key-2024-for-ai-studio"
BASE_URL = "https://api.likeadmin.cn/api/v1"
JWT_EXPIRATION = 7 * 24 * 60 * 60

# ===== 路径 =====
OUTPUT_DIR = "outputs"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/studio.db")

# ===== 模型配置文件路径 =====
MODEL_CONFIG_PATH = "config/models.json"

# ===== 积分价格（默认，可被 price_map.py 覆盖）=====
DEFAULT_PRICE = {
    "image": 10,
    "video_720p": 100,
    "video_1080p": 200,
    "video_4k": 400,
    "music": 50,
    "human": 300,
    "chat": 5
}
