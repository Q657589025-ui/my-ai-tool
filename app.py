import gradio as gr
import requests
import time
import json
import os
import base64

# ==================== 配置（请替换为你重置后的 Key） ====================
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
    """将上传的文件转换为 data URI（支持图片和视频）"""
    if file_obj is None:
        return None
    # file_obj 是临时文件路径
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

# ==================== 功能配置（模型、渠道、默认参数） ====================
# 每个功能对应一个默认模型和渠道，并提供可选的参数配置
FEATURES = {
    "图片生成": {
        "model": "gpt-image-2",
        "channel": "OpenAI",
        "params": {
            "分辨率": {"type": "radio", "options": ["1k", "2k", "4k"], "default": "1k"},
            "比例": {"type": "radio", "options": ["1:1", "16:9", "9:16", "4:3", "3:4"], "default": "1:1"}
        },
        "supports_image": True,
        "api_params_map": {"resolution": "resolution", "aspect_ratio": "aspect_ratio"}
    },
    "视频生成": {
        "model": "veo3.1-fast",
        "channel": "xAIQ",
        "params": {
            "清晰度": {"type": "radio", "options": ["720p", "1080p", "4k"], "default": "720p"},
            "时长(秒)": {"type": "slider", "min": 4, "max": 30, "step": 2, "default": 8},
            "比例": {"type": "radio", "options": ["16:9", "9:16"], "default": "16:9"}
        },
        "supports_image": True,
        "api_params_map": {"quality": "quality", "duration": "duration", "aspect_ratio": "aspect_ratio"}
    },
    "音乐生成": {
        "model": "music_generation",
        "channel": "music_gen",
        "params": {
            "风格": {"type": "radio", "options": ["pop", "jazz", "classical", "rock", "electronic"], "default": "pop"},
            "速度(BPM)": {"type": "slider", "min": 60, "max": 180, "step": 5, "default": 120}
        },
        "supports_image": False,
        "api_params_map": {"style": "style", "tempo": "tempo"}
    },
    "文本对话": {
        "model": "qwen3.6-plus",
        "channel": "dashscope_compatible",
        "params": {
            "创意度": {"type": "slider", "min": 0, "max": 2, "step": 0.1, "default": 0.7},
            "最大长度": {"type": "slider", "min": 256, "max": 4096, "step": 256, "default": 2048}
        },
        "supports_image": False,
        "api_params_map": {"temperature": "temperature", "max_tokens": "max_tokens"}
    },
    "数字人": {
        "model": "digital_human",
        "channel": "dh_channel",
        "params": {
            "表情": {"type": "radio", "options": ["neutral", "happy", "sad", "surprised"], "default": "neutral"}
        },
        "supports_image": False,
        "api_params_map": {"expression": "expression"}
    },
    "更多应用": {
        "model": "full_video",
        "channel": "full_video_ch",
        "params": {
            "应用类型": {"type": "dropdown", "options": ["全能视频生成", "seedsvc", "FlashVSR", "水印消除", "数字人对口型", "dressing-diffusion", "MMaudio", "Happy Horse", "wan", "智能剪辑", "人物替换", "动作迁移", "全驱动数字人"], "default": "全能视频生成"}
        },
        "supports_image": True,
        "supports_video": True,
        "api_params_map": {}
    }
}

