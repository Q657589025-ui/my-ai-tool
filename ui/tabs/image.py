import gradio as gr
from core.task_manager import submit_task
from core.utils import download_image
from config.settings import MODEL_CONFIG_PATH
import json

with open(MODEL_CONFIG_PATH, "r") as f:
    MODEL_CONFIG = json.load(f)

def get_model_config(category, name):
    return MODEL_CONFIG.get(category, {}).get(name, {})

def create_image_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 🖼️ 图片创作")
        model_sel = gr.Dropdown(choices=list(MODEL_CONFIG.get("image", {}).keys()), label="模型", value="GPT Image 2")
        prompt = gr.Textbox(label="描述", lines=3, placeholder="输入图片描述...")
        file = gr.File(label="参考图（可选）", file_types=[".jpg", ".png", ".gif", ".webp"])
        with gr.Row():
            resolution = gr.Radio(["1k", "2k", "4k"], label="分辨率", value="1k")
            aspect = gr.Radio(["1:1", "16:9", "9:16", "4:3", "3:4"], label="比例", value="1:1")
        btn = gr.Button("🚀 生成", variant="primary")
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

        btn.click(gen, [user_id_state, model_sel, prompt, file, resolution, aspect], [output, status])
    return gr.Column()
