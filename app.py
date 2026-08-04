css="""
    /* ===== 全局字体 & 重置 ===== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        background: #f0f2f5;
    }

    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 16px 20px !important;
        background: transparent !important;
    }

    /* ===== 顶部导航栏 ===== */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 24px;
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 6px 16px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.5);
    }

    .app-header .logo {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #1a1a2e;
    }

    .app-header .logo span {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .app-header .balance {
        font-size: 15px;
        font-weight: 600;
        color: #1e293b;
        background: #f1f4f9;
        padding: 6px 16px;
        border-radius: 30px;
    }

    .app-header .balance span {
        color: #4f46e5;
    }

    /* ===== 左侧导航 ===== */
    .sidebar-nav {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(8px);
        border-radius: 16px;
        padding: 12px 8px;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .sidebar-nav .gr-button {
        border: none !important;
        background: transparent !important;
        padding: 10px 16px !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        color: #64748b !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
        text-align: left !important;
    }

    .sidebar-nav .gr-button:hover {
        background: #f1f5f9 !important;
        color: #1e293b !important;
    }

    .sidebar-nav .gr-button.primary-nav {
        background: #eef2ff !important;
        color: #4f46e5 !important;
        font-weight: 600 !important;
    }

    .sidebar-nav .gr-button.primary-nav:hover {
        background: #e0e7ff !important;
    }

    /* ===== 主内容卡片 ===== */
    .main-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 28px 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 6px 16px rgba(0,0,0,0.04);
        border: 1px solid rgba(255,255,255,0.5);
        transition: box-shadow 0.2s;
    }

    .main-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.06), 0 12px 40px rgba(0,0,0,0.05);
    }

    /* ===== 标题 ===== */
    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.3px !important;
        color: #0f172a !important;
    }

    h1 { font-size: 28px !important; }
    h2 { font-size: 22px !important; }
    h3 { font-size: 18px !important; }

    /* ===== 按钮 ===== */
    .gr-button-primary {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 10px 28px !important;
        color: white !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(79,70,229,0.25) !important;
    }

    .gr-button-primary:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(79,70,229,0.35) !important;
    }

    .gr-button-primary:active {
        transform: scale(0.97) !important;
    }

    .gr-button-secondary {
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        color: #334155 !important;
        transition: all 0.15s !important;
    }

    .gr-button-secondary:hover {
        background: #e2e8f0 !important;
    }

    /* ===== 输入框 ===== */
    .gr-textbox textarea,
    .gr-textbox input {
        border-radius: 12px !important;
        border: 1.5px solid #e2e8f0 !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
        background: #fafbfc !important;
    }

    .gr-textbox textarea:focus,
    .gr-textbox input:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 4px rgba(79,70,229,0.08) !important;
        background: #ffffff !important;
    }

    /* ===== 下拉框 ===== */
    .gr-dropdown select {
        border-radius: 12px !important;
        border: 1.5px solid #e2e8f0 !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        background: #fafbfc !important;
        transition: border-color 0.2s !important;
    }

    .gr-dropdown select:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 4px rgba(79,70,229,0.08) !important;
    }

    /* ===== Radio / 滑块 ===== */
    .gr-radio label {
        font-weight: 500 !important;
        color: #334155 !important;
        font-size: 14px !important;
    }

    .gr-radio input[type="radio"] {
        accent-color: #4f46e5 !important;
        width: 18px !important;
        height: 18px !important;
    }

    .gr-slider input[type="range"] {
        accent-color: #4f46e5 !important;
    }

    /* ===== 文件上传 ===== */
    .gr-file input[type="file"] {
        border-radius: 12px !important;
        border: 1.5px dashed #d1d5db !important;
        padding: 20px !important;
        background: #fafbfc !important;
        transition: border-color 0.2s !important;
    }

    .gr-file input[type="file"]:hover {
        border-color: #4f46e5 !important;
        background: #f8fafc !important;
    }

    /* ===== Tabs 样式 ===== */
    .tabs-nav {
        display: flex;
        gap: 4px;
        background: #f1f4f9;
        border-radius: 14px;
        padding: 4px;
        margin-bottom: 20px;
    }

    .tabs-nav button {
        border: none !important;
        background: transparent !important;
        padding: 8px 20px !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        color: #64748b !important;
        transition: all 0.15s !important;
    }

    .tabs-nav button:hover {
        color: #1e293b !important;
        background: rgba(255,255,255,0.5) !important;
    }

    .tabs-nav button.selected {
        background: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        font-weight: 600 !important;
    }

    /* ===== 统计卡片 ===== */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 12px;
        margin: 16px 0;
    }

    .stat-card {
        background: #f8fafc;
        border-radius: 14px;
        padding: 16px 20px;
        text-align: center;
        border: 1px solid #f1f4f9;
    }

    .stat-card .number {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
    }

    .stat-card .label {
        font-size: 13px;
        color: #64748b;
        margin-top: 4px;
    }

    /* ===== 响应式（手机） ===== */
    @media (max-width: 768px) {
        .gradio-container { padding: 8px 12px !important; }
        .app-header { padding: 10px 16px; flex-wrap: wrap; gap: 8px; }
        .app-header .logo { font-size: 17px; }
        .main-card { padding: 16px !important; border-radius: 16px; }
        .stat-grid { grid-template-columns: repeat(2, 1fr); }
        .sidebar-nav .gr-button { font-size: 13px !important; padding: 8px 12px !important; }
        .tabs-nav button { font-size: 13px !important; padding: 6px 14px !important; }
        h1 { font-size: 22px !important; }
        h2 { font-size: 18px !important; }
        h3 { font-size: 16px !important; }
    }

    @media (max-width: 480px) {
        .stat-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .stat-card { padding: 12px; }
        .stat-card .number { font-size: 20px; }
        .main-card { padding: 12px !important; }
    }

    /* ===== 深色模式支持（可选） ===== */
    @media (prefers-color-scheme: dark) {
        body { background: #0f0f1a; }
        .app-header { background: rgba(26,26,46,0.9); border-color: rgba(255,255,255,0.06); }
        .app-header .logo { color: #e2e8f0; }
        .app-header .balance { background: rgba(255,255,255,0.06); color: #cbd5e1; }
        .app-header .balance span { color: #818cf8; }
        .sidebar-nav { background: rgba(26,26,46,0.9); border-color: rgba(255,255,255,0.06); }
        .sidebar-nav .gr-button { color: #94a3b8 !important; }
        .sidebar-nav .gr-button:hover { background: rgba(255,255,255,0.06) !important; color: #e2e8f0 !important; }
        .sidebar-nav .gr-button.primary-nav { background: rgba(79,70,229,0.2) !important; color: #818cf8 !important; }
        .main-card { background: #1a1a2e; border-color: rgba(255,255,255,0.06); }
        .main-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.3), 0 12px 40px rgba(0,0,0,0.2); }
        h1, h2, h3 { color: #f1f5f9 !important; }
        .stat-card { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.06); }
        .stat-card .number { color: #f1f5f9; }
        .stat-card .label { color: #94a3b8; }
        .gr-textbox textarea, .gr-textbox input { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.1) !important; color: #e2e8f0 !important; }
        .gr-textbox textarea:focus, .gr-textbox input:focus { background: rgba(255,255,255,0.08) !important; border-color: #818cf8 !important; }
        .gr-dropdown select { background: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.1) !important; color: #e2e8f0 !important; }
        .tabs-nav { background: rgba(255,255,255,0.06); }
        .tabs-nav button { color: #94a3b8 !important; }
        .tabs-nav button.selected { background: rgba(255,255,255,0.08) !important; color: #f1f5f9 !important; }
        .gr-file input[type="file"] { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.1) !important; color: #94a3b8 !important; }
        .gr-radio label { color: #cbd5e1 !important; }
    }
"""
