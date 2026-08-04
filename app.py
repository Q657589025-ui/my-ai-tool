import gradio as gr
import requests
import time
import json
import os
import base64
from datetime import datetime

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

# ==================== 模型数据库 ====================
MODELS = {
    "文本": {
        "qwen3.6-plus": {
            "label": "Qwen3.6-Plus",
            "channel": "dashscope_compatible",
            "params": [
                {"key": "temperature", "label": "温度", "type": "slider", "min": 0, "max": 2, "default": 0.7},
                {"key": "max_tokens", "label": "最大输出", "type": "slider", "min": 256, "max": 4096, "default": 2048, "step": 256},
                {"key": "top_p", "label": "Top P", "type": "slider", "min": 0, "max": 1, "default": 0.9},
                {"key": "enable_search", "label": "联网搜索", "type": "checkbox", "default": False},
                {"key": "enable_thinking", "label": "深度思考", "type": "checkbox", "default": False}
            ]
        }
    },
    "图片": {
        "gpt-image-2": {
            "label": "GPT Image 2",
            "channel": "OpenAI",
            "params": [
                {"key": "resolution", "label": "分辨率", "type": "radio", "options": ["1k", "2k", "4k"], "default": "1k"},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["1:1", "16:9", "9:16", "4:3", "3:4"], "default": "1:1"},
                {"key": "n", "label": "生成张数", "type": "number", "default": 1, "min": 1, "max": 1, "step": 1}
            ],
            "supports_image": True
        },
        "gpt-image-2-pro": {
            "label": "GPT Image 2 Pro",
            "channel": "OpenaiM",
            "params": [
                {"key": "image_size", "label": "分辨率", "type": "radio", "options": ["1k", "2k", "4k"], "default": "1k"},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["1:1", "16:9", "9:16", "4:3", "3:4"], "default": "1:1"},
                {"key": "mask_url", "label": "遮罩图URL", "type": "text", "default": ""}
            ],
            "supports_image": True
        },
        "gpt-image-2-fast": {
            "label": "GPT Image 2 Fast",
            "channel": "openaiD",
            "params": [
                {"key": "image_size", "label": "分辨率", "type": "radio", "options": ["1k", "2k", "4k"], "default": "1k"},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["auto", "1:1", "16:9", "9:16", "4:3", "3:4"], "default": "auto"},
                {"key": "quality", "label": "质量", "type": "radio", "options": ["low", "medium", "high"], "default": "medium"}
            ],
            "supports_image": True
        },
        "nano-banana-pro": {
            "label": "Nano-Banana Pro",
            "channel": "Google",
            "params": [
                {"key": "image_size", "label": "分辨率", "type": "radio", "options": ["1K", "2K", "4K"], "default": "1K"},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"], "default": "1:1"}
            ],
            "supports_image": True
        },
        "nano-banana-2": {
            "label": "Nano-Banana 2",
            "channel": "Google",
            "params": [
                {"key": "image_size", "label": "分辨率", "type": "radio", "options": ["1K", "2K", "4K"], "default": "1K"},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"], "default": "1:1"}
            ],
            "supports_image": True
        }
    },
    "视频": {
        "veo3.1-pro": {
            "label": "VEO 3.1 Pro",
            "channel": "xAIQ",
            "params": [
                {"key": "quality", "label": "清晰度", "type": "radio", "options": ["720p", "1080p", "4k"], "default": "720p"},
                {"key": "duration", "label": "时长(秒)", "type": "slider", "min": 4, "max": 8, "default": 8, "step": 2},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["16:9", "9:16"], "default": "16:9"},
                {"key": "generation_type", "label": "模式", "type": "radio", "options": ["TEXT", "FIRST&LAST", "REFERENCE"], "default": "TEXT"}
            ],
            "supports_image": True
        },
        "veo3.1-fast": {
            "label": "VEO 3.1 Fast",
            "channel": "xAIQ",
            "params": [
                {"key": "quality", "label": "清晰度", "type": "radio", "options": ["720p", "1080p", "4k"], "default": "720p"},
                {"key": "duration", "label": "时长(秒)", "type": "slider", "min": 4, "max": 8, "default": 8, "step": 2},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["16:9", "9:16"], "default": "16:9"},
                {"key": "generation_type", "label": "模式", "type": "radio", "options": ["TEXT", "FIRST&LAST", "REFERENCE"], "default": "TEXT"}
            ],
            "supports_image": True
        },
        "grok-video": {
            "label": "Grok Video",
            "channel": "xAIQ",
            "params": [
                {"key": "duration", "label": "时长(秒)", "type": "radio", "options": [6, 10, 15, 20, 25, 30], "default": 6},
                {"key": "aspect_ratio", "label": "比例", "type": "radio", "options": ["2:3", "3:2", "1:1", "9:16", "16:9"], "default": "16:9"},
                {"key": "quality", "label": "清晰度", "type": "text", "default": "720p", "visible": False}
            ],
            "supports_image": True
        },
        "h3-video": {
            "label": "H3 视频",
            "channel": "minimax",
            "params": [
                {"key": "duration", "label": "时长(秒)", "type": "number", "default": 4, "min": 4, "max": 8},
                {"key": "resolution", "label": "分辨率", "type": "radio", "options": ["1K", "2K", "4K"], "default": "2K"},
                {"key": "ratio", "label": "比例", "type": "radio", "options": ["16:9", "9:16"], "default": "16:9"}
            ],
            "supports_image": True
        }
    },
    "音乐": {
        "music_generation": {
            "label": "音乐生成",
            "channel": "music_gen",
            "params": [
                {"key": "style", "label": "风格", "type": "radio", "options": ["pop", "jazz", "classical", "rock", "electronic"], "default": "pop"},
                {"key": "tempo", "label": "速度(BPM)", "type": "slider", "min": 60, "max": 180, "default": 120, "step": 5}
            ],
            "supports_image": False
        }
    },
    "数字人": {
        "digital_human": {
            "label": "全驱动数字人",
            "channel": "dh_channel",
            "params": [
                {"key": "expression", "label": "表情", "type": "radio", "options": ["neutral", "happy", "sad", "surprised"], "default": "neutral"},
                {"key": "voice", "label": "语音", "type": "text", "default": ""}
            ],
            "supports_image": False
        }
    }
}

