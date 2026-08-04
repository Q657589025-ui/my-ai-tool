import gradio as gr
import requests
import time
import json
import os
import base64
from datetime import datetime

# ==================== 配置（请替换为你的 Key） ====================
YOUR_API_KEY = "sk-7a0c8f2f854263e38c24f8037e1cb22d828f7545b4016709"
BASE_URL = "https://api.likeadmin.cn/api/v1"

# ==================== 客户端 ====================
class AIGCClient:
    def __init__(self, api_key=YOUR_API_KEY):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=self.headers, params=params)
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
        mime = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".gif": "image/gif", ".webp": "image/webp",
            ".mp4": "video/mp4", ".mov": "video/quicktime", ".avi": "video/x-msvideo"
        }.get(ext, "application/octet-stream")
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"

# ==================== 生成逻辑（统一入口） ====================
def generate_image(prompt, file, resolution, aspect_ratio, model="gpt-image-2", channel="OpenAI"):
    """图片生成"""
    return _generate_async(model, channel, prompt, file, resolution=resolution, aspect_ratio=aspect_ratio)

def generate_video(prompt, file, quality, duration, aspect_ratio, model="veo3.1-fast", channel="xAIQ"):
    return _generate_async(model, channel, prompt, file, quality=quality, duration=duration, aspect_ratio=aspect_ratio)

def generate_music(prompt, style, tempo, model="music_generation", channel="music_gen"):
    return _generate_async(model, channel, prompt, None, style=style, tempo=tempo)

def generate_chat(prompt, temperature, max_tokens, model="qwen3.6-plus", channel="dashscope_compatible"):
    """文本对话（同步）"""
    if not prompt:
        return "⚠️ 请输入问题"
    client = AIGCClient()
    messages = [{"role": "user", "content": prompt}]
    resp = client.chat_completion(model, channel, messages, temperature=temperature, max_tokens=max_tokens)
    if "error" in resp:
        return f"❌ 错误：{resp['error']}"
    choices = resp.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "无回复")
        usage = resp.get("usage", {})
        cost = usage.get("points_cost", 0)
        return f"🤖 {content}\n\n消耗 {cost} 点"
    return "⚠️ 未获取回复"

def generate_digital_human(prompt, expression, model="digital_human", channel="dh_channel"):
    return _generate_async(model, channel, prompt, None, expression=expression)

def generate_more_app(prompt, file, app_name, **kwargs):
    """更多应用（根据选择动态映射）"""
    app_map = {
        "全能视频生成": {"model": "full_video", "channel": "full_video_ch"},
        "seedsvc": {"model": "seedsvc", "channel": "seedsvc_ch"},
        "FlashVSR": {"model": "flashvsr", "channel": "flashvsr_ch"},
        "水印消除": {"model": "watermark_removal", "channel": "wm_ch"},
        "数字人对口型": {"model": "digital_human_lip", "channel": "dh_lip_ch"},
        "dressing-diffusion": {"model": "dressing_diffusion", "channel": "dd_ch"},
        "MMaudio": {"model": "mmaudio", "channel": "mmaudio_ch"},
        "Happy Horse": {"model": "happy_horse", "channel": "hh_ch"},
        "wan": {"model": "wan", "channel": "wan_ch"},
        "智能剪辑": {"model": "smart_edit", "channel": "edit_ch"},
        "人物替换": {"model": "person_swap", "channel": "swap_ch"},
        "动作迁移": {"model": "motion_transfer", "channel": "mt_ch"},
        "全驱动数字人": {"model": "full_digital_human", "channel": "fdh_ch"}
    }
    info = app_map.get(app_name, {"model": "full_video", "channel": "full_video_ch"})
    return _generate_async(info["model"], info["channel"], prompt, file, **kwargs)

