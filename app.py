import gradio as gr
import requests
import time
import json
import os
import sqlite3
import base64
from datetime import datetime

# ==================== 配置 ====================
API_KEY = os.getenv("AIGC_API_KEY", "sk-7a0c8f2f854263e38c24f8037e1cb22d828f7545b4016709")
BASE_URL = "https://api.likeadmin.cn/api/v1"
DB_PATH = "database/studio.db"

# ==================== 数据库 ====================
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            type TEXT,
            model TEXT,
            prompt TEXT,
            status TEXT,
            progress INTEGER,
            result TEXT,
            cost REAL,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            prompt TEXT,
            model TEXT,
            url TEXT,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            points INTEGER DEFAULT 10000
        )
    ''')
    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute("INSERT INTO users (points) VALUES (10000)")
    conn.commit()
    conn.close()

def get_points():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT points FROM users LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row["points"] if row else 10000

def deduct_points(amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET points = points - ? WHERE points >= ?", (amount, amount))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def save_task(task_id, task_type, model, prompt):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (task_id, type, model, prompt, status, progress, created_at) VALUES (?,?,?,?,?,?,?)",
        (task_id, task_type, model, prompt, "waiting", 0, datetime.now())
    )
    conn.commit()
    conn.close()

def update_task(task_id, status=None, progress=None, result=None, cost=None):
    conn = get_db()
    c = conn.cursor()
    fields, vals = [], []
    if status is not None:
        fields.append("status=?"); vals.append(status)
    if progress is not None:
        fields.append("progress=?"); vals.append(progress)
    if result is not None:
        fields.append("result=?"); vals.append(json.dumps(result))
    if cost is not None:
        fields.append("cost=?"); vals.append(cost)
    if fields:
        vals.append(task_id)
        c.execute(f"UPDATE tasks SET {','.join(fields)} WHERE task_id=?", vals)
        conn.commit()
    conn.close()

def save_work(work_type, title, prompt, model, url):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO works (type, title, prompt, model, url, created_at) VALUES (?,?,?,?,?,?)",
        (work_type, title, prompt, model, url, datetime.now())
    )
    conn.commit()
    conn.close()

def get_works(limit=20):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM works ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==================== API 客户端 ====================
class AIGCClient:
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

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

    def get_balance(self):
        return self._request("GET", "/user/balance")

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

def load_model_config(category, name):
    with open("config/models.json", "r") as f:
        models = json.load(f)
    return models.get(category, {}).get(name, {})

# ==================== 任务管理 ====================
PRICE_MAP = {
    "image": 10,
    "video_720p": 100,
    "video_1080p": 200,
    "video_4k": 400,
    "music": 50,
    "human": 300,
    "chat": 5
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

def submit_task(task_type, model, channel, prompt, file, **params):
    cost = get_cost(task_type, params)
    if get_points() < cost:
        return None, "余额不足，请充值"
    client = AIGCClient()
    if task_type == "chat":
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return None, resp["error"]
        if deduct_points(cost):
            choices = resp.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                save_work("chat", prompt[:20], prompt, model, content)
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
        save_task(task_id, task_type, model, prompt)
        if not deduct_points(cost):
            return None, "扣费失败"
        # 轮询结果（简单同步轮询，会阻塞界面，但演示够用）
        start = time.time()
        while time.time() - start < 150:
            status_resp = client.query_task(task_id)
            if "error" in status_resp:
                update_task(task_id, status="failed")
                return None, status_resp["error"]
            status = status_resp.get("status")
            progress = 50 if status == "processing" else 100 if status in ["completed", "success"] else 0
            update_task(task_id, status=status, progress=progress)
            if status in ["completed", "success"]:
                result = status_resp.get("result", {})
                cost_used = status_resp.get("usage", {}).get("points_cost", 0)
                update_task(task_id, status="completed", result=result, cost=cost_used)
                # 保存作品
                url = None
                if "images" in result:
                    url = result["images"][0].get("url", "")
                elif "video_url" in result:
                    url = result["video_url"]
                elif "audio_url" in result:
                    url = result["audio_url"]
                if url:
                    save_work(task_type, prompt[:20], prompt, model, url)
                return {"result": result, "url": url, "cost": cost_used}, None
            elif status in ["failed", "cancelled"]:
                update_task(task_id, status="failed")
                return None, status_resp.get("msg", "未知错误")
            time.sleep(2)
        update_task(task_id, status="timeout")
        return None, "超时"

# ==================== UI 模块 ====================
def create_dashboard():
    points = get_points()
    works = get_works(5)
    with gr.Column(elem_classes="dashboard"):
        gr.Markdown(f"## 💰 余额：{points} 点")
        gr.Markdown("### 📊 今日统计（示例）")
        with gr.Row():
            gr.Markdown("🎨 图片：23")
            gr.Markdown("🎬 视频：8")
            gr.Markdown("🧑 数字人：4")
        gr.Markdown("### 🚀 快速创作")
        with gr.Row():
            btn_img = gr.Button("🖼️ 图片生成", variant="secondary", size="lg")
            btn_vid = gr.Button("🎬 视频生成", variant="secondary", size="lg")
            btn_music = gr.Button("🎵 音乐生成", variant="secondary", size="lg")
            btn_human = gr.Button("🧑 数字人", variant="secondary", size="lg")
        gr.Markdown("### 📂 最近作品")
        if works:
            for w in works[:5]:
                with gr.Row():
                    gr.Markdown(f"**{w['title']}**  {w['type']}  {w['model']}  {w['created_at']}")
        else:
            gr.Markdown("暂无作品")
    return btn_img, btn_vid, btn_music, btn_human

def create_image_ui():
    with gr.Column():
        gr.Markdown("## 🖼️ 图片创作")
        model_sel = gr.Dropdown(
            choices=list(load_model_config("image", "").keys()) if False else ["GPT Image 2", "GPT Image 2 Pro", "GPT Image 2 Fast", "Nano-Banana Pro", "Nano-Banana 2"],
            label="选择模型",
            value="GPT Image 2"
        )
        prompt = gr.Textbox(label="描述", placeholder="输入图片描述...", lines=3)
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
        with gr.Row():
            resolution = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k")
            aspect = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1")
        btn = gr.Button("🚀 生成", variant="primary")
        output = gr.Image(label="生成结果", interactive=False)
        status = gr.Markdown("等待生成...")
        task_state = gr.State("")

        def generate(model_name, prompt, file, res, ratio):
            config = load_model_config("image", model_name)
            if not config:
                return None, "❌ 模型配置未找到", ""
            result, error = submit_task("image", config["model"], config["channel"], prompt, file,
                                         resolution=res, aspect_ratio=ratio)
            if error:
                return None, f"❌ {error}", ""
            if result and "url" in result:
                # 由于Gradio Image组件需要本地文件，我们无法直接显示URL，这里展示链接
                return None, f"✅ 生成完成！\n[点击查看]({result['url']})", ""
            return None, "⚠️ 未知结果", ""

        btn.click(generate, [model_sel, prompt, file, resolution, aspect], [output, status, task_state])
    return

def create_video_ui():
    with gr.Column():
        gr.Markdown("## 🎬 视频创作")
        model_sel = gr.Dropdown(
            choices=["VEO 3.1 Pro", "VEO 3.1 Fast", "Grok Video", "H3 Video"],
            label="选择模型",
            value="VEO 3.1 Fast"
        )
        prompt = gr.Textbox(label="描述", placeholder="输入视频描述...", lines=3)
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
        with gr.Row():
            quality = gr.Radio(["720p", "1080p", "4k"], label="清晰度", value="720p")
            duration = gr.Slider(4, 30, value=8, step=2, label="时长(秒)")
            ratio = gr.Radio(["16:9", "9:16"], label="比例", value="16:9")
        btn = gr.Button("🚀 生成", variant="primary")
        output = gr.Video(label="生成结果", interactive=False)
        status = gr.Markdown("等待生成...")

        def generate(model_name, prompt, file, quality, duration, ratio):
            config = load_model_config("video", model_name)
            if not config:
                return None, "❌ 模型配置未找到"
            result, error = submit_task("video", config["model"], config["channel"], prompt, file,
                                         quality=quality, duration=duration, aspect_ratio=ratio)
            if error:
                return None, f"❌ {error}"
            if result and "url" in result:
                # 返回视频URL（Gradio Video组件也支持URL）
                return result["url"], f"✅ 生成完成！消耗 {result.get('cost',0)} 点"
            return None, "⚠️ 未知结果"

        btn.click(generate, [model_sel, prompt, file, quality, duration, ratio], [output, status])
    return

def create_music_ui():
    with gr.Column():
        gr.Markdown("## 🎵 音乐生成")
        prompt = gr.Textbox(label="描述", placeholder="输入音乐描述...", lines=3)
        with gr.Row():
            style = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop")
            tempo = gr.Slider(60, 180, value=120, step=5, label="速度(BPM)")
        btn = gr.Button("🚀 生成", variant="primary")
        output = gr.Audio(label="生成结果", interactive=False)
        status = gr.Markdown("等待生成...")

        def generate(prompt, style, tempo):
            config = load_model_config("music", "Music Generation")
            if not config:
                return None, "❌ 模型配置未找到"
            result, error = submit_task("music", config["model"], config["channel"], prompt, None,
                                         style=style, tempo=tempo)
            if error:
                return None, f"❌ {error}"
            if result and "url" in result:
                return result["url"], f"✅ 生成完成！消耗 {result.get('cost',0)} 点"
            return None, "⚠️ 未知结果"

        btn.click(generate, [prompt, style, tempo], [output, status])
    return

def create_human_ui():
    with gr.Column():
        gr.Markdown("## 🧑 数字人")
        prompt = gr.Textbox(label="脚本", placeholder="输入数字人要说的话...", lines=3)
        expr = gr.Radio(["neutral", "happy", "sad", "surprised"], label="表情", value="neutral")
        btn = gr.Button("🚀 生成", variant="primary")
        output = gr.Video(label="生成结果", interactive=False)
        status = gr.Markdown("等待生成...")

        def generate(prompt, expr):
            config = load_model_config("human", "Digital Human")
            if not config:
                return None, "❌ 模型配置未找到"
            result, error = submit_task("human", config["model"], config["channel"], prompt, None,
                                         expression=expr)
            if error:
                return None, f"❌ {error}"
            if result and "url" in result:
                return result["url"], f"✅ 生成完成！消耗 {result.get('cost',0)} 点"
            return None, "⚠️ 未知结果"

        btn.click(generate, [prompt, expr], [output, status])
    return

def create_chat_ui():
    with gr.Column():
        gr.Markdown("## 🤖 AI 助手")
        prompt = gr.Textbox(label="问题", placeholder="输入你的问题...", lines=3)
        with gr.Row():
            temp = gr.Slider(0, 2, value=0.7, step=0.1, label="创意度")
            max_tokens = gr.Slider(256, 4096, value=2048, step=256, label="最大回复长度")
        btn = gr.Button("🚀 发送", variant="primary")
        output = gr.Markdown(label="回复")

        def generate(prompt, temp, max_tokens):
            config = load_model_config("chat", "Qwen3.6-Plus")
            if not config:
                return "❌ 模型配置未找到"
            result, error = submit_task("chat", config["model"], config["channel"], prompt, None,
                                         temperature=temp, max_tokens=max_tokens)
            if error:
                return f"❌ {error}"
            if result and "choices" in result:
                content = result["choices"][0].get("message", {}).get("content", "无回复")
                return f"🤖 {content}"
            return "⚠️ 未知回复"

        btn.click(generate, [prompt, temp, max_tokens], output)
    return

def create_history_ui():
    with gr.Column():
        gr.Markdown("## 📂 我的作品")
        works = get_works(50)
        if works:
            for w in works:
                with gr.Row():
                    gr.Markdown(f"**{w['title']}**  {w['type']}  {w['model']}  {w['created_at']}")
                    if w['url'] and w['url'].startswith("http"):
                        gr.Markdown(f"[查看]({w['url']})")
        else:
            gr.Markdown("暂无作品")
    return

# ==================== 主界面（左侧导航 + 右侧内容） ====================
def build_app():
    init_db()
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio v2.0", css="""
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .gradio-container { font-family: 'Inter', sans-serif; max-width: 1400px; margin: auto; padding: 20px; }
        .sidebar { background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .main-area { background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .gr-button-primary { background: #4f46e5 !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
        .gr-button-primary:hover { background: #4338ca !important; }
        .gr-textbox textarea { border-radius: 8px !important; border: 1px solid #e5e7eb !important; padding: 12px !important; }
    """) as demo:
        gr.Markdown("# 🧠 AI Studio v2.0")

        with gr.Row(equal_height=False):
            # 左侧导航
            with gr.Column(scale=1, elem_classes="sidebar"):
                gr.Markdown("### 🧭 导航")
                nav_home = gr.Button("🏠 首页", variant="secondary", size="lg")
                nav_image = gr.Button("🎨 图片创作", variant="secondary", size="lg")
                nav_video = gr.Button("🎬 视频创作", variant="secondary", size="lg")
                nav_music = gr.Button("🎵 音乐生成", variant="secondary", size="lg")
                nav_human = gr.Button("🧑 数字人", variant="secondary", size="lg")
                nav_chat = gr.Button("🤖 AI助手", variant="secondary", size="lg")
                nav_history = gr.Button("📂 我的作品", variant="secondary", size="lg")
                # 余额显示
                balance = gr.Markdown(f"💰 余额：{get_points()} 点")
                refresh_btn = gr.Button("🔄 刷新余额", size="sm")
                refresh_btn.click(fn=lambda: f"💰 余额：{get_points()} 点", outputs=balance)

            # 右侧内容区域（动态切换）
            with gr.Column(scale=4, elem_classes="main-area"):
                content = gr.Column(visible=True)
                # 默认显示 Dashboard
                with gr.Column(visible=True) as dashboard_col:
                    btn_img, btn_vid, btn_music, btn_human = create_dashboard()
                # 其他页面初始隐藏
                image_col = gr.Column(visible=False)
                video_col = gr.Column(visible=False)
                music_col = gr.Column(visible=False)
                human_col = gr.Column(visible=False)
                chat_col = gr.Column(visible=False)
                history_col = gr.Column(visible=False)

                # 填充各页面内容（先创建但隐藏）
                with image_col:
                    create_image_ui()
                with video_col:
                    create_video_ui()
                with music_col:
                    create_music_ui()
                with human_col:
                    create_human_ui()
                with chat_col:
                    create_chat_ui()
                with history_col:
                    create_history_ui()

                # 导航点击切换可见性
                def show_page(target):
                    return {dashboard_col: gr.update(visible=target=="dashboard"),
                            image_col: gr.update(visible=target=="image"),
                            video_col: gr.update(visible=target=="video"),
                            music_col: gr.update(visible=target=="music"),
                            human_col: gr.update(visible=target=="human"),
                            chat_col: gr.update(visible=target=="chat"),
                            history_col: gr.update(visible=target=="history")}

                nav_home.click(fn=lambda: show_page("dashboard"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_image.click(fn=lambda: show_page("image"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_video.click(fn=lambda: show_page("video"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_music.click(fn=lambda: show_page("music"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_human.click(fn=lambda: show_page("human"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_chat.click(fn=lambda: show_page("chat"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                nav_history.click(fn=lambda: show_page("history"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                # 从 Dashboard 快速按钮跳转
                btn_img.click(fn=lambda: show_page("image"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                btn_vid.click(fn=lambda: show_page("video"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                btn_music.click(fn=lambda: show_page("music"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])
                btn_human.click(fn=lambda: show_page("human"), outputs=[dashboard_col, image_col, video_col, music_col, human_col, chat_col, history_col])

    return demo

# ==================== 启动 ====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
