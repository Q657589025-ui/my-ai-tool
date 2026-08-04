CUSTOM_CSS = """
/* ===== 字体 ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', -apple-system, sans-serif; }

/* ===== 全局 ===== */
body { background: #f0f2f5; }
.gradio-container { max-width: 1400px !important; margin: 0 auto !important; padding: 20px !important; background: transparent !important; }

/* ===== 顶部导航 ===== */
.app-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 28px;
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.5);
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    margin-bottom: 24px;
}
.app-header .logo { font-size: 22px; font-weight: 700; color: #0f172a; }
.app-header .logo span { background: linear-gradient(135deg, #4f46e5, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.app-header .balance { font-size: 15px; font-weight: 600; color: #1e293b; background: #f1f4f9; padding: 8px 20px; border-radius: 30px; }
.app-header .balance strong { color: #4f46e5; }

/* ===== 统计卡片 ===== */
.stats-row { display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 16px !important; margin-bottom: 24px !important; }
.stat-card {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    border: 1px solid #f1f4f9;
    transition: transform 0.15s, box-shadow 0.15s;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
.stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-number { font-size: 32px; font-weight: 700; color: #0f172a; letter-spacing: -0.5px; }
.stat-label { font-size: 14px; color: #64748b; margin-top: 4px; font-weight: 500; }

/* ===== 作品区域 ===== */
.section-title { font-size: 18px; font-weight: 600; color: #0f172a; margin-bottom: 16px; }
.works-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
}
.work-card {
    background: white;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid #f1f4f9;
    transition: transform 0.15s, box-shadow 0.15s;
    cursor: pointer;
}
.work-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
.work-thumb { font-size: 32px; text-align: center; padding: 20px 0; background: #f8fafc; border-radius: 12px; margin-bottom: 12px; }
.work-title { font-weight: 600; color: #0f172a; font-size: 14px; }
.work-meta { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.empty-state { text-align: center; padding: 40px; color: #94a3b8; font-size: 16px; }

/* ===== 侧边导航 ===== */
.sidebar-nav { background: rgba(255,255,255,0.8); backdrop-filter: blur(12px); border-radius: 20px; padding: 16px 12px; border: 1px solid rgba(255,255,255,0.5); }
.sidebar-nav .gr-button { border: none !important; background: transparent !important; padding: 12px 18px !important; border-radius: 14px !important; font-weight: 500 !important; font-size: 15px !important; color: #64748b !important; transition: all 0.15s !important; width: 100% !important; text-align: left !important; }
.sidebar-nav .gr-button:hover { background: rgba(79,70,229,0.06) !important; color: #1e293b !important; }
.sidebar-nav .gr-button.primary-nav { background: rgba(79,70,229,0.1) !important; color: #4f46e5 !important; font-weight: 600 !important; }

/* ===== 主卡片 ===== */
.main-card { background: white; border-radius: 24px; padding: 32px; box-shadow: 0 1px 4px rgba(0,0,0,0.02), 0 8px 32px rgba(0,0,0,0.04); border: 1px solid rgba(255,255,255,0.5); }

/* ===== 按钮 ===== */
.gr-button-primary { background: linear-gradient(135deg, #4f46e5, #7c3aed) !important; border: none !important; border-radius: 14px !important; font-weight: 600 !important; font-size: 16px !important; padding: 12px 32px !important; color: white !important; box-shadow: 0 4px 14px rgba(79,70,229,0.25) !important; transition: all 0.2s !important; }
.gr-button-primary:hover { transform: translateY(-3px) !important; box-shadow: 0 8px 28px rgba(79,70,229,0.35) !important; }

/* ===== 输入框 ===== */
.gr-textbox textarea, .gr-textbox input { border-radius: 14px !important; border: 1.5px solid #e2e8f0 !important; padding: 14px 18px !important; font-size: 15px !important; background: #fafbfc !important; transition: border-color 0.2s !important; }
.gr-textbox textarea:focus, .gr-textbox input:focus { border-color: #4f46e5 !important; box-shadow: 0 0 0 4px rgba(79,70,229,0.08) !important; background: white !important; }

/* ===== Tabs ===== */
.tabs-nav { display: flex; gap: 6px; background: rgba(241,244,249,0.6); border-radius: 18px; padding: 6px; margin-bottom: 28px; border: 1px solid rgba(255,255,255,0.5); }
.tabs-nav button { border: none !important; background: transparent !important; padding: 10px 24px !important; border-radius: 14px !important; font-weight: 500 !important; font-size: 15px !important; color: #64748b !important; transition: all 0.15s !important; }
.tabs-nav button:hover { color: #1e293b !important; background: rgba(255,255,255,0.4) !important; }
.tabs-nav button.selected { background: white !important; color: #0f172a !important; box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important; font-weight: 600 !important; }

/* ===== 深色模式 ===== */
@media (prefers-color-scheme: dark) {
    body { background: #0f0f1a; }
    .app-header { background: rgba(26,26,46,0.8); border-color: rgba(255,255,255,0.06); }
    .app-header .logo { color: #e2e8f0; }
    .app-header .balance { background: rgba(255,255,255,0.06); color: #cbd5e1; }
    .app-header .balance strong { color: #818cf8; }
    .stat-card { background: #1a1a2e; border-color: rgba(255,255,255,0.06); }
    .stat-number { color: #f1f5f9; }
    .stat-label { color: #94a3b8; }
    .work-card { background: #1a1a2e; border-color: rgba(255,255,255,0.06); }
    .work-title { color: #e2e8f0; }
    .work-meta { color: #64748b; }
    .work-thumb { background: rgba(255,255,255,0.04); }
    .section-title { color: #f1f5f9; }
    .sidebar-nav { background: rgba(26,26,46,0.8); border-color: rgba(255,255,255,0.06); }
    .sidebar-nav .gr-button { color: #94a3b8 !important; }
    .sidebar-nav .gr-button:hover { background: rgba(255,255,255,0.04) !important; color: #e2e8f0 !important; }
    .sidebar-nav .gr-button.primary-nav { background: rgba(79,70,229,0.2) !important; color: #818cf8 !important; }
    .main-card { background: #1a1a2e; border-color: rgba(255,255,255,0.06); }
    .gr-textbox textarea, .gr-textbox input { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.08) !important; color: #e2e8f0 !important; }
    .tabs-nav { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.04); }
    .tabs-nav button { color: #94a3b8 !important; }
    .tabs-nav button.selected { background: rgba(255,255,255,0.08) !important; color: #f1f5f9 !important; }
}
"""
