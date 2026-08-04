import gradio as gr
import requests
import time
import json

class AIGCClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.likeadmin.cn/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method, endpoint, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            if method == "POST":
                resp = requests.post(url, headers=self.headers, json=data)
            else:
                resp = requests.get(url, headers=self.headers, params=data)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def generate_image(self, prompt):
        resp = self._request("POST", "/tasks", {
            "model": "gpt-image-2",
            "params": {"prompt": prompt, "width": 1024, "height": 1024}
        })
        if "error" in resp:
            return f"❌ 请求失败: {resp['error']}"
        task_id = resp.get("data", {}).get("task_id")
        if not task_id:
            return "❌ 未获取到任务ID，请检查模型是否已开通"
        for _ in range(60):
            status_resp = self._request("GET", f"/tasks/{task_id}")
            if "error" in status_resp:
                return f"❌ 轮询错误: {status_resp['error']}"
            status = status_resp.get("data", {}).get("status")
            if status in ["completed", "success"]:
                imgs = status_resp.get("data", {}).get("images", [])
                if imgs:
                    return f"✅ 生成成功！点击链接查看：{imgs[0].get('url')}"
                return "⚠️ 任务完成但未返回图片"
            elif status == "failed":
                return f"❌ 任务失败: {status_resp.get('data', {}).get('msg', '未知原因')}"
            time.sleep(2)
        return "⏰ 任务超时，请稍后重试"

    def chat(self, prompt):
        resp = self._request("POST", "/chat/completions", {
            "model": "gpt-3.5-turbo",
            "params": {"messages": [{"role": "user", "content": prompt}]}
        })
        if "error" in resp:
            return f"❌ 请求失败: {resp['error']}"
        choices = resp.get("data", {}).get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "无回复内容")
        return "⚠️ 未获取到回复"

def process(api_key, prompt, mode):
    if not api_key:
        return "⚠️ 请先输入你的 API Key"
    if not prompt:
        return "⚠️ 请输入描述或问题"
    client = AIGCClient(api_key)
    if mode == "🖼️ 图片生成":
        return client.generate_image(prompt)
    else:
        return client.chat(prompt)

iface = gr.Interface(
    fn=process,
    inputs=[
        gr.Textbox(label="🔑 API Key（从个人中心复制）", type="password", placeholder="sk-..."),
        gr.Textbox(label="📝 输入指令/问题", placeholder="例如：一只赛博朋克猫"),
        gr.Radio(["🖼️ 图片生成", "💬 文本对话"], label="选择模式", value="🖼️ 图片生成")
    ],
    outputs=gr.Markdown(label="📤 结果"),
    title="🧠 算力超市 · 手机AI助手",
)

iface.launch()
