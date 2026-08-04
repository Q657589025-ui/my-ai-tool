# ui/main.py 已正确传递 user_id_state 给每个 Tab
def create_main_tabs(user_id_state):
    with gr.Tabs() as tabs:
        with gr.TabItem("🏠 首页"):
            create_dashboard_tab(user_id_state)
        with gr.TabItem("🎨 图片"):
            create_image_tab(user_id_state)
        # ... 其他 Tab
    return tabs
