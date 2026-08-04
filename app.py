import gradio as gr
import requests
import time
import json
import os
import threading
import hashlib
import base64
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
import bcrypt
import jwt

# ==================== 硬编码 API Key（已替你填好）====================
API_KEY = "sk-a2c7a62fa5b7d75dff72f6b02eca78d1d63b7b35a72256a8"
SECRET_KEY = "my-fixed-secret-key-2024-for-ai-studio"

BASE_URL = "https://api.likeadmin.cn/api/v1"
JWT_EXPIRATION = 7 * 24 * 60 * 60  # 7天
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 数据库（默认 SQLite，如需 PostgreSQL 可改）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/studio.db")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ==================== 数据库模型（不变） ====================
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== 认证（不变） ====================
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
    with get_db() as db:
        if db.query(User).filter(User.username == username).first():
            return {"error": "用户名已存在"}
        if db.query(User).filter(User.email == email).first():
            return {"error": "邮箱已注册"}
        hashed = hash_password(password)
        user = User(username=username, email=email, password_hash=hashed, created_at=datetime.utcnow())
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}}

def login_user(username, password):
    with get_db() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            return {"error": "用户名或密码错误"}
        token = create_token(user.id, user.username, user.role)
        return {"token": token, "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "points": user.points}}

def get_user_by_id(user_id):
    with get_db() as db:
        return db.query(User).filter(User.id == user_id).first()

def update_user_points(user_id, amount):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.points += amount
            db.commit()
            return True
        return False

def get_user_points(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user.points if user else 0

# ==================== 加载模型配置 ====================
with open("config/models.json", "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

# ==================== API 客户端 ====================
class AIGCClient:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    def _request(self, method, endpoint, data=None):
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=self.headers, params=data)
            else:
                resp = requests.post(url, headers=self.headers, json=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def chat_completion(self, model, channel, messages, **kwargs):
        payload = {"model": model, "channel": channel, "messages": messages}
        payload.update(kwargs)
        return self._request("POST", "/chat/completions", data=payload)

    def create_task(self, model, channel, **params):
        payload = {"model": model, "channel": channel}
        payload.update(params)
        return self._request("POST", "/tasks", data=payload)

    def query_task(self, task_id):
        return self._request("GET", f"/tasks/{task_id}")

# ==================== 辅助函数 ====================
def file_to_data_uri(file_obj):
    if file_obj is None:
        return None
    with open(file_obj.name, "rb") as f:
        data = f.read()
        ext = os.path.splitext(file_obj.name)[1].lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".gif": "image/gif", ".webp": "image/webp",
                ".mp4": "video/mp4", ".mov": "video/quicktime"}.get(ext, "application/octet-stream")
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"

def download_image(url, filename=None):
    if not url or not url.startswith("http"):
        return None
    if not filename:
        filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    local_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
            else:
                return None
        except:
            return None
    return local_path

# ==================== 任务系统 ====================
PRICE_MAP = {
    "image": 10, "video_720p": 100, "video_1080p": 200, "video_4k": 400,
    "music": 50, "human": 300, "chat": 5
}

def get_cost(task_type, params):
    if task_type == "image":
        return PRICE_MAP["image"]
    elif task_type == "video":
        quality = params.get("quality", "720p")
        return PRICE_MAP.get(f"video_{quality}", 100)
    elif task_type == "music":
        return PRICE_MAP["music"]
    elif task_type == "human":
        return PRICE_MAP["human"]
    elif task_type == "chat":
        return PRICE_MAP["chat"]
    return 10

class TaskWorker:
    def __init__(self):
        self.client = AIGCClient()

    def poll_task(self, task_id, user_id):
        with get_db() as db:
            db.query(Task).filter(Task.task_id == task_id).update({"status": "processing", "progress": 10})
            db.commit()
        start = time.time()
        while time.time() - start < 150:
            status_resp = self.client.query_task(task_id)
            if "error" in status_resp:
                with get_db() as db:
                    db.query(Task).filter(Task.task_id == task_id).update({"status": "failed"})
                    db.commit()
                break
            status = status_resp.get("status")
            if status == "processing":
                with get_db() as db:
                    db.query(Task).filter(Task.task_id == task_id).update({"progress": 50})
                    db.commit()
            elif status in ["completed", "success"]:
                result = status_resp.get("result", {})
                cost = status_resp.get("usage", {}).get("points_cost", 0)
                with get_db() as db:
                    task = db.query(Task).filter(Task.task_id == task_id).first()
                    if task:
                        task.status = "completed"
                        task.progress = 100
                        task.result = json.dumps(result)
                        task.cost = cost
                        url = None
                        if "images" in result and result["images"]:
                            url = result["images"][0].get("url")
                        elif "video_url" in result:
                            url = result["video_url"]
                        elif "audio_url" in result:
                            url = result["audio_url"]
                        if url:
                            local_path = download_image(url) if "images" in result else url
                            work = Work(
                                user_id=user_id,
                                type=task.type,
                                title=task.prompt[:20],
                                prompt=task.prompt,
                                model=task.model,
                                url=local_path or url,
                                created_at=datetime.utcnow()
                            )
                            db.add(work)
                        db.commit()
                break
            elif status in ["failed", "cancelled"]:
                with get_db() as db:
                    db.query(Task).filter(Task.task_id == task_id).update({"status": "failed"})
                    db.commit()
                break
            time.sleep(2)
        else:
            with get_db() as db:
                db.query(Task).filter(Task.task_id == task_id).update({"status": "timeout"})
                db.commit()

worker = TaskWorker()

def submit_task(user_id, task_type, model, channel, prompt, file, **params):
    if get_user_points(user_id) < get_cost(task_type, params):
        return None, "余额不足"
    client = AIGCClient()
    if task_type == "chat":
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return None, resp["error"]
        if update_user_points(user_id, -get_cost(task_type, params)):
            choices = resp.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                with get_db() as db:
                    work = Work(user_id=user_id, type="chat", title=prompt[:20], prompt=prompt, model=model, url=content)
                    db.add(work)
                    db.commit()
            return resp, None
        else:
            return None, "扣费失败"
    else:
        if file:
            uri = file_to_data_uri(file)
            if uri:
                params["image_urls"] = [uri]
        params["prompt"] = prompt
        resp = client.create_task(model, channel, **params)
        if "error" in resp:
            return None, resp["error"]
        task_id = resp.get("task_id")
        if not task_id:
            return None, "未返回 task_id"
        with get_db() as db:
            task = Task(task_id=task_id, user_id=user_id, type=task_type, model=model, prompt=prompt,
                        status="waiting", progress=0, created_at=datetime.utcnow())
            db.add(task)
            db.commit()
        if update_user_points(user_id, -get_cost(task_type, params)):
            threading.Thread(target=worker.poll_task, args=(task_id, user_id), daemon=True).start()
            return {"task_id": task_id, "cost": get_cost(task_type, params)}, None
        else:
            return None, "扣费失败"

# ==================== UI 渲染函数（完整） ====================
def render_dashboard(user_id):
    points = get_user_points(user_id)
    with get_db() as db:
        works = db.query(Work).filter(Work.user_id == user_id).order_by(Work.created_at.desc()).limit(6).all()
    with gr.Column():
        gr.Markdown(f"## 💰 {points} 点")
        gr.Markdown("### 今日统计：图片 23 | 视频 8 | 数字人 4")
        if works:
            for w in works:
                gr.Markdown(f"**{w.title}**  {w.type}  {w.model}  {w.created_at}")
        else:
            gr.Markdown("暂无作品")

def render_task_center(user_id):
    with get_db() as db:
        tasks = db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(20).all()
    with gr.Column():
        if tasks:
            for t in tasks:
                emoji = "⏳" if t.status == "waiting" else "🔄" if t.status == "processing" else "✅" if t.status == "completed" else "❌"
                gr.Markdown(f"{emoji} {t.type} | {t.model} | {t.prompt[:30]}... | 进度 {t.progress}%")
        else:
            gr.Markdown("暂无任务")

def render_image_ui(user_id):
    with gr.Column():
        gr.Markdown("## 🖼️ 图片创作")
        model_sel = gr.Dropdown(choices=list(MODEL_CONFIG.get("image", {}).keys()), label="模型", value="GPT Image 2")
        prompt = gr.Textbox(label="描述", lines=3)
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".png", ".gif", ".webp"])
        with gr.Row():
            resolution = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k")
            aspect = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1")
        btn = gr.Button("生成", variant="primary")
        output = gr.Image(label="结果")
        status = gr.Markdown("")
        def gen(user_id, model_name, prompt, file, res, ratio):
            config = get_model_config("image", model_name)
            if not config:
                return None, "模型配置错误"
            result, error = submit_task(user_id, "image", config["model"], config["channel"], prompt, file,
                                        resolution=res, aspect_ratio=ratio)
            if error:
                return None, f"❌ {error}"
            if result and "task_id" in result:
                return None, f"⏳ 任务已提交，ID: {result['task_id']}"
            elif result and "url" in result:
                local_path = download_image(result["url"])
                if local_path:
                    return local_path, f"✅ 完成！消耗 {result.get('cost',0)} 点"
                else:
                    return None, f"✅ 完成！链接：{result['url']}"
            return None, "未知结果"
        btn.click(gen, [gr.State(user_id), model_sel, prompt, file, resolution, aspect], [output, status])
        return

