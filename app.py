import gradio as gr
import requests
import time
import json
import os
import threading
import hashlib
from datetime import datetime
from core.database import init_db, get_db, get_user_points, update_user_points
from core.auth import verify_token
from core.config import config
from ui.login_ui import create_login_ui

init_db()
API_KEY = config.AIGC_API_KEY
BASE_URL = config.BASE_URL
OUTPUT_DIR = config.OUTPUT_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("config/models.json", "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

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

def file_to_data_uri(file_obj):
    if file_obj is None:
        return None
    import base64
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
            db.execute("UPDATE tasks SET status='processing', progress=10 WHERE task_id=?", (task_id,))
            db.commit()
        start = time.time()
        while time.time() - start < 150:
            status_resp = self.client.query_task(task_id)
            if "error" in status_resp:
                with get_db() as db:
                    db.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
                    db.commit()
                break
            status = status_resp.get("status")
            if status == "processing":
                with get_db() as db:
                    db.execute("UPDATE tasks SET progress=50 WHERE task_id=?", (task_id,))
                    db.commit()
            elif status in ["completed", "success"]:
                result = status_resp.get("result", {})
                cost = status_resp.get("usage", {}).get("points_cost", 0)
                with get_db() as db:
                    db.execute("UPDATE tasks SET status='completed', progress=100, result=?, cost=? WHERE task_id=?",
                               (json.dumps(result), cost, task_id))
                    db.commit()
                    url = None
                    if "images" in result and result["images"]:
                        url = result["images"][0].get("url")
                    elif "video_url" in result:
                        url = result["video_url"]
                    elif "audio_url" in result:
                        url = result["audio_url"]
                    if url:
                        local_path = download_image(url) if "images" in result else url
                        row = db.execute("SELECT prompt, model, type FROM tasks WHERE task_id=?", (task_id,)).fetchone()
                        if row:
                            db.execute(
                                "INSERT INTO works (user_id, type, title, prompt, model, url, created_at) VALUES (?,?,?,?,?,?,?)",
                                (user_id, row[2], row[0][:20], row[0], row[1], local_path or url, datetime.utcnow())
                            )
                            db.commit()
                break
            elif status in ["failed", "cancelled"]:
                with get_db() as db:
                    db.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
                    db.commit()
                break
            time.sleep(2)
        else:
            with get_db() as db:
                db.execute("UPDATE tasks SET status='timeout' WHERE task_id=?", (task_id,))
                db.commit()

worker = TaskWorker()

def submit_task(user_id, task_type, model, channel, prompt, file, **params):
    with get_db() as db:
        points = get_user_points(db, user_id)
        cost = get_cost(task_type, params)
        if points < cost:
            return None, "余额不足"
    client = AIGCClient()
    if task_type == "chat":
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return None, resp["error"]
        with get_db() as db:
            if update_user_points(db, user_id, -cost):
                choices = resp.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    db.execute(
                        "INSERT INTO works (user_id, type, title, prompt, model, url, created_at) VALUES (?,?,?,?,?,?,?)",
                        (user_id, "chat", prompt[:20], prompt, model, content, datetime.utcnow())
                    )
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
            db.execute(
                "INSERT INTO tasks (task_id, user_id, type, model, prompt, status, progress, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (task_id, user_id, task_type, model, prompt, "waiting", 0, datetime.utcnow())
            )
            db.commit()
            if update_user_points(db, user_id, -cost):
                threading.Thread(target=worker.poll_task, args=(task_id, user_id), daemon=True).start()
                return {"task_id": task_id, "cost": cost}, None
            else:
                return None, "扣费失败"

# ---------- UI 模块（所有函数接收 user_id_state） ----------
def render_dashboard(user_id_state):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id_state.value,)).fetchone()
        points = user["points"] if user else 0
    with gr.Column():
        gr.Markdown(f"## 💰 {points} 点")
        gr.Markdown("### 今日统计：图片 23 | 视频 8 | 数字人 4")
        with get_db() as db:
            works = db.execute("SELECT * FROM works WHERE user_id=? ORDER BY created_at DESC LIMIT 6", (user_id_state.value,)).fetchall()
        if works:
            for w in works:
                gr.Markdown(f"**{w['title']}**  {w['type']}  {w['model']}  {w['created_at']}")
        else:
            gr.Markdown("暂无作品")

