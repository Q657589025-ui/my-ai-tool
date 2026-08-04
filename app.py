import os
import gradio as gr
from core.database import create_default_admin
from ui.login import create_login_ui
from ui.main import (
    render_dashboard, render_task_center, render_image_ui,
    render_video_ui, render_music_ui, render_human_ui,
    render_chat_ui, render_history
)
from core.auth import get_user_points

def build_app():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio Pro", css="""
        .gradio-container { max-width: 1400px; margin: auto; padding: 20px; }
        .sidebar { background: #f8fafc; border-radius: 16px; padding: 20px; }
        .main-area { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .gr-button-primary { background: #4f46e5 !important; border: none !important; border-radius: 8px !important; }
    """) as demo:
        login_col, token_state, user_state, user_id_state = create_login_ui()

        main_col = gr.Column(visible=False)
        with main_col:
            with gr.Row():
                gr.Markdown("### 🧠 AI Studio Pro")
                balance_display = gr.Markdown("")
                logout_btn = gr.Button("🚪 退出", size="sm")

            with gr.Row():
                nav_home = gr.Button("🏠 首页", variant="secondary")
                nav_image = gr.Button("🎨 图片", variant="secondary")
                nav_video = gr.Button("🎬 视频", variant="secondary")
                nav_music = gr.Button("🎵 音乐", variant="secondary")
                nav_human = gr.Button("🧑 数字人", variant="secondary")
                nav_chat = gr.Button("🤖 助手", variant="secondary")
                nav_tasks = gr.Button("📌 任务", variant="secondary")
                nav_history = gr.Button("📂 作品", variant="secondary")

            content_col = gr.Column()
            with content_col:
                page_placeholder = gr.Column(visible=True)
                with page_placeholder:
                    gr.Markdown("请登录后选择功能")

            def switch_page(page_name, user_id):
                if not user_id:
                    return gr.Column(children=[gr.Markdown("请先登录")])
                if page_name == "dashboard":
                    return render_dashboard(user_id)
                elif page_name == "image":
                    return render_image_ui(user_id)
                elif page_name == "video":
                    return render_video_ui(user_id)
                elif page_name == "music":
                    return render_music_ui(user_id)
                elif page_name == "human":
                    return render_human_ui(user_id)
                elif page_name == "chat":
                    return render_chat_ui(user_id)
                elif page_name == "tasks":
                    return render_task_center(user_id)
                elif page_name == "history":
                    return render_history(user_id)
                else:
                    return gr.Column(children=[gr.Markdown("未知页面")])

            nav_home.click(fn=switch_page, inputs=[gr.State("dashboard"), user_id_state], outputs=page_placeholder)
            nav_image.click(fn=switch_page, inputs=[gr.State("image"), user_id_state], outputs=page_placeholder)
            nav_video.click(fn=switch_page, inputs=[gr.State("video"), user_id_state], outputs=page_placeholder)
            nav_music.click(fn=switch_page, inputs=[gr.State("music"), user_id_state], outputs=page_placeholder)
            nav_human.click(fn=switch_page, inputs=[gr.State("human"), user_id_state], outputs=page_placeholder)
            nav_chat.click(fn=switch_page, inputs=[gr.State("chat"), user_id_state], outputs=page_placeholder)
            nav_tasks.click(fn=switch_page, inputs=[gr.State("tasks"), user_id_state], outputs=page_placeholder)
            nav_history.click(fn=switch_page, inputs=[gr.State("history"), user_id_state], outputs=page_placeholder)

            def logout():
                return "", {}, None, gr.update(visible=True), gr.update(visible=False)
            logout_btn.click(fn=logout, inputs=[], outputs=[token_state, user_state, user_id_state, login_col, main_col])

            def update_balance(user_id):
                if user_id:
                    return f"💰 {get_user_points(user_id)} 点"
                return ""
            user_id_state.change(fn=update_balance, inputs=user_id_state, outputs=balance_display)

        def on_login_success(token, user):
            if token:
                return user.get("id"), gr.update(visible=False), gr.update(visible=True)
            return None, gr.update(visible=True), gr.update(visible=False)

        token_state.change(
            fn=on_login_success,
            inputs=[token_state, user_state],
            outputs=[user_id_state, login_col, main_col]
        )

    return demo

if __name__ == "__main__":
    create_default_admin()
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
