import os
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
from core.config import config

DATABASE_URL = config.DATABASE_URL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, poolclass=NullPool)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ---------- 模型 ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    avatar = Column(String, default="")
    points = Column(Integer, default=10000)
    role = Column(String, default="user")  # user, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="user")
    works = relationship("Work", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    model = Column(String)
    prompt = Column(Text)
    status = Column(String, default="waiting")
    progress = Column(Integer, default=0)
    result = Column(Text)  # JSON
    cost = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")

class Work(Base):
    __tablename__ = "works"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    title = Column(String)
    prompt = Column(Text)
    model = Column(String)
    url = Column(Text)
    cdn_url = Column(Text, default="")
    file_size = Column(Integer, default=0)
    storage_type = Column(String, default="local")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="works")

# ---------- 初始化 ----------
def init_db():
    Base.metadata.create_all(bind=engine)

# ---------- DB 会话 ----------
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- 用户操作 ----------
def get_user_by_username(db, username):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db, user_id):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db, username, email, password_hash, role="user", points=10000):
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        points=points,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_points(db, user_id, amount):
    user = get_user_by_id(db, user_id)
    if user:
        user.points += amount
        db.commit()
        return True
    return False

def get_user_points(db, user_id):
    user = get_user_by_id(db, user_id)
    return user.points if user else 0
