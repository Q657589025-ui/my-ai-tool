import gradio as gr
from core.task_manager import submit_task
from config.settings import MODEL_CONFIG_PATH
import json

with open(MODEL_CONFIG_PATH, "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

def create_human_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 🧑 数字人")
        prompt = gr.Textbox(label="脚本", lines=3)
        expr = gr.Radio(["neutral", "happy", "sad", "surprised"], label="表情", value="neutral")
        btn = gr.Button("🚀 生成", variant="primary")
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
    return gr.Column()
