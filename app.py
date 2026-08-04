import os
import socket
import gradio as gr
from core.auth import create_default_admin, get_user_points
from ui.login import create_login_ui
from ui.main import create_main_tabs

create_default_admin()

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

# ========== 硬编码 CSS（确保样式生效） ==========
HARD_CODED_CSS = """
.stats-row {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 16px !important;
    margin-bottom: 24px !important;
}
.stat-card {
    background: white !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
    text-align: center !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    border: 1px solid #f1f4f9 !important;
}
.stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-number { font-size: 32px; font-weight: 700; color: #0f172a; }
.stat-label { font-size: 14px; color: #64748b; }
.works-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)) !important;
    gap: 16px !important;
}
.work-card {
    background: white !important;
    border-radius: 16px !important;
    padding: 16px !important;
    border: 1px solid #f1f4f9 !important;
}
.work-thumb { font-size: 32px; text-align: center; padding: 20px 0; background: #f8fafc; border-radius: 12px; }
.work-title { font-weight: 600; color: #0f172a; font-size: 14px; }
.work-meta { font-size: 12px; color: #94a3b8; }
.empty-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 16px; }
.section-title { font-size: 18px; font-weight: 600; color: #0f172a; margin-bottom: 16px; }
@media (prefers-color-scheme: dark) {
    .stat-card { background: #1a1a2e !important; border-color: rgba(255,255,255,0.06) !important; }
    .stat-number { color: #f1f5f9 !important; }
    .stat-label { color: #94a3b8 !important; }
    .work-card { background: #1a1a2e !important; border-color: rgba(255,255,255,0.06) !important; }
    .work-title { color: #e2e8f0 !important; }
    .work-meta { color: #64748b !important; }
    .work-thumb { background: rgba(255,255,255,0.04) !important; }
    .section-title { color: #f1f5f9 !important; }
    .empty-state { color: #94a3b8 !important; }
}
"""

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

if __name__ == "__main__":
    preferred_port = int(os.getenv("PORT", 7860))
    port = find_free_port(preferred_port)
    print(f"✅ 使用端口: {port}")
    demo = build_app()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=gr.themes.Soft(primary_hue="indigo"),
        css=HARD_CODED_CSS
    )