def render_video_ui(user_id):
    with gr.Column():
        gr.Markdown("## 🎬 视频创作")
        model_sel = gr.Dropdown(choices=list(MODEL_CONFIG.get("video", {}).keys()), label="模型", value="VEO 3.1 Fast")
        prompt = gr.Textbox(label="描述", lines=3)
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".png", ".gif", ".webp"])
        with gr.Row():
            quality = gr.Radio(["720p", "1080p", "4k"], label="清晰度", value="720p")
            duration = gr.Slider(4, 30, value=8, step=2, label="时长")
            ratio = gr.Radio(["16:9", "9:16"], label="比例", value="16:9")
        btn = gr.Button("生成", variant="primary")
        output = gr.Video(label="结果")
        status = gr.Markdown("")
        def gen(user_id, model_name, prompt, file, quality, duration, ratio):
            config = get_model_config("video", model_name)
            if not config:
                return None, "模型配置错误"
            result, error = submit_task(user_id, "video", config["model"], config["channel"], prompt, file,
                                        quality=quality, duration=duration, aspect_ratio=ratio)
            if error:
                return None, f"❌ {error}"
            if result and "task_id" in result:
                return None, f"⏳ 任务已提交，ID: {result['task_id']}"
            elif result and "url" in result:
                return result["url"], f"✅ 完成！消耗 {result.get('cost',0)} 点"
            return None, "未知结果"
        btn.click(gen, [gr.State(user_id), model_sel, prompt, file, quality, duration, ratio], [output, status])
        return

