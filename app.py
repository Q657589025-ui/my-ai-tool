import gradio as gr
from core.database import create_default_admin
from ui.login import create_login_ui
from ui.main import create_main_ui  # 需要实现，但我们可以把主应用放在这里

create_default_admin()

def build_app():
    # 创建登录界面（独立页面）
    login_page, token_state, user_state, user_id_state = create_login_ui()

    # 创建主应用界面（先不显示）
    main_page = gr.Blocks(visible=False)
    # 填充主应用内容...
    # 这里为了演示，简化为主应用占位
    with main_page:
        gr.Markdown("主应用内容（待实现）")

    # 当登录成功时，切换可见性
    def on_login_success(token, user):
        if token:
            return gr.update(visible=False), gr.update(visible=True), user.get("id")
        return gr.update(visible=True), gr.update(visible=False), None

    token_state.change(
        fn=on_login_success,
        inputs=[token_state, user_state],
        outputs=[login_page, main_page, user_id_state]
    )

    # 将两个页面组合在一起
    app = gr.Blocks()
    with app:
        login_page.render()
        main_page.render()

    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=port)
