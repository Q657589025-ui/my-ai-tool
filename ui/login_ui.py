import gradio as gr
from core.auth import register_user, login_user

def create_login_ui():
    with gr.Column(visible=True) as login_col:
        gr.Markdown("## 🔐 欢迎使用 AI Studio Pro")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 登录")
                username_login = gr.Textbox(label="用户名", placeholder="输入用户名")
                password_login = gr.Textbox(label="密码", type="password", placeholder="输入密码")
                login_btn = gr.Button("登录", variant="primary")
                login_output = gr.Markdown("")
            with gr.Column():
                gr.Markdown("### 注册")
                username_reg = gr.Textbox(label="用户名", placeholder="设置用户名")
                email_reg = gr.Textbox(label="邮箱", placeholder="your@email.com")
                password_reg = gr.Textbox(label="密码", type="password", placeholder="至少6位")
                reg_btn = gr.Button("注册", variant="secondary")
                reg_output = gr.Markdown("")

        token_state = gr.State("")
        user_state = gr.State({})

        def do_login(username, password):
            result = login_user(username, password)
            if "error" in result:
                return "", {}, f"❌ {result['error']}"
            return result["token"], result["user"], f"✅ 登录成功！欢迎 {result['user']['username']}"

        login_btn.click(do_login, [username_login, password_login], [token_state, user_state, login_output])

        def do_register(username, email, password):
            if len(password) < 6:
                return "❌ 密码至少6位"
            result = register_user(username, email, password)
            if "error" in result:
                return f"❌ {result['error']}"
            return "✅ 注册成功！请登录"

        reg_btn.click(do_register, [username_reg, email_reg, password_reg], reg_output)

        return login_col, token_state, user_state