def _generate_async(model, channel, prompt, file, **params):
    """异步任务通用处理"""
    if not prompt and file is None:
        return "⚠️ 请输入描述或上传文件"
    client = AIGCClient()
    if file is not None:
        uri = file_to_data_uri(file)
        if uri:
            params["image_urls"] = [uri]
    if prompt:
        params["prompt"] = prompt
    resp = client.create_task(model, channel, **params)
    if "error" in resp:
        return f"❌ 错误：{resp['error']}"
    task_id = resp.get("task_id")
    if not task_id:
        return f"⚠️ 同步返回：{json.dumps(resp, ensure_ascii=False, indent=2)}"
    # 轮询
    start = time.time()
    while time.time() - start < 150:
        status_resp = client.query_task(task_id)
        if "error" in status_resp:
            return f"❌ 查询失败：{status_resp['error']}"
        status = status_resp.get("status")
        if status in ["completed", "success"]:
            result = status_resp.get("result", {})
            usage = status_resp.get("usage", {})
            cost = usage.get("points_cost", 0)
            url = None
            if "images" in result:
                url = result["images"][0].get("url", "")
            elif "video_url" in result:
                url = result["video_url"]
            elif "audio_url" in result:
                url = result["audio_url"]
            else:
                url = json.dumps(result, ensure_ascii=False, indent=2)
            return f"✅ 生成完成！\n链接：{url}\n消耗 {cost} 点"
        elif status in ["failed", "cancelled"]:
            return f"❌ 任务失败：{status_resp.get('msg', '未知错误')}"
        time.sleep(2)
    return "⏰ 超时，请稍后重试"

def get_balance_display():
    client = AIGCClient()
    resp = client.get_balance()
    if "error" in resp:
        return "💰 余额：查询失败"
    return f"💰 余额：{resp.get('available_points', 0):.2f} 点"

# ==================== 自定义 CSS（优化字体、间距、颜色） ====================
custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 1400px;
        margin: auto;
        background: #f8f9fc;
        padding: 20px;
        border-radius: 16px;
    }
    .sidebar {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .main-area {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }
    .gr-button-primary {
        background: #4f46e5 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .gr-button-primary:hover {
        background: #4338ca !important;
    }
    .gr-textbox textarea {
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
        padding: 12px !important;
        font-size: 14px !important;
    }
    .gr-radio label, .gr-dropdown label {
        font-weight: 500 !important;
        color: #1f2937 !important;
    }
    .gr-accordion {
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
    }
    .gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
        color: #111827 !important;
    }
