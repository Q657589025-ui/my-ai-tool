import os
import gradio as gr
from ui.theme import CUSTOM_CSS
from core.auth import create_default_admin, get_user_points
from ui.login import create_login_ui
from ui.main import create_main_tabs

create_default_admin()

def build_app():
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo"), title="AI Studio Pro", css=CUSTOM_CSS) as demo:
        login_col, token_state, user_state, user_id_state = create_login_ui()

        main_col = gr.Column(visible=False)
        with main_col:
            with gr.Row():
                gr.Markdown("### 🧠 AI Studio Pro")
                balance_display = gr.Markdown("")
                logout_btn = gr.Button("🚪 退出", size="sm")
            main_tabs = create_main_tabs(user_id_state)

        def on_login_success(token, user):
            if token:
                return user.get("id"), gr.update(visible=False), gr.update(visible=True)
            return None, gr.update(visible=True), gr.update(visible=False)

        token_state.change(
            fn=on_login_success,
            inputs=[token_state, user_state],
            outputs=[user_id_state, login_col, main_col]
        )

        def logout():
            return "", {}, None, gr.update(visible=True), gr.update(visible=False)
        logout_btn.click(fn=logout, inputs=[], outputs=[token_state, user_state, user_id_state, login_col, main_col])

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
