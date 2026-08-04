import os
import gradio as gr
from core.database import create_default_admin
from ui.login import create_login_ui
from ui.main import create_main_tabs
from core.auth import get_user_points

create_default_admin()

def build_app():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio Pro", css="""
        .gradio-container { max-width: 1400px; margin: auto; padding: 20px; }
        .sidebar { background: #f8fafc; border-radius: 16px; padding: 20px; }
        .main-area { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .gr-button-primary { background: #4f46e5 !important; border: none !important; border-radius: 8px !important; }
    """) as demo:
        # 登录组件
        login_col, token_state, user_state, user_id_state = create_login_ui()

        # 主应用（登录后可见）
        main_col = gr.Column(visible=False)
        with main_col:
            with gr.Row():
                gr.Markdown("### 🧠 AI Studio Pro")
                balance_display = gr.Markdown("")
                logout_btn = gr.Button("🚪 退出", size="sm")

            # 创建主界面 Tabs（传入 user_id_state）
            main_tabs = create_main_tabs(user_id_state)

        # 登录成功后切换
        def on_login_success(token, user):
            if token:
                return user.get("id"), gr.update(visible=False), gr.update(visible=True)
            return None, gr.update(visible=True), gr.update(visible=False)

        token_state.change(
            fn=on_login_success,
            inputs=[token_state, user_state],
            outputs=[user_id_state, login_col, main_col]
        )

        # 退出登录
        def logout():
            return "", {}, None, gr.update(visible=True), gr.update(visible=False)
        logout_btn.click(fn=logout, inputs=[], outputs=[token_state, user_state, user_id_state, login_col, main_col])

        # 更新余额
        def update_balance(user_id):
            if user_id:
                return f"💰 {get_user_points(user_id)} 点"
            return ""
        user_id_state.change(fn=update_balance, inputs=user_id_state, outputs=balance_display)

    return demo

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
