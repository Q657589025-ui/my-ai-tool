import gradio as gr
import requests
import time
import json
import os

# ========== 你的 API Key（已硬编码，但强烈建议重置后替换） ==========
YOUR_API_KEY = "sk-7a0c8f2f854263e38c24f8037e1cb22d828f7545b4016709"
# ⚠️ 如果你重置了 Key，请将上面这行替换为新 Key。

# ========== 基础 URL（根据你的平台是 likeadmin） ==========
BASE_URL = "https://api.likeadmin.cn/api/v1"

# ========== 客户端 ==========
class AIGCClient:
    def __init__(self, api_key=YOUR_API_KEY):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

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

    def get_models(self, detail=1):
        return self._request("GET", "/models", params={"detail": detail})

    def get_balance(self):
        return self._request("GET", "/user/balance")

    def chat_completion(self, model, channel, messages, stream=False, **kwargs):
        payload = {"model": model, "channel": channel, "messages": messages, "stream": stream}
        payload.update(kwargs)
        return self._request("POST", "/chat/completions", data=payload)

    def create_task(self, model, channel, callback_url=None, **params):
        payload = {"model": model, "channel": channel}
        if callback_url:
            payload["callback_url"] = callback_url
        payload.update(params)
        return self._request("POST", "/tasks", data=payload)

    def query_task(self, task_id):
        return self._request("GET", f"/tasks/{task_id}")

    def get_pricing(self, model, channel=None):
        params = {"type": "model", "model": model}
        if channel:
            params["channel"] = channel
        return self._request("GET", "/pricing", params=params)


# ========== 应用映射（覆盖截图中所有应用） ==========
APP_MAP = {
    "音乐生成": {"app_code": "music_generation", "api_code": "generate"},
    "全驱动数字人": {"app_code": "full_digital_human", "api_code": "create"},
    "人物替换": {"app_code": "person_swap", "api_code": "swap"},
    "动作迁移": {"app_code": "motion_transfer", "api_code": "transfer"},
    "全能视频生成": {"app_code": "full_video", "api_code": "create_task"},
    "seedsvc": {"app_code": "seedsvc", "api_code": "generate"},
    "FlashVSR": {"app_code": "flashvsr", "api_code": "enhance"},
    "水印消除": {"app_code": "watermark_removal", "api_code": "remove"},
    "数字人对口型": {"app_code": "digital_human_lip", "api_code": "sync"},
    "dressing-diffusion": {"app_code": "dressing_diffusion", "api_code": "generate"},
    "MMaudio": {"app_code": "mmaudio", "api_code": "generate"},
    "Happy Horse": {"app_code": "happy_horse", "api_code": "generate"},
    "wan": {"app_code": "wan", "api_code": "generate"},
    "智能剪辑": {"app_code": "smart_edit", "api_code": "edit"},
}


# ========== 界面逻辑 ==========
def load_models():
    """点击加载模型按钮时调用"""
    client = AIGCClient()
    resp = client.get_models()
    if "error" in resp:
        return gr.update(choices=[]), f"❌ 加载失败: {resp['error']}"
    data = resp.get("data", [])
    choices = []
    for m in data:
        label = f"{m.get('model_name', m.get('model_code'))} ({m.get('model_code')})"
        choices.append(label)
    # 同时更新余额
    bal = client.get_balance()
    if "error" in bal:
        bal_text = "❌ 余额查询失败"
    else:
        bal_text = f"💰 当前余额: {bal.get('available_points', 0):.2f} 点"
    return gr.update(choices=choices), bal_text

def on_app_click(app_name):
    info = APP_MAP.get(app_name, {})
    return info.get("app_code", ""), info.get("api_code", "")

def submit_request(model_selection, channel, prompt, app_code, api_code,
                   extra_params, mode, callback_url):
    client = AIGCClient()
    # 提取 model_code
    if model_selection:
        model_code = model_selection.split("(")[-1].rstrip(")")
    else:
        model_code = ""

    if mode == "文本对话":
        if not prompt:
            return "⚠️ 请输入对话内容"
        if not model_code or not channel:
            return "⚠️ 请先选择模型并填写 channel"
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model_code, channel, messages, stream=False)
        if "error" in resp:
            return f"❌ 请求失败: {resp['error']}"
        choices = resp.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "无回复")
            usage = resp.get("usage", {})
            cost = usage.get("points_cost", 0)
            return f"🤖 回复:\n{content}\n\n📊 消耗: {cost} 点"
        return "⚠️ 未获取到回复"

    else:  # 异步任务
        if not model_code or not channel:
            return "⚠️ 异步任务需要选择模型并填写 channel"
        try:
            params = json.loads(extra_params) if extra_params.strip() else {}
        except:
            return "⚠️ 额外参数 JSON 格式错误"
        if prompt:
            params["prompt"] = prompt
        # 如果 app_code 和 api_code 都存在，尝试使用应用接口（但实际仍走 /tasks，因为平台应用也是 /tasks 方式）
        # 我们统一使用 create_task，并传入 model 和 channel
        resp = client.create_task(model_code, channel, callback_url, **params)
        if "error" in resp:
            return f"❌ 创建任务失败: {resp['error']}"
        task_id = resp.get("task_id")
        if not task_id:
            return f"⚠️ 未返回 task_id，可能同步返回:\n{json.dumps(resp, ensure_ascii=False, indent=2)}"
        # 轮询等待
        start = time.time()
        while time.time() - start < 120:
            status_resp = client.query_task(task_id)
            if "error" in status_resp:
                return f"❌ 查询状态失败: {status_resp['error']}"
            status = status_resp.get("status")
            if status in ["completed", "success"]:
                result = status_resp.get("result", {})
                usage = status_resp.get("usage", {})
                cost = usage.get("points_cost", 0)
                result_str = json.dumps(result, indent=2, ensure_ascii=False)
                return f"✅ 任务完成 (ID: {task_id})\n结果:\n{result_str}\n\n消耗: {cost} 点"
            elif status in ["failed", "cancelled"]:
                msg = status_resp.get("msg", "未知错误")
                return f"❌ 任务失败: {msg}"
            time.sleep(2)
        return f"⏰ 超时，当前状态: {status_resp.get('status', 'unknown')}"


