import bcrypt
import jwt
from datetime import datetime, timedelta
from core.config import config
from core.database import (
    get_db, get_user_by_username, get_user_by_email,
    create_user, get_user_by_id, update_user_points
)

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
EXPIRATION = config.JWT_EXPIRATION

# ---------- 密码 ----------
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

# ---------- JWT ----------
def create_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + EXPIRATION
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def verify_token(token: str):
    payload = decode_token(token)
    if not payload:
        return None
    with get_db() as db:
        user = get_user_by_id(db, payload["user_id"])
        return user

# ---------- 业务 ----------
def register_user(username: str, email: str, password: str, role: str = "user"):
    with get_db() as db:
        if get_user_by_username(db, username):
            return {"error": "用户名已存在"}
        if get_user_by_email(db, email):
            return {"error": "邮箱已注册"}
        hashed = hash_password(password)
        user = create_user(db, username, email, hashed, role)
        return {"user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}

def login_user(username: str, password: str):
    with get_db() as db:
        user = get_user_by_username(db, username)
        if not user:
            return {"error": "用户名或密码错误"}
        if not verify_password(password, user.password_hash):
            return {"error": "用户名或密码错误"}
        token = create_token(user.id, user.username, user.role)
        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "points": user.points
            }
        }