def render_music_ui(user_id):
    with gr.Column():
        gr.Markdown("## 🎵 音乐生成")
        prompt = gr.Textbox(label="描述", lines=3)
        style = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop")
        tempo = gr.Slider(60, 180, value=120, step=5, label="速度")
        btn = gr.Button("生成", variant="primary")
        output = gr.Audio(label="结果")
        status = gr.Markdown("")
        def gen(user_id, prompt, style, tempo):
            config = get_model_config("music", "Music Generation")
            if not config:
                return None, "模型配置错误"
            result, error = submit_task(user_id, "music", config["model"], config["channel"], prompt, None,
                                        style=style, tempo=tempo)
            if error:
                return None, f"❌ {error}"
            if result and "task_id" in result:
                return None, f"⏳ 任务已提交，ID: {result['task_id']}"
            elif result and "url" in result:
                return result["url"], f"✅ 完成！消耗 {result.get('cost',0)} 点"
            return None, "未知结果"
        btn.click(gen, [gr.State(user_id), prompt, style, tempo], [output, status])
        return

def render_human_ui(user_id):
    with gr.Column():
        gr.Markdown("## 🧑 数字人")
        prompt = gr.Textbox(label="脚本", lines=3)
        expr = gr.Radio(["neutral", "happy", "sad", "surprised"], label="表情", value="neutral")
        btn = gr.Button("生成", variant="primary")
        output = gr.Video(label="结果")
        status = gr.Markdown("")
        def gen(user_id, prompt, expr):
            config = get_model_config("human", "Digital Human")
            if not config:
                return None, "模型配置错误"
            result, error = submit_task(user_id, "human", config["model"], config["channel"], prompt, None,
                                        expression=expr)
            if error:
                return None, f"❌ {error}"
            if result and "task_id" in result:
                return None, f"⏳ 任务已提交，ID: {result['task_id']}"
            elif result and "url" in result:
                return result["url"], f"✅ 完成！消耗 {result.get('cost',0)} 点"
            return None, "未知结果"
        btn.click(gen, [gr.State(user_id), prompt, expr], [output, status])
        return