# ==================== 核心生成函数 ====================
def generate(feature, prompt, file, *param_values):
    """生成逻辑"""
    if not prompt.strip() and file is None:
        return "⚠️ 请输入描述或上传文件"
    feat = FEATURES.get(feature)
    if not feat:
        return "⚠️ 功能未定义"
    model = feat["model"]
    channel = feat["channel"]
    # 处理文件
    image_urls = None
    if file is not None:
        uri = file_to_data_uri(file)
        if uri:
            image_urls = [uri]  # 有的接口支持数组，有的只支持单张，这里使用数组，接口会处理
    # 构建业务参数
    params = {}
    # 将 param_values 与 api_params_map 对应
    param_keys = list(feat["params"].keys())
    for i, key in enumerate(param_keys):
        if i < len(param_values):
            val = param_values[i]
            if val is not None:
                api_key = feat["api_params_map"].get(key, key)
                params[api_key] = val
    # 添加 prompt 和 image_urls
    if prompt:
        params["prompt"] = prompt
    if image_urls:
        params["image_urls"] = image_urls  # 或者 urls，根据接口文档，但多数接受 image_urls
    # 如果是“更多应用”，需要根据选择的子应用调整 model 和 channel
    if feature == "更多应用":
        sub_app = params.get("应用类型", "全能视频生成")
        # 根据子应用映射到真实 model 和 channel（这里需要映射，但事实未提供，我们使用默认）
        # 为简化，我们用预设映射
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
        mapping = app_map.get(sub_app, {"model": "full_video", "channel": "full_video_ch"})
        model = mapping["model"]
        channel = mapping["channel"]
        # 移除“应用类型”参数，因为它不是业务参数
        del params["应用类型"]

    client = AIGCClient()
    # 判断是否是文本对话（同步）
    if feature == "文本对话":
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return f"❌ 错误：{resp['error']}"
        choices = resp.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "无回复")
            usage = resp.get("usage", {})
            cost = usage.get("points_cost", 0)
            return f"🤖 {content}\n\n消耗 {cost} 点"
        return "⚠️ 未获取回复"
    else:
        # 异步任务
        resp = client.create_task(model, channel, **params)
        if "error" in resp:
            return f"❌ 错误：{resp['error']}"
        task_id = resp.get("task_id")
        if not task_id:
            return f"⚠️ 同步返回：{json.dumps(resp, ensure_ascii=False, indent=2)}"
        # 轮询
        start = time.time()
        while time.time() - start < 120:
            status_resp = client.query_task(task_id)
            if "error" in status_resp:
                return f"❌ 查询失败：{status_resp['error']}"
            status = status_resp.get("status")
            if status in ["completed", "success"]:
                result = status_resp.get("result", {})
                usage = status_resp.get("usage", {})
                cost = usage.get("points_cost", 0)
                # 提取链接
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
        return "⏰ 超时，请稍后查询"

