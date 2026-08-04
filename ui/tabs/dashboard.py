import gradio as gr
from core.database import get_db_session, Work
from core.auth import get_user_points
from datetime import datetime

def create_dashboard_tab(user_id_state):
    with gr.Column(elem_classes="dashboard-container"):
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
            # 更新余额
            balance_html = str(points)
            # 生成作品网格
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

        # 绑定更新事件
        works_grid.change(None, None, None)  # 占位
        user_id_state.change(
            fn=update_dashboard,
            inputs=user_id_state,
            outputs=[works_grid, gr.HTML("#balance-display")]
        )

    return gr.Column()