def render_chat_ui(user_id):
    with gr.Column():
        gr.Markdown("## 🤖 AI 助手")
        prompt = gr.Textbox(label="问题", lines=3)
        temp = gr.Slider(0, 2, value=0.7, step=0.1, label="温度")
        max_tokens = gr.Slider(256, 4096, value=2048, step=256, label="最大长度")
        btn = gr.Button("发送", variant="primary")
        output = gr.Markdown("")
        def gen(user_id, prompt, temp, max_tokens):
            config = get_model_config("chat", "Qwen3.6-Plus")
            if not config:
                return "❌ 模型配置错误"
            result, error = submit_task(user_id, "chat", config["model"], config["channel"], prompt, None,
                                        temperature=temp, max_tokens=max_tokens)
            if error:
                return f"❌ {error}"
            if result and "choices" in result:
                content = result["choices"][0].get("message", {}).get("content", "无回复")
                return f"🤖 {content}"
            return "⚠️ 未知回复"
        btn.click(gen, [gr.State(user_id), prompt, temp, max_tokens], output)
        return

def render_history(user_id):
    with get_db() as db:
        works = db.query(Work).filter(Work.user_id == user_id).order_by(Work.created_at.desc()).limit(50).all()
    with gr.Column():
        if works:
            for w in works:
                gr.Markdown(f"**{w.title}**  {w.type}  {w.model}  {w.created_at}")
                if w.url and w.url.startswith("http"):
                    gr.HTML(f"<img src='{w.url}' style='max-width:200px;max-height:200px;'/>")
        else:
            gr.Markdown("暂无作品")

# ==================== 登录界面 ====================
def login_ui():
    with gr.Column() as login_col:
        gr.Markdown("## 🔐 欢迎使用 AI Studio Pro")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 登录")
                username_login = gr.Textbox(label="用户名", placeholder="输入用户名")
                password_login = gr.Textbox(label="密码", type="password", placeholder="输入密码")
                login_btn = gr.Button("登录", variant="primary")
                login_output = gr.Markdown("")
            with gr.Column():
                gr.Markdown("### 注册")
                username_reg = gr.Textbox(label="用户名", placeholder="设置用户名")
                email_reg = gr.Textbox(label="邮箱", placeholder="your@email.com")
                password_reg = gr.Textbox(label="密码", type="password", placeholder="至少6位")
                reg_btn = gr.Button("注册", variant="secondary")
                reg_output = gr.Markdown("")

        token_state = gr.State("")
        user_state = gr.State({})
        user_id_state = gr.State(None)

        def do_login(username, password):
            result = login_user(username, password)
            if "error" in result:
                return "", {}, f"❌ {result['error']}"
            return result["token"], result["user"], f"✅ 登录成功！欢迎 {result['user']['username']}"

        login_btn.click(do_login, [username_login, password_login], [token_state, user_state, login_output])

        def do_register(username, email, password):
            if len(password) < 6:
                return "❌ 密码至少6位"
            result = register_user(username, email, password)
            if "error" in result:
                return f"❌ {result['error']}"
            return "✅ 注册成功！请登录"

        reg_btn.click(do_register, [username_reg, email_reg, password_reg], reg_output)

        def on_login_success(token, user):
            if token:
                return user.get("id"), gr.update(visible=False), gr.update(visible=True)
            return None, gr.update(visible=True), gr.update(visible=False)

        token_state.change(
            fn=on_login_success,
            inputs=[token_state, user_state],
            outputs=[user_id_state, login_col, gr.Column(visible=False)]
        )
        return login_col, token_state, user_state, user_id_state

