import gradio as gr
from core.database import get_db_session, Work
from core.auth import get_user_points

def create_dashboard_tab(user_id_state):
    with gr.Column():
        # 动态更新（实际内容通过 user_id_state 变化时刷新）
        gr.Markdown("## 💰 加载中...")
        gr.Markdown("### 今日统计：图片 23 | 视频 8 | 数字人 4")
        gr.Markdown("暂无作品")

    # 因 Gradio 无法在渲染时动态读取 State，我们采用事件绑定更新内容
    # 在 app.py 中通过 user_id_state.change 更新
    return gr.Column()  # 占位