# 应用映射（用于“更多应用”快捷访问，这里未在UI中直接实现，但可扩展）
APP_MAP = {
    "音乐生成": "music_generation",
    "全驱动数字人": "digital_human",
    "人物替换": "gpt-image-2",
    "动作迁移": "veo3.1-fast",
    "全能视频生成": "veo3.1-pro",
    "seedsvc": "veo3.1-fast",
    "FlashVSR": "veo3.1-fast",
    "水印消除": "gpt-image-2",
    "数字人对口型": "digital_human",
    "dressing-diffusion": "gpt-image-2",
    "MMaudio": "music_generation",
    "Happy Horse": "veo3.1-fast",
    "wan": "veo3.1-fast",
    "智能剪辑": "veo3.1-fast"
}

# ==================== 历史记录（内存） ====================
history = []

# ==================== 生成函数 ====================
def generate_wrapper(model_key, prompt, file, *args):
    """生成入口，处理所有模型"""
    model_info = None
    for cat, mods in MODELS.items():
        if model_key in mods:
            model_info = mods[model_key]
            break
    if not model_info:
        return "❌ 未找到模型配置"

    # 构建参数
    params = {}
    param_defs = model_info["params"]
    for i, pdef in enumerate(param_defs):
        if i < len(args):
            val = args[i]
            if val is not None:
                if pdef["type"] == "checkbox":
                    params[pdef["key"]] = bool(val)
                else:
                    params[pdef["key"]] = val

    # 处理文件
    if file is not None:
        uri = file_to_data_uri(file)
        if uri:
            if "image" in model_key or "nano" in model_key:
                params["image_urls"] = [uri]
            elif "video" in model_key or "h3" in model_key:
                params["image_urls"] = [uri]
            else:
                params["urls"] = [uri]

    if prompt:
        params["prompt"] = prompt

    channel = model_info["channel"]
    model = model_key
    client = AIGCClient()

    if "qwen" in model_key:
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return f"❌ 错误：{resp['error']}"
        choices = resp.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "无回复")
            usage = resp.get("usage", {})
            cost = usage.get("points_cost", 0)
            result_text = f"🤖 {content}\n\n消耗 {cost} 点"
            history.append({"时间": datetime.now().strftime("%H:%M:%S"), "模型": model_key, "提示": prompt, "结果": result_text[:100]})
            return result_text
        return "⚠️ 未获取回复"
    else:
        resp = client.create_task(model, channel, **params)
        if "error" in resp:
            return f"❌ 错误：{resp['error']}"
        task_id = resp.get("task_id")
        if not task_id:
            result_text = f"⚠️ 同步返回：{json.dumps(resp, ensure_ascii=False, indent=2)}"
            history.append({"时间": datetime.now().strftime("%H:%M:%S"), "模型": model_key, "提示": prompt, "结果": result_text[:100]})
            return result_text
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
                result_text = f"✅ 生成完成！\n链接：{url}\n消耗 {cost} 点"
                history.append({"时间": datetime.now().strftime("%H:%M:%S"), "模型": model_key, "提示": prompt, "结果": result_text[:100]})
                return result_text
            elif status in ["failed", "cancelled"]:
                return f"❌ 任务失败：{status_resp.get('msg', '未知错误')}"
            time.sleep(2)
        return "⏰ 超时，请稍后查询"