# ==================== 构建界面 ====================
def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), title="AI 创作助手", css="""
        .gradio-container { max-width: 800px; margin: auto; }
        .tab-nav { margin-bottom: 10px; }
    """) as demo:
        gr.Markdown("# 🎨 AI 创作助手")
        with gr.Row():
            balance_display = gr.Markdown(get_balance())
            refresh_btn = gr.Button("🔄 刷新余额", size="sm")
        refresh_btn.click(fn=get_balance, outputs=balance_display)

        # 使用 Tabs 实现功能切换
        with gr.Tabs():
            # ---------- 图片生成 ----------
            with gr.TabItem("🖼️ 图片"):
                with gr.Row():
                    prompt_img = gr.Textbox(label="描述", placeholder="例如：一只猫，4k，16:9", lines=2, scale=2)
                with gr.Row():
                    file_img = gr.File(label="上传参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
                with gr.Row():
                    res_img = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k")
                    ratio_img = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1")
                btn_img = gr.Button("生成", variant="primary", size="lg")
                output_img = gr.Markdown(label="结果")
                btn_img.click(
                    fn=lambda p, f, r, a: generate("图片生成", p, f, r, a),
                    inputs=[prompt_img, file_img, res_img, ratio_img],
                    outputs=output_img
                )

            # ---------- 视频生成 ----------
            with gr.TabItem("🎬 视频"):
                with gr.Row():
                    prompt_vid = gr.Textbox(label="描述", placeholder="例如：一只狗在沙滩奔跑", lines=2, scale=2)
                with gr.Row():
                    file_vid = gr.File(label="上传参考图（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp"])
                with gr.Row():
                    quality_vid = gr.Radio(["720p", "1080p", "4k"], label="清晰度", value="720p")
                    dur_vid = gr.Slider(4, 30, value=8, step=2, label="时长(秒)")
                    ratio_vid = gr.Radio(["16:9", "9:16"], label="比例", value="16:9")
                btn_vid = gr.Button("生成", variant="primary", size="lg")
                output_vid = gr.Markdown(label="结果")
                btn_vid.click(
                    fn=lambda p, f, q, d, r: generate("视频生成", p, f, q, d, r),
                    inputs=[prompt_vid, file_vid, quality_vid, dur_vid, ratio_vid],
                    outputs=output_vid
                )

            # ---------- 音乐生成 ----------
            with gr.TabItem("🎵 音乐"):
                with gr.Row():
                    prompt_mus = gr.Textbox(label="描述", placeholder="例如：欢快的流行歌曲", lines=2, scale=2)
                with gr.Row():
                    style_mus = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop")
                    tempo_mus = gr.Slider(60, 180, value=120, step=5, label="速度(BPM)")
                btn_mus = gr.Button("生成", variant="primary", size="lg")
                output_mus = gr.Markdown(label="结果")
                btn_mus.click(
                    fn=lambda p, s, t: generate("音乐生成", p, None, s, t),
                    inputs=[prompt_mus, style_mus, tempo_mus],
                    outputs=output_mus
                )

            # ---------- 文本对话 ----------
            with gr.TabItem("💬 对话"):
                with gr.Row():
                    prompt_chat = gr.Textbox(label="问题", placeholder="问点什么...", lines=2, scale=2)
                with gr.Row():
                    temp_chat = gr.Slider(0, 2, value=0.7, step=0.1, label="创意度")
                    max_tokens_chat = gr.Slider(256, 4096, value=2048, step=256, label="最大回复长度")
                btn_chat = gr.Button("发送", variant="primary", size="lg")
                output_chat = gr.Markdown(label="回复")
                btn_chat.click(
                    fn=lambda p, t, m: generate("文本对话", p, None, t, m),
                    inputs=[prompt_chat, temp_chat, max_tokens_chat],
                    outputs=output_chat
                )

            # ---------- 数字人 ----------
            with gr.TabItem("🧑‍🎤 数字人"):
                with gr.Row():
                    prompt_dh = gr.Textbox(label="描述", placeholder="例如：说一段欢迎词", lines=2, scale=2)
                with gr.Row():
                    expr_dh = gr.Radio(["neutral", "happy", "sad", "surprised"], label="表情", value="neutral")
                btn_dh = gr.Button("生成", variant="primary", size="lg")
                output_dh = gr.Markdown(label="结果")
                btn_dh.click(
                    fn=lambda p, e: generate("数字人", p, None, e),
                    inputs=[prompt_dh, expr_dh],
                    outputs=output_dh
                )

            # ---------- 更多应用 ----------
            with gr.TabItem("✨ 更多"):
                with gr.Row():
                    prompt_more = gr.Textbox(label="描述", placeholder="描述你的需求...", lines=2, scale=2)
                with gr.Row():
                    file_more = gr.File(label="上传参考文件（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"])
                with gr.Row():
                    sub_app = gr.Dropdown(
                        choices=["全能视频生成", "seedsvc", "FlashVSR", "水印消除", "数字人对口型",
                                 "dressing-diffusion", "MMaudio", "Happy Horse", "wan", "智能剪辑",
                                 "人物替换", "动作迁移", "全驱动数字人"],
                        label="选择具体应用",
                        value="全能视频生成"
                    )
                btn_more = gr.Button("生成", variant="primary", size="lg")
                output_more = gr.Markdown(label="结果")
                btn_more.click(
                    fn=lambda p, f, app: generate("更多应用", p, f, app),
                    inputs=[prompt_more, file_more, sub_app],
                    outputs=output_more
                )

    return demo

# ==================== 启动 ====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
