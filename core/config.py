import os

API_KEY = "sk-a2c7a62fa5b7d75dff72f6b02eca78d1d63b7b35a72256a8"
SECRET_KEY = "my-fixed-secret-key-2024-for-ai-studio"
BASE_URL = "https://api.likeadmin.cn/api/v1"
JWT_EXPIRATION = 7 * 24 * 60 * 60
OUTPUT_DIR = "outputs"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/studio.db")
