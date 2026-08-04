import gradio as gr
from core.task_manager import submit_task
from config.settings import MODEL_CONFIG_PATH
import json

with open(MODEL_CONFIG_PATH, "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

def create_chat_tab(user_id_state):
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
    return gr.Column()
