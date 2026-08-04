import gradio as gr
from core.task_manager import submit_task
from config.settings import MODEL_CONFIG_PATH
import json

with open(MODEL_CONFIG_PATH, "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

def create_video_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 🎬 视频创作")
        model_sel = gr.Dropdown(choices=list(MODEL_CONFIG.get("video", {}).keys()), label="模型", value="VEO 3.1 Fast")
        prompt = gr.Textbox(label="描述", lines=3)
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".png", ".gif", ".webp"])
        with gr.Row():
            quality = gr.Radio(["720p", "1080p", "4k"], label="清晰度", value="720p")
            duration = gr.Slider(4, 30, value=8, step=2, label="时长(秒)")
            ratio = gr.Radio(["16:9", "9:16"], label="比例", value="16:9")
        btn = gr.Button("🚀 生成", variant="primary")
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

        btn.click(gen, [user_id_state, model_sel, prompt, file, quality, duration, ratio], [output, status])
    return gr.Column()
