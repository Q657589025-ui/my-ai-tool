import gradio as gr
from core.database import get_db_session, Work

def create_gallery_tab(user_id_state):
    with gr.Column():
        gallery_md = gr.Markdown("⏳ 加载中...")

        def update_gallery(user_id):
            if not user_id:
                return "⚠️ 请先登录"
            db = get_db_session()
            try:
                works = db.query(Work).filter(Work.user_id == user_id).order_by(Work.created_at.desc()).limit(50).all()
            finally:
                db.close()
            if not works:
                return "📭 暂无作品"
            lines = []
            for w in works:
                lines.append(f"**{w.title}**  {w.type}  {w.model}  {w.created_at}")
                if w.url and w.url.startswith("http"):
                    lines.append(f"![作品]({w.url})")
            return "\n\n".join(lines)

        user_id_state.change(fn=update_gallery, inputs=user_id_state, outputs=gallery_md)
    return gr.Column()
