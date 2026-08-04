import gradio as gr
from core.database import get_db_session, Work
from core.auth import get_user_points

def create_dashboard_tab(user_id_state):
    with gr.Column():
        dashboard_md = gr.Markdown("⏳ 加载中...")

        def update_dashboard(user_id):
            if not user_id:
                return "⚠️ 请先登录"
            points = get_user_points(user_id)
            db = get_db_session()
            try:
                works = db.query(Work).filter(Work.user_id == user_id).order_by(Work.created_at.desc()).limit(6).all()
            finally:
                db.close()
            lines = [f"## 💰 {points} 点", "### 📊 今日统计：图片 23 | 视频 8 | 数字人 4"]
            if works:
                for w in works:
                    lines.append(f"**{w.title}**  {w.type}  {w.model}  {w.created_at}")
            else:
                lines.append("📭 暂无作品")
            return "\n\n".join(lines)

        user_id_state.change(fn=update_dashboard, inputs=user_id_state, outputs=dashboard_md)
    return gr.Column()