def render_task_center(user_id_state):
    with get_db() as db:
        tasks = db.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (user_id_state.value,)).fetchall()
    with gr.Column():
        if tasks:
            for t in tasks:
                emoji = "⏳" if t['status']=="waiting" else "🔄" if t['status']=="processing" else "✅" if t['status']=="completed" else "❌"
                gr.Markdown(f"{emoji} {t['type']} | {t['model']} | {t['prompt'][:30]}... | 进度 {t['progress']}%")
        else:
            gr.Markdown("暂无任务")

def render_image_ui(user_id_state):
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
        btn.click(gen, [user_id_state, model_sel, prompt, file, resolution, aspect], [output, status])
        return

def render_video_ui(user_id_state):
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
        btn.click(gen, [user_id_state, model_sel, prompt, file, quality, duration, ratio], [output, status])
        return

def render_music_ui(user_id_state):
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
        btn.click(gen, [user_id_state, prompt, style, tempo], [output, status])
        return

def render_human_ui(user_id_state):
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
        btn.click(gen, [user_id_state, prompt, expr], [output, status])
        return

def render_chat_ui(user_id_state):
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
        btn.click(gen, [user_id_state, prompt, temp, max_tokens], output)
        return

# ---------- 主应用 ----------
def build_app():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio Pro", css="""
        .gradio-container { max-width: 1400px; margin: auto; padding: 20px; }
        .sidebar { background: #f8fafc; border-radius: 16px; padding: 20px; }
        .main-area { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .gr-button-primary { background: #4f46e5 !important; border: none !important; border-radius: 8px !important; }
    """) as demo:
        # 状态
        token_state = gr.State("")
        user_state = gr.State({})
        user_id_state = gr.State(None)

        # ---------- 登录界面 ----------
        login_col = gr.Column(visible=True)
        with login_col:
            login_ui_col, token_state, user_state = create_login_ui()
            # 登录成功后切换到主界面
            def on_login_success(token, user):
                if token:
                    return user.get("id"), gr.update(visible=False), gr.update(visible=True)
                return None, gr.update(visible=True), gr.update(visible=False)
            token_state.change(
                fn=on_login_success,
                inputs=[token_state, user_state],
                outputs=[user_id_state, login_col, gr.Column(visible=False)]
            )

        # ---------- 主应用 ----------
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

            # 内容容器（初始显示首页）
            content_col = gr.Column()
            with content_col:
                # 使用 Column 占位，后续更新内容
                page_placeholder = gr.Column(visible=True)
                # 初始化首页
                page_placeholder = render_dashboard(user_id_state)
                # 定义一个函数来更新内容
                def switch_page(page_name, user_id):
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
                        # 复用作品展示
                        with get_db() as db:
                            works = db.execute("SELECT * FROM works WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (user_id,)).fetchall()
                        with gr.Column():
                            if works:
                                for w in works:
                                    gr.Markdown(f"**{w['title']}**  {w['type']}  {w['model']}  {w['created_at']}")
                                    if w['url'] and w['url'].startswith("http"):
                                        gr.HTML(f"<img src='{w['url']}' style='max-width:200px;max-height:200px;'/>")
                            else:
                                gr.Markdown("暂无作品")
                        return
                # 导航点击事件
                nav_home.click(fn=switch_page, inputs=[gr.State("dashboard"), user_id_state], outputs=page_placeholder)
                nav_image.click(fn=switch_page, inputs=[gr.State("image"), user_id_state], outputs=page_placeholder)
                nav_video.click(fn=switch_page, inputs=[gr.State("video"), user_id_state], outputs=page_placeholder)
                nav_music.click(fn=switch_page, inputs=[gr.State("music"), user_id_state], outputs=page_placeholder)
                nav_human.click(fn=switch_page, inputs=[gr.State("human"), user_id_state], outputs=page_placeholder)
                nav_chat.click(fn=switch_page, inputs=[gr.State("chat"), user_id_state], outputs=page_placeholder)
                nav_tasks.click(fn=switch_page, inputs=[gr.State("tasks"), user_id_state], outputs=page_placeholder)
                nav_history.click(fn=switch_page, inputs=[gr.State("history"), user_id_state], outputs=page_placeholder)

            # 退出登录
            def logout():
                return "", {}, None, gr.update(visible=True), gr.update(visible=False)
            logout_btn.click(fn=logout, inputs=[], outputs=[token_state, user_state, user_id_state, login_col, main_col])

    return demo

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
