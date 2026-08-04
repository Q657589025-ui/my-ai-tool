import gradio as gr
from core.database import get_db_session, Work
from core.auth import get_user_points
from datetime import datetime

def create_dashboard_tab(user_id_state):
    with gr.Column():
        # 内联样式（双重保障）
        gr.HTML("""
        <style>
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
        </style>
        """)

        # 统计卡片行
        with gr.Row(elem_classes="stats-row"):
            with gr.Column(scale=1, elem_classes="stat-card"):
                gr.HTML("""
                    <div class="stat-icon">💰</div>
                    <div class="stat-number" id="balance-display">0</div>
                    <div class="stat-label">可用积分</div>
                """)
            with gr.Column(scale=1, elem_classes="stat-card"):
                gr.HTML("""
                    <div class="stat-icon">🎨</div>
                    <div class="stat-number">23</div>
                    <div class="stat-label">今日生成</div>
                """)
            with gr.Column(scale=1, elem_classes="stat-card"):
                gr.HTML("""
                    <div class="stat-icon">📊</div>
                    <div class="stat-number">8</div>
                    <div class="stat-label">进行中</div>
                """)
            with gr.Column(scale=1, elem_classes="stat-card"):
                gr.HTML("""
                    <div class="stat-icon">⭐</div>
                    <div class="stat-number">4</div>
                    <div class="stat-label">作品数</div>
                """)

        # 最近作品区域
        with gr.Column(elem_classes="works-section"):
            gr.HTML('<div class="section-title">📂 最近作品</div>')
            works_grid = gr.HTML('<div class="works-grid">暂无作品</div>')

        def update_dashboard(user_id):
            if not user_id:
                return '<div class="works-grid">请先登录</div>', "0"
            points = get_user_points(user_id)
            db = get_db_session()
            try:
                works = db.query(Work).filter(Work.user_id == user_id).order_by(Work.created_at.desc()).limit(6).all()
            finally:
                db.close()
            balance_html = str(points)
            if not works:
                works_html = '<div class="works-grid"><div class="empty-state">暂无作品，开始创作吧 🚀</div></div>'
            else:
                items = []
                for w in works:
                    date_str = w.created_at.strftime("%m-%d %H:%M") if w.created_at else ""
                    items.append(f'''
                        <div class="work-card">
                            <div class="work-thumb">{w.type} 🎯</div>
                            <div class="work-title">{w.title}</div>
                            <div class="work-meta">{w.model} · {date_str}</div>
                        </div>
                    ''')
                works_html = f'<div class="works-grid">{"".join(items)}</div>'
            return works_html, balance_html

        user_id_state.change(
            fn=update_dashboard,
            inputs=user_id_state,
            outputs=[works_grid, gr.HTML("#balance-display")]
        )

    return gr.Column()
