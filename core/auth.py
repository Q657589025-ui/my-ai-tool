import bcrypt
import jwt
from datetime import datetime
from core.config import SECRET_KEY, JWT_EXPIRATION
from core.database import get_db, User

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id, username, role):
    payload = {"user_id": user_id, "username": username, "role": role, "exp": datetime.utcnow().timestamp() + JWT_EXPIRATION}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None

def register_user(username, email, password):
    try:
        with get_db() as db:
            if db.query(User).filter(User.username == username).first():
                return {"error": "用户名已存在"}
            if db.query(User).filter(User.email == email).first():
                return {"error": "邮箱已注册"}
            hashed = hash_password(password)
            user = User(username=username, email=email, password_hash=hashed)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}
    except Exception as e:
        return {"error": f"注册失败: {str(e)}"}

def login_user(username, password):
    try:
        with get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user or not verify_password(password, user.password_hash):
                return {"error": "用户名或密码错误"}
            token = create_token(user.id, user.username, user.role)
            return {"token": token, "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "points": user.points}}
    except Exception as e:
        return {"error": f"登录失败: {str(e)}"}

def get_user_points(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user.points if user else 0
