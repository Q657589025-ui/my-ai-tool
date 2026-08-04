import os
import socket
import gradio as gr
from ui.theme import CUSTOM_CSS  # 确保正确导入
from core.auth import create_default_admin, get_user_points
from ui.login import create_login_ui
from ui.main import create_main_tabs

# ========== 创建默认管理员 ==========
create_default_admin()

# ========== 端口自动查找 ==========
def find_free_port(start_port, max_attempts=10):
    port = start_port
    for _ in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise RuntimeError(f"无法找到可用端口（从 {start_port} 开始）")

# ========== 构建应用 ==========
def build_app():
    with gr.Blocks(title="AI Studio Pro") as demo:
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

# ========== 启动服务（强制注入 CSS） ==========
if __name__ == "__main__":
    preferred_port = int(os.getenv("PORT", 7860))
    port = find_free_port(preferred_port)
    print(f"✅ 使用端口: {port}")
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=gr.themes.Soft(primary_hue="indigo"),
        css=CUSTOM_CSS   # 明确传递 CSS
    )
