import gradio as gr
from core.database import get_db_session, Work

def create_gallery_tab(user_id_state):
    with gr.Column():
        gr.Markdown("## 📂 作品库")
        gr.Markdown("加载作品...")
    return gr.Column()
