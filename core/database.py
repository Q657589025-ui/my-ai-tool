import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool
from config.settings import DATABASE_URL

if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

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
    role = Column(String, default="user")
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
    result = Column(Text)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="works")

Base.metadata.create_all(bind=engine)

# ---------- 会话管理 ----------
def get_db_session():
    return SessionLocal()
