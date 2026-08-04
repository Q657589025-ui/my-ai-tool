import gradio as gr
from core.database import get_db_session, Task

def create_task_center_tab(user_id_state):
    with gr.Column():
        task_md = gr.Markdown("⏳ 加载中...")

        def update_tasks(user_id):
            if not user_id:
                return "⚠️ 请先登录"
            db = get_db_session()
            try:
                tasks = db.query(Task).filter(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(20).all()
            finally:
                db.close()
            if not tasks:
                return "📭 暂无任务"
            lines = []
            for t in tasks:
                emoji = "⏳" if t.status == "waiting" else "🔄" if t.status == "processing" else "✅" if t.status == "completed" else "❌"
                lines.append(f"{emoji} {t.type} | {t.model} | {t.prompt[:30]}... | 进度 {t.progress}%")
            return "\n".join(lines)

        user_id_state.change(fn=update_tasks, inputs=user_id_state, outputs=task_md)
    return gr.Column()
