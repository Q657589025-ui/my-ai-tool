# AI Studio Pro — 企业级 AI 创作平台

基于 Gradio + SQLAlchemy + JWT，支持图片、视频、音乐、数字人、AI助手生成，多用户隔离，积分系统，任务队列。

## 部署
1. 安装依赖：`pip install -r requirements.txt`
2. 启动：`python app.py`
3. 访问：`http://localhost:7860`
4. 默认管理员：`admin / admin123`

## 结构
- `core/`：业务逻辑
- `ui/`：界面组件
- `config/`：配置文件
- `workers/`：后台任务（预留）

## 扩展
- 新模型：在 `config/models.json` 添加
- 新功能：在 `ui/tabs/` 新建 Tab
- 积分定价：修改 `config/price_map.py`
