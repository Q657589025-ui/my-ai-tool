import gradio as gr
from core.database import get_db_session, Task

def create_task_center_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 📌 任务中心")
        # 通过 user_id_state 变化刷新，此处占位
        gr.Markdown("加载任务...")
    return gr.Column()
