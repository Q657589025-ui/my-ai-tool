# UI 主题模块 - 专业级样式
CUSTOM_CSS = """
/* ===== 字体：Inter 为主，优雅降级 ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
    box-sizing: border-box;
}

/* ===== 全局背景 ===== */
body {
    background: #f7f8fc;
    margin: 0;
    padding: 0;
}

.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    padding: 20px 24px !important;
    background: transparent !important;
}

/* ===== 顶部导航 ===== */
.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 28px;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.04);
    margin-bottom: 24px;
    transition: box-shadow 0.2s;
}

.app-header:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 12px 48px rgba(0, 0, 0, 0.04);
}

.app-header .logo {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.6px;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 10px;
}

.app-header .logo svg {
    width: 28px;
    height: 28px;
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
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(4px);
    padding: 8px 20px;
    border-radius: 40px;
    border: 1px solid rgba(0, 0, 0, 0.04);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.app-header .balance strong {
    color: #4f46e5;
    font-weight: 700;
}

/* ===== 主布局：侧边栏 + 内容 ===== */
.sidebar-nav {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 16px 12px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.sidebar-nav .gr-button {
    border: none !important;
    background: transparent !important;
    padding: 12px 18px !important;
    border-radius: 14px !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    color: #64748b !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
    text-align: left !important;
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
}

.sidebar-nav .gr-button:hover {
    background: rgba(79, 70, 229, 0.06) !important;
    color: #1e293b !important;
}

.sidebar-nav .gr-button.primary-nav {
    background: rgba(79, 70, 229, 0.1) !important;
    color: #4f46e5 !important;
    font-weight: 600 !important;
}

.sidebar-nav .gr-button.primary-nav:hover {
    background: rgba(79, 70, 229, 0.16) !important;
}

/* ===== 主内容卡片 ===== */
.main-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 32px 36px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02), 0 8px 32px rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.5);
    transition: box-shadow 0.25s ease, transform 0.2s ease;
}

.main-card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04), 0 16px 56px rgba(0, 0, 0, 0.04);
    transform: translateY(-2px);
}

/* ===== 标题 ===== */
h1, h2, h3, h4 {
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
    color: #0f172a !important;
    margin-top: 0 !important;
}

h1 { font-size: 30px !important; line-height: 1.2; }
h2 { font-size: 24px !important; line-height: 1.25; }
h3 { font-size: 20px !important; line-height: 1.3; }

/* ===== 按钮 ===== */
.gr-button-primary {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 12px 32px !important;
    color: white !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25) !important;
}

.gr-button-primary:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 28px rgba(79, 70, 229, 0.35) !important;
}

.gr-button-primary:active {
    transform: scale(0.96) !important;
}

.gr-button-secondary {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(4px);
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    color: #334155 !important;
    transition: all 0.15s !important;
}

.gr-button-secondary:hover {
    background: #ffffff !important;
    border-color: #cbd5e1 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ===== 输入框 ===== */
.gr-textbox textarea,
.gr-textbox input {
    border-radius: 14px !important;
    border: 1.5px solid #e2e8f0 !important;
    padding: 14px 18px !important;
    font-size: 15px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    background: #fafbfc !important;
    line-height: 1.5 !important;
}

.gr-textbox textarea:focus,
.gr-textbox input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.08) !important;
    background: #ffffff !important;
}

/* ===== 下拉框 ===== */
.gr-dropdown select {
    border-radius: 14px !important;
    border: 1.5px solid #e2e8f0 !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    background: #fafbfc !important;
    transition: border-color 0.2s !important;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
    padding-right: 40px !important;
}

.gr-dropdown select:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.08) !important;
}

/* ===== Radio 按钮 ===== */
.gr-radio label {
    font-weight: 500 !important;
    color: #334155 !important;
    font-size: 15px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 8px 12px !important;
    border-radius: 10px !important;
    transition: background 0.15s !important;
    cursor: pointer !important;
}

.gr-radio label:hover {
    background: rgba(79, 70, 229, 0.04) !important;
}

.gr-radio input[type="radio"] {
    accent-color: #4f46e5 !important;
    width: 18px !important;
    height: 18px !important;
}

/* ===== 滑块 ===== */
.gr-slider input[type="range"] {
    accent-color: #4f46e5 !important;
    height: 6px !important;
    border-radius: 6px !important;
}

/* ===== 文件上传 ===== */
.gr-file input[type="file"] {
    border-radius: 16px !important;
    border: 1.5px dashed #d1d5db !important;
    padding: 28px !important;
    background: #fafbfc !important;
    transition: border-color 0.2s, background 0.2s !important;
    text-align: center !important;
    font-size: 14px !important;
    color: #64748b !important;
}

.gr-file input[type="file"]:hover {
    border-color: #4f46e5 !important;
    background: #f8fafc !important;
}

/* ===== Tabs 导航 ===== */
.tabs-nav {
    display: flex;
    gap: 6px;
    background: rgba(241, 244, 249, 0.6);
    backdrop-filter: blur(4px);
    border-radius: 18px;
    padding: 6px;
    margin-bottom: 28px;
    border: 1px solid rgba(255, 255, 255, 0.5);
}

.tabs-nav button {
    border: none !important;
    background: transparent !important;
    padding: 10px 24px !important;
    border-radius: 14px !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    color: #64748b !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}

.tabs-nav button:hover {
    color: #1e293b !important;
    background: rgba(255, 255, 255, 0.4) !important;
}

.tabs-nav button.selected {
    background: #ffffff !important;
    color: #0f172a !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04), 0 1px 4px rgba(0, 0, 0, 0.02) !important;
    font-weight: 600 !important;
}

/* ===== 统计卡片 ===== */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
    margin: 20px 0;
}

.stat-card {
    background: #f8fafc;
    border-radius: 18px;
    padding: 20px 24px;
    text-align: center;
    border: 1px solid #f1f4f9;
    transition: transform 0.15s, box-shadow 0.15s;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
}

.stat-card .number {
    font-size: 32px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
}

.stat-card .label {
    font-size: 14px;
    color: #64748b;
    margin-top: 6px;
    font-weight: 500;
}

/* ===== 作品网格 ===== */
.work-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
    margin-top: 12px;
}

.work-item {
    background: #f8fafc;
    border-radius: 16px;
    overflow: hidden;
    padding: 12px;
    border: 1px solid #f1f4f9;
    transition: transform 0.15s, box-shadow 0.15s;
}

.work-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
}

.work-item img {
    width: 100%;
    height: 120px;
    object-fit: cover;
    border-radius: 12px;
}

.work-item .title {
    font-size: 14px;
    font-weight: 500;
    margin-top: 8px;
    color: #0f172a;
}

/* ===== 响应式 (手机/平板) ===== */
@media (max-width: 1024px) {
    .gradio-container { padding: 16px !important; }
    .main-card { padding: 24px !important; }
}

@media (max-width: 768px) {
    .gradio-container { padding: 12px !important; }
    .app-header { padding: 12px 18px; flex-wrap: wrap; gap: 8px; border-radius: 16px; }
    .app-header .logo { font-size: 18px; }
    .app-header .balance { font-size: 14px; padding: 6px 14px; }
    .sidebar-nav .gr-button { font-size: 14px !important; padding: 10px 14px !important; }
    .main-card { padding: 18px !important; border-radius: 18px; }
    .tabs-nav button { padding: 8px 16px !important; font-size: 14px !important; }
    .stat-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .stat-card .number { font-size: 24px; }
    .work-grid { grid-template-columns: repeat(2, 1fr); }
    h1 { font-size: 24px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 17px !important; }
}

@media (max-width: 480px) {
    .gradio-container { padding: 8px !important; }
    .app-header { padding: 10px 14px; border-radius: 14px; }
    .app-header .logo { font-size: 16px; }
    .app-header .balance { font-size: 13px; padding: 4px 12px; }
    .main-card { padding: 14px !important; border-radius: 16px; }
    .tabs-nav button { padding: 6px 12px !important; font-size: 13px !important; }
    .stat-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
    .stat-card { padding: 14px; }
    .stat-card .number { font-size: 20px; }
    .work-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .gr-button-primary { font-size: 15px !important; padding: 10px 24px !important; }
}

/* ===== 深色模式自适应 ===== */
@media (prefers-color-scheme: dark) {
    body { background: #0f0f1a; }
    .app-header { background: rgba(26, 26, 46, 0.8); border-color: rgba(255, 255, 255, 0.06); }
    .app-header .logo { color: #e2e8f0; }
    .app-header .balance { background: rgba(255, 255, 255, 0.06); color: #cbd5e1; border-color: rgba(255, 255, 255, 0.04); }
    .app-header .balance strong { color: #818cf8; }
    .sidebar-nav { background: rgba(26, 26, 46, 0.8); border-color: rgba(255, 255, 255, 0.06); }
    .sidebar-nav .gr-button { color: #94a3b8 !important; }
    .sidebar-nav .gr-button:hover { background: rgba(255, 255, 255, 0.04) !important; color: #e2e8f0 !important; }
    .sidebar-nav .gr-button.primary-nav { background: rgba(79, 70, 229, 0.2) !important; color: #818cf8 !important; }
    .sidebar-nav .gr-button.primary-nav:hover { background: rgba(79, 70, 229, 0.28) !important; }
    .main-card { background: #1a1a2e; border-color: rgba(255, 255, 255, 0.06); }
    .main-card:hover { box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4), 0 16px 56px rgba(0, 0, 0, 0.2); }
    h1, h2, h3, h4 { color: #f1f5f9 !important; }
    .stat-card { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.06); }
    .stat-card .number { color: #f1f5f9; }
    .stat-card .label { color: #94a3b8; }
    .gr-textbox textarea, .gr-textbox input { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.08) !important; color: #e2e8f0 !important; }
    .gr-textbox textarea:focus, .gr-textbox input:focus { background: rgba(255, 255, 255, 0.08) !important; border-color: #818cf8 !important; }
    .gr-dropdown select { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.08) !important; color: #e2e8f0 !important; }
    .gr-dropdown select:focus { border-color: #818cf8 !important; }
    .tabs-nav { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.04); }
    .tabs-nav button { color: #94a3b8 !important; }
    .tabs-nav button:hover { background: rgba(255, 255, 255, 0.04) !important; color: #e2e8f0 !important; }
    .tabs-nav button.selected { background: rgba(255, 255, 255, 0.08) !important; color: #f1f5f9 !important; }
    .gr-file input[type="file"] { background: rgba(255, 255, 255, 0.04) !important; border-color: rgba(255, 255, 255, 0.08) !important; color: #94a3b8 !important; }
    .gr-radio label { color: #cbd5e1 !important; }
    .gr-button-secondary { background: rgba(255, 255, 255, 0.06) !important; border-color: rgba(255, 255, 255, 0.08) !important; color: #cbd5e1 !important; }
    .gr-button-secondary:hover { background: rgba(255, 255, 255, 0.1) !important; border-color: rgba(255, 255, 255, 0.12) !important; }
    .work-item { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.06); }
    .work-item .title { color: #e2e8f0; }
}
"""