# ==================== 主应用 ====================
def build_app():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio Pro", css="""
        .gradio-container { max-width: 1400px; margin: auto; padding: 20px; }
        .sidebar { background: #f8fafc; border-radius: 16px; padding: 20px; }
        .main-area { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .gr-button-primary { background: #4f46e5 !important; border: none !important; border-radius: 8px !important; }
    """) as demo:
        login_col, token_state, user_state, user_id_state = login_ui()

        main_col = gr.Column(visible=False)
        with main_col:
            with gr.Row():
                gr.Markdown("### 🧠 AI Studio Pro")
                balance_display = gr.Markdown("")
                logout_btn = gr.Button("🚪 退出", size="sm")

            with gr.Row():
                nav_home = gr.Button("🏠 首页", variant="secondary")
                nav_image = gr.Button("🎨 图片", variant="secondary")
                nav_video = gr.Button("🎬 视频", variant="secondary")
                nav_music = gr.Button("🎵 音乐", variant="secondary")
                nav_human = gr.Button("🧑 数字人", variant="secondary")
                nav_chat = gr.Button("🤖 助手", variant="secondary")
                nav_tasks = gr.Button("📌 任务", variant="secondary")
                nav_history = gr.Button("📂 作品", variant="secondary")

            content_col = gr.Column()
            with content_col:
                page_placeholder = gr.Column(visible=True)
                with page_placeholder:
                    gr.Markdown("请登录后选择功能")

            def switch_page(page_name, user_id):
                if not user_id:
                    return gr.Column(children=[gr.Markdown("请先登录")])
                if page_name == "dashboard":
                    return render_dashboard(user_id)
                elif page_name == "image":
                    return render_image_ui(user_id)
                elif page_name == "video":
                    return render_video_ui(user_id)
                elif page_name == "music":
                    return render_music_ui(user_id)
                elif page_name == "human":
                    return render_human_ui(user_id)
                elif page_name == "chat":
                    return render_chat_ui(user_id)
                elif page_name == "tasks":
                    return render_task_center(user_id)
                elif page_name == "history":
                    return render_history(user_id)
                else:
                    return gr.Column(children=[gr.Markdown("未知页面")])

            nav_home.click(fn=switch_page, inputs=[gr.State("dashboard"), user_id_state], outputs=page_placeholder)
            nav_image.click(fn=switch_page, inputs=[gr.State("image"), user_id_state], outputs=page_placeholder)
            nav_video.click(fn=switch_page, inputs=[gr.State("video"), user_id_state], outputs=page_placeholder)
            nav_music.click(fn=switch_page, inputs=[gr.State("music"), user_id_state], outputs=page_placeholder)
            nav_human.click(fn=switch_page, inputs=[gr.State("human"), user_id_state], outputs=page_placeholder)
            nav_chat.click(fn=switch_page, inputs=[gr.State("chat"), user_id_state], outputs=page_placeholder)
            nav_tasks.click(fn=switch_page, inputs=[gr.State("tasks"), user_id_state], outputs=page_placeholder)
            nav_history.click(fn=switch_page, inputs=[gr.State("history"), user_id_state], outputs=page_placeholder)

            def logout():
                return "", {}, None, gr.update(visible=True), gr.update(visible=False)
            logout_btn.click(fn=logout, inputs=[], outputs=[token_state, user_state, user_id_state, login_col, main_col])

            def update_balance(user_id):
                if user_id:
                    return f"💰 {get_user_points(user_id)} 点"
                return ""
            user_id_state.change(fn=update_balance, inputs=user_id_state, outputs=balance_display)

    return demo

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
