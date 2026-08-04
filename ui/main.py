import gradio as gr
import requests
import time
import json
import os
import threading
import hashlib
import base64
from datetime import datetime
from core.database import get_db, Task, Work
from core.auth import get_user_points, update_user_points
from core.config import API_KEY, BASE_URL, OUTPUT_DIR   # ✅ 不再导入 MODEL_CONFIG

# ==================== 加载模型配置（在文件内部） ====================
with open("config/models.json", "r") as f:
    MODEL_CONFIG = json.load(f)

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
        mime = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp",
            ".mp4": "video/mp4", ".mov": "video/quicktime"
        }.get(ext, "application/octet-stream")
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

# ==================== 价格与任务 ====================
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
                    work = Work(
                        user_id=user_id,
                        type="chat",
                        title=prompt[:20],
                        prompt=prompt,
                        model=model,
                        url=content,
                        created_at=datetime.utcnow()
                    )
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
            task = Task(
                task_id=task_id,
                user_id=user_id,
                type=task_type,
                model=model,
                prompt=prompt,
                status="waiting",
                progress=0,
                created_at=datetime.utcnow()
            )
            db.add(task)
            db.commit()
        if update_user_points(user_id, -get_cost(task_type, params)):
            threading.Thread(target=worker.poll_task, args=(task_id, user_id), daemon=True).start()
            return {"task_id": task_id, "cost": get_cost(task_type, params)}, None
        else:
            return None, "扣费失败"

# ==================== 获取模型配置 ====================
def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

# ==================== UI 渲染函数（完整）====================
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