"""

# ==================== 构建主界面（多个 Tab） ====================
def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), css=custom_css, title="AI 创作平台") as demo:
        # 顶部横幅
        gr.Markdown("# 🧠 AI 创作平台")
        with gr.Row():
            balance = gr.Markdown(get_balance_display())
            refresh_btn = gr.Button("🔄 刷新余额", size="sm")
        refresh_btn.click(fn=get_balance_display, outputs=balance)

        # 主要功能 Tabs
        with gr.Tabs():
            # ---------- 1. 图片生成 ----------
            with gr.TabItem("🖼️ 图片生成"):
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_img = gr.Textbox(label="📝 提示词", placeholder="描述你想要的图片...", lines=3)
                        file_img = gr.File(label="📎 参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
                        with gr.Row():
                            res_img = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k")
                            ratio_img = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1")
                        btn_img = gr.Button("🚀 生成", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_img = gr.Markdown(label="✨ 结果", value="等待生成...")
                btn_img.click(
                    fn=generate_image,
                    inputs=[prompt_img, file_img, res_img, ratio_img],
                    outputs=output_img
                )

            # ---------- 2. 视频生成 ----------
            with gr.TabItem("🎬 视频生成"):
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_vid = gr.Textbox(label="📝 提示词", placeholder="描述你想要的视频...", lines=3)
                        file_vid = gr.File(label="📎 参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
                        with gr.Row():
                            quality_vid = gr.Radio(["720p", "1080p", "4k"], label="清晰度", value="720p")
                            dur_vid = gr.Slider(4, 30, value=8, step=2, label="时长(秒)")
                            ratio_vid = gr.Radio(["16:9", "9:16"], label="比例", value="16:9")
                        btn_vid = gr.Button("🚀 生成", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_vid = gr.Markdown(label="✨ 结果", value="等待生成...")
                btn_vid.click(
                    fn=generate_video,
                    inputs=[prompt_vid, file_vid, quality_vid, dur_vid, ratio_vid],
                    outputs=output_vid
                )

            # ---------- 3. 音乐生成 ----------
            with gr.TabItem("🎵 音乐生成"):
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_mus = gr.Textbox(label="📝 描述", placeholder="描述你想要的音乐...", lines=3)
                        with gr.Row():
                            style_mus = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop")
                            tempo_mus = gr.Slider(60, 180, value=120, step=5, label="速度(BPM)")
                        btn_mus = gr.Button("🚀 生成", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_mus = gr.Markdown(label="✨ 结果", value="等待生成...")
                btn_mus.click(
                    fn=generate_music,
                    inputs=[prompt_mus, style_mus, tempo_mus],
                    outputs=output_mus
                )

            # ---------- 4. 文本对话 ----------
            with gr.TabItem("💬 文本对话"):
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_chat = gr.Textbox(label="💬 问题", placeholder="输入你的问题...", lines=3)
                        with gr.Row():
                            temp_chat = gr.Slider(0, 2, value=0.7, step=0.1, label="创意度")
                            max_tokens_chat = gr.Slider(256, 4096, value=2048, step=256, label="最大回复长度")
                        btn_chat = gr.Button("🚀 发送", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_chat = gr.Markdown(label="✨ 回复", value="等待回复...")
                btn_chat.click(
                    fn=generate_chat,
                    inputs=[prompt_chat, temp_chat, max_tokens_chat],
                    outputs=output_chat
                )

            # ---------- 5. 数字人 ----------
            with gr.TabItem("🧑‍🎤 数字人"):
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_dh = gr.Textbox(label="📝 脚本", placeholder="输入数字人要说的话...", lines=3)
                        expr_dh = gr.Radio(["neutral", "happy", "sad", "surprised"], label="表情", value="neutral")
                        btn_dh = gr.Button("🚀 生成", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_dh = gr.Markdown(label="✨ 结果", value="等待生成...")
                btn_dh.click(
                    fn=generate_digital_human,
                    inputs=[prompt_dh, expr_dh],
                    outputs=output_dh
                )

            # ---------- 6. 更多应用 ----------
            with gr.TabItem("✨ 更多"):
                gr.Markdown("### 选择特定应用（覆盖 14 种能力）")
                with gr.Row():
                    with gr.Column(scale=2):
                        prompt_more = gr.Textbox(label="📝 描述", placeholder="描述你的需求...", lines=3)
                        file_more = gr.File(label="📎 参考文件（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"])
                        app_selector = gr.Dropdown(
                            choices=[
                                "全能视频生成", "seedsvc", "FlashVSR", "水印消除", "数字人对口型",
                                "dressing-diffusion", "MMaudio", "Happy Horse", "wan", "智能剪辑",
                                "人物替换", "动作迁移", "全驱动数字人"
                            ],
                            label="选择应用",
                            value="全能视频生成"
                        )
                        # 额外参数（根据应用可选）
                        with gr.Accordion("高级参数（可选）", open=False):
                            extra_res = gr.Textbox(label="分辨率（可选）", placeholder="如 1k, 2k, 4k")
                            extra_ratio = gr.Textbox(label="比例（可选）", placeholder="如 16:9, 1:1")
                            extra_duration = gr.Number(label="时长（可选）", value=8)
                        btn_more = gr.Button("🚀 生成", variant="primary", size="lg")
                    with gr.Column(scale=2):
                        output_more = gr.Markdown(label="✨ 结果", value="等待生成...")
                # 处理更多应用生成（将额外参数传递）
                def more_app_wrapper(prompt, file, app, res, ratio, dur):
                    params = {}
                    if res:
                        params["resolution"] = res
                    if ratio:
                        params["aspect_ratio"] = ratio
                    if dur:
                        params["duration"] = dur
                    return generate_more_app(prompt, file, app, **params)
                btn_more.click(
                    fn=more_app_wrapper,
                    inputs=[prompt_more, file_more, app_selector, extra_res, extra_ratio, extra_duration],
                    outputs=output_more
                )

        # 底部历史记录（所有 Tab 共用）
        gr.Markdown("---")
        gr.Markdown("### 📜 全局历史记录")
        history_display = gr.Markdown("暂无记录")
        refresh_hist_btn = gr.Button("刷新历史", size="sm")
        # 历史记录更新函数（需要收集所有生成结果，为简化，此处仅示意）
        def get_history():
            # 实际可收集全局变量，但为了演示，返回静态
            return "历史记录功能开发中..."
        refresh_hist_btn.click(fn=get_history, outputs=history_display)

    return demo

# ==================== 启动 ====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
