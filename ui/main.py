import gradio as gr  # ✅ 添加这行
from ui.tabs.dashboard import create_dashboard_tab
from ui.tabs.image import create_image_tab
from ui.tabs.video import create_video_tab
from ui.tabs.music import create_music_tab
from ui.tabs.human import create_human_tab
from ui.tabs.chat import create_chat_tab
from ui.tabs.task_center import create_task_center_tab
from ui.tabs.gallery import create_gallery_tab

def create_main_tabs(user_id_state):
    with gr.Tabs() as tabs:
        with gr.TabItem("🏠 首页"):
            create_dashboard_tab(user_id_state)
        with gr.TabItem("🎨 图片"):
            create_image_tab(user_id_state)
        with gr.TabItem("🎬 视频"):
            create_video_tab(user_id_state)
        with gr.TabItem("🎵 音乐"):
            create_music_tab(user_id_state)
        with gr.TabItem("🧑 数字人"):
            create_human_tab(user_id_state)
        with gr.TabItem("🤖 助手"):
            create_chat_tab(user_id_state)
        with gr.TabItem("📌 任务"):
            create_task_center_tab(user_id_state)
        with gr.TabItem("📂 作品"):
            create_gallery_tab(user_id_state)
    return tabs