# ========== 构建高级界面 ==========
with gr.Blocks(theme=gr.themes.Soft(), title="算力超市 · 全功能 AI 工作站") as iface:
    gr.Markdown("# 🧠 算力超市 · 全功能 AI 工作站")
    gr.Markdown("API Key 已内置，点击「加载模型」即可自动获取可用模型列表。")

    with gr.Row():
        load_btn = gr.Button("🔄 加载模型", variant="primary")
        balance_display = gr.Markdown("💰 点击加载模型后显示余额")

    model_dropdown = gr.Dropdown(label="📦 选择模型", choices=[], interactive=True)
    channel_input = gr.Textbox(label="📡 渠道 (channel)", placeholder="如 openai, dashscope_compatible")

    mode_radio = gr.Radio(
        choices=["文本对话", "异步任务"],
        label="⚙️ 调用模式",
        value="文本对话",
        interactive=True
    )

    prompt_input = gr.Textbox(label="📝 提示词 / 指令", placeholder="输入你的描述或问题...", lines=3)

    gr.Markdown("### 🚀 应用快捷入口（点击自动填充 app_code 和 api_code）")
    # 按行显示卡片
    app_names = list(APP_MAP.keys())
    for i in range(0, len(app_names), 4):
        with gr.Row():
            for name in app_names[i:i+4]:
                btn = gr.Button(name, size="sm", variant="secondary")
                btn.click(fn=on_app_click, inputs=gr.State(name), outputs=[gr.State(), gr.State()])
                # 但我们无法直接控制输出，需要用隐藏组件，简化：我们使用gr.State存储，并利用js？这里我们使用回调更新文本框
                # 另一种方式：直接将点击事件绑定到设置文本框值，需使用gr.update，但无法跨组件。
                # 我们使用一个隐藏的文本框来接收，然后通过js或回调更新，但为了简单，我们让点击时调用一个函数，返回两个值，然后赋值给文本框
                # 因为Gradio不支持直接给其他组件赋值，只能通过输出，我们可以定义两个文本框用于接收，但这里我们使用on_app_click直接更新两个文本框的value，需要设置输出。
                # 这里我们重新设计：每个按钮点击时，调用函数，输出到两个文本框（作为输出），再更新。
                # 但多个按钮不能共用输出，我们用gr.State存储中间值，然后用一个事件监听？太复杂。我们改为：点击按钮时，将app_code和api_code填充到下面两个文本框，通过JavaScript或通过Gradio的update机制。
                # Gradio的Blocks中，一个事件的输出可以指定多个组件，我们可以为每个按钮绑定一个单独的事件，但每个按钮都绑定到同一个输出组件（两个文本框）即可。
                # 我们使用一个函数，返回两个值，然后设置输出为app_code_input和api_code_input。
                # 但每个按钮需要独立触发，可以共用同一个函数，传入name。
                # 所以我们将按钮放在循环外，用变量存储按钮对象，然后统一绑定。
                # 这里用更简洁的方式：创建一个隐藏的组件，用gr.State存储当前选中的应用，然后监听这个State变化来更新文本框？有点绕。
                # 最简单的做法：每个按钮绑定一个函数，直接返回两个值，然后使用outputs=[app_code_input, api_code_input]。
                # 因此我们在循环中为每个按钮绑定。
                btn.click(
                    fn=on_app_click,
                    inputs=gr.State(name),
                    outputs=[app_code_input, api_code_input]
                )

    with gr.Row():
        app_code_input = gr.Textbox(label="App Code", placeholder="应用编码", scale=1)
        api_code_input = gr.Textbox(label="API Code", placeholder="接口编码", scale=1)

    extra_params_input = gr.Textbox(label="📎 额外参数 (JSON)", placeholder='{"width": 1280, "height": 720}', lines=2)
    callback_url_input = gr.Textbox(label="🔔 回调地址 (选填)", placeholder="https://your-domain.com/callback")

    submit_btn = gr.Button("🚀 执行", variant="primary", size="lg")
    output_markdown = gr.Markdown(label="📤 执行结果")

    # 事件绑定
    load_btn.click(fn=load_models, inputs=[], outputs=[model_dropdown, balance_display])

    submit_btn.click(
        fn=submit_request,
        inputs=[
            model_dropdown,
            channel_input,
            prompt_input,
            app_code_input,
            api_code_input,
            extra_params_input,
            mode_radio,
            callback_url_input
        ],
        outputs=output_markdown
    )


# ========== 启动 ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    iface.launch(server_name="0.0.0.0", server_port=port)
