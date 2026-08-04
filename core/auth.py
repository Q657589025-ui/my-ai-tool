import bcrypt
import jwt
from datetime import datetime
from config.settings import SECRET_KEY, JWT_EXPIRATION
from core.database import get_db_session, User

# ---------- 密码 ----------
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

# ---------- JWT ----------
def create_token(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow().timestamp() + JWT_EXPIRATION
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None

# ---------- 业务 ----------
def register_user(username, email, password):
    db = get_db_session()
    try:
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
    finally:
        db.close()

def login_user(username, password):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
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
    finally:
        db.close()

def get_user_by_id(user_id):
    db = get_db_session()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()

def get_user_points(user_id):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.points if user else 0
    finally:
        db.close()

def update_user_points(user_id, amount):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.points += amount
            db.commit()
            return True
        return False
    finally:
        db.close()

def create_default_admin():
    db = get_db_session()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            hashed = hash_password("admin123")
            admin = User(username="admin", email="admin@studio.com", password_hash=hashed, role="admin", points=99999)
            db.add(admin)
            db.commit()
            print("✅ 默认管理员已创建: admin / admin123")
    except Exception as e:
        print(f"⚠️ 创建管理员失败: {e}")
    finally:
        db.close()
