import gradio as gr
from core.task_manager import submit_task
from config.settings import MODEL_CONFIG_PATH
import json

with open(MODEL_CONFIG_PATH, "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

def create_music_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 🎵 音乐生成")
        prompt = gr.Textbox(label="描述", lines=3)
        style = gr.Radio(["pop", "jazz", "classical", "rock", "electronic"], label="风格", value="pop")
        tempo = gr.Slider(60, 180, value=120, step=5, label="速度(BPM)")
        btn = gr.Button("🚀 生成", variant="primary")
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
    return gr.Column()