def get_balance_display():
    client = AIGCClient()
    resp = client.get_balance()
    if "error" in resp:
        return "💰 余额：查询失败"
    return f"💰 余额：{resp.get('available_points', 0):.2f} 点"

def refresh_history_display():
    if not history:
        return "暂无记录"
    lines = []
    for item in history[-10:]:
        lines.append(f"{item['时间']} | {item['模型']} | {item['结果'][:50]}...")
    return "\n".join(lines)

def on_model_cat_change(cat):
    return gr.update(choices=list(MODELS[cat].keys()))

# ==================== 构建大型系统界面（修复主题） ====================
def build_ui():
    # 自定义 CSS（保留深色风格）
    custom_css = """
    .gradio-container { max-width: 1400px; margin: auto; }
    .sidebar { background: #1a1a2e; padding: 15px; border-radius: 8px; }
    .main-area { background: #0f0f1a; padding: 20px; border-radius: 8px; }
    """
    # 使用 Soft 主题（兼容所有版本），并设置主色调为靛蓝
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), css=custom_css, title="AI 创作平台 · 企业版") as demo:
        gr.Markdown("# 🧠 AI 创作平台 · 企业版")

        # 顶部状态栏
        with gr.Row():
            balance_display = gr.Markdown(get_balance_display())
            refresh_btn = gr.Button("🔄 刷新余额", size="sm")
        refresh_btn.click(fn=get_balance_display, outputs=balance_display)

        # 主布局：左侧参数栏 + 右侧结果区
        with gr.Row(equal_height=False):
            # ---------- 左侧参数面板 ----------
            with gr.Column(scale=1, elem_classes="sidebar"):
                gr.Markdown("### 🎯 模型选择")
                model_cat = gr.Dropdown(choices=list(MODELS.keys()), label="模型类别", value="图片")
                model_dropdown = gr.Dropdown(label="选择模型", choices=list(MODELS["图片"].keys()), interactive=True)
                model_cat.change(fn=on_model_cat_change, inputs=model_cat, outputs=model_dropdown)

                gr.Markdown("### 📝 输入")
                prompt_box = gr.Textbox(label="提示词 / 指令", placeholder="描述你的需求...", lines=3)

                gr.Markdown("### 📎 上传参考文件")
                file_upload = gr.File(label="上传图片/视频（可选）", file_types=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi"])

                gr.Markdown("### ⚙️ 参数设置")
                with gr.Accordion("高级参数", open=False):
                    # 通用参数（所有模型通用）
                    seed = gr.Number(label="种子 (Seed)", value=-1, precision=0)
                    # 主要参数控件（将根据模型类型显示/隐藏，但这里统一显示，用户自行使用）
                    resolution = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k", visible=True)
                    aspect = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1", visible=True)
                    duration = gr.Slider(4, 30, value=8, step=2, label="时长(秒)", visible=True)
                    style = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop", visible=True)
                    temperature = gr.Slider(0, 2, value=0.7, step=0.1, label="温度", visible=True)
                    max_tokens = gr.Slider(256, 4096, value=2048, step=256, label="最大输出", visible=True)

                generate_btn = gr.Button("🚀 生成", variant="primary", size="lg")

            # ---------- 右侧结果展示 ----------
            with gr.Column(scale=2, elem_classes="main-area"):
                output_md = gr.Markdown(label="📤 生成结果", value="等待生成...")
                gr.Markdown("### 📜 历史记录")
                history_display = gr.Markdown("暂无记录")
                refresh_history_btn = gr.Button("刷新历史", size="sm")
                refresh_history_btn.click(fn=refresh_history_display, outputs=history_display)

        # ---------- 事件绑定 ----------
        generate_btn.click(
            fn=generate_wrapper,
            inputs=[
                model_dropdown,
                prompt_box,
                file_upload,
                resolution,
                aspect,
                duration,
                style,
                temperature,
                max_tokens,
                seed
            ],
            outputs=output_md
        ).then(fn=refresh_history_display, outputs=history_display)

    return demo

# ==================== 启动 ====================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=port)
