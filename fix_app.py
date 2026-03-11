import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Clean up CSS
old_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Card UI */
.sv-card {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 24px;
}

.sv-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Banner */
.mp-banner {
    background: #111827;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.mp-banner h1 { color: #f9fafb; font-size: 1.8rem; font-weight: 700; margin: 0; }
.mp-banner p  { color: #9ca3af; font-size: 0.95rem; margin: 4px 0 0 0; }
.mp-badge {
    background: #374151; border: 1px solid #4b5563; color: #d1d5db;
    border-radius: 20px; padding: 3px 12px; font-size: 0.75rem;
    font-weight: 600; display: inline-block; margin-top: 8px;
}

/* Primary Button */
.stButton > button[kind="primary"] {
    background: #000000;
    color: white; font-weight: 600; border: none;
    border-radius: 8px; padding: 12px 0; transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    background: #374151;
    transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Secondary Button */
.stButton > button[kind="secondary"] {
    background: #ffffff;
    color: #111827; font-weight: 500; border: 1px solid #d1d5db;
    border-radius: 8px; transition: all 0.2s;
}
.stButton > button[kind="secondary"]:hover {
    background: #f3f4f6; border-color: #9ca3af;
}

/* Segmented Control Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #f3f4f6;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px;
    color: #4b5563;
    padding: 8px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #111827 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* Output Card Title */
.output-card-title {
    color: #111827; font-size: 1rem; font-weight: 600;
    margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #e5e7eb; padding-bottom: 12px;
}

/* Score Ring */
.score-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 64px; height: 64px; border-radius: 50%;
    font-size: 1.4rem; font-weight: 700;
    background: #ffffff;
    box-shadow: inset 0 0 0 4px currentColor;
}

/* SEO Box */
.seo-title-box {
    background: #f9fafb; border-left: 3px solid #111827;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    color: #111827; font-size: 1.05rem; font-weight: 600; margin-bottom: 8px;
}
.seo-desc-box {
    background: #f3f4f6; border-radius: 8px; padding: 12px 16px;
    color: #4b5563; font-size: 0.9rem; line-height: 1.6;
}

/* Image Prompt */
.image-prompt-block {
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 10px;
    font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 0.85rem;
    color: #111827; line-height: 1.6;
}
.image-prompt-label { color: #6b7280; font-weight: 600; font-size: 0.75rem; margin-bottom: 6px; display: block; text-transform: uppercase; letter-spacing: 0.05em; }
.image-prompt-cn { color: #6b7280; font-size: 0.8rem; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb; }

/* Sidebar */
[data-testid="stSidebar"] { background: #f9fafb; border-right: 1px solid #e5e7eb; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #111827; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
}

.kw-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.7rem; font-weight: 600; margin-left: 4px;
}
.kw-low  { background: #dcfce7; color: #065f46; border: 1px solid #bbf7d0; }
.kw-med  { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.kw-high { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

hr { border-color: #e5e7eb; }
</style>"""

new_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Banner */
.mp-banner {
    background: #111827;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
.mp-banner h1 { color: #f9fafb; font-size: 1.8rem; font-weight: 700; margin: 0; }
.mp-banner p  { color: #9ca3af; font-size: 0.95rem; margin: 4px 0 0 0; }
.mp-badge {
    background: #374151; border: 1px solid #4b5563; color: #d1d5db;
    border-radius: 20px; padding: 3px 12px; font-size: 0.75rem;
    font-weight: 600; display: inline-block; margin-top: 8px;
}

/* Primary Button */
.stButton > button[kind="primary"] {
    background: #000000;
    color: white; font-weight: 600; border: none;
    border-radius: 8px; padding: 12px 0; transition: all 0.2s;
}
.stButton > button[kind="primary"]:hover {
    background: #374151;
    transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Secondary Button */
.stButton > button[kind="secondary"] {
    background: #ffffff;
    color: #111827; font-weight: 500; border: 1px solid #d1d5db;
    border-radius: 8px; transition: all 0.2s;
}
.stButton > button[kind="secondary"]:hover {
    background: #f3f4f6; border-color: #9ca3af;
}

/* Segmented Control Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #f3f4f6;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px;
    color: #4b5563;
    padding: 8px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #111827 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* Output Card Title */
.output-card-title {
    color: #111827; font-size: 1rem; font-weight: 600;
    margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #e5e7eb; padding-bottom: 12px;
}

/* Score Ring */
.score-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 64px; height: 64px; border-radius: 50%;
    font-size: 1.4rem; font-weight: 700;
    background: #ffffff;
    box-shadow: inset 0 0 0 4px currentColor;
}

/* SEO Box */
.seo-title-box {
    background: #f9fafb; border-left: 3px solid #111827;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    color: #111827; font-size: 1.05rem; font-weight: 600; margin-bottom: 8px;
}
.seo-desc-box {
    background: #f3f4f6; border-radius: 8px; padding: 12px 16px;
    color: #4b5563; font-size: 0.9rem; line-height: 1.6;
}

/* Image Prompt */
.image-prompt-block {
    background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 10px;
    font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 0.85rem;
    color: #111827; line-height: 1.6;
}
.image-prompt-label { color: #6b7280; font-weight: 600; font-size: 0.75rem; margin-bottom: 6px; display: block; text-transform: uppercase; letter-spacing: 0.05em; }
.image-prompt-cn { color: #6b7280; font-size: 0.8rem; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb; }

/* Sidebar */
[data-testid="stSidebar"] { background: #f9fafb; border-right: 1px solid #e5e7eb; }
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #111827; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
}

hr { border-color: #e5e7eb; }
</style>"""

content = content.replace(old_css, new_css)

# 2. Replace the layout part
layout_start = content.find("# ══════════════════════════════════════════════════════════════════════════════\n# 主区域 — 配置面板")
layout_end = content.find("# ══════════════════════════════════════════════════════════════════════════════\n# 生成按钮")

new_layout = """# ══════════════════════════════════════════════════════════════════════════════
# 主区域 — 配置面板
# ══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown("**📝 内容配置**")
    col_lang, col_cat, col_scen, col_style = st.columns(4)

    with col_lang:
        st.caption("🌐 输出语言")
        lang_options = list(LANGUAGES.keys())
        language = st.selectbox("输出语言", lang_options, index=0, label_visibility="collapsed")

    with col_cat:
        st.caption("🎯 场景分类")
        category_names = list(SCENARIO_CATEGORIES.keys())
        selected_category = st.selectbox("场景分类", category_names, index=0, label_visibility="collapsed")
        scenarios_in_cat = SCENARIO_CATEGORIES[selected_category]
        scenario_labels = [s["label"] for s in scenarios_in_cat]

    with col_scen:
        st.caption("📄 具体场景")
        selected_scenario_label = st.selectbox("具体场景", scenario_labels, index=0, label_visibility="collapsed")
        selected_scenario = next(s for s in scenarios_in_cat if s["label"] == selected_scenario_label)

    with col_style:
        st.caption("✍️ 文章文风")
        style_hint = selected_scenario.get("style_hint", "pain_story")
        style_keys = list(ARTICLE_STYLES.keys())
        hint_index = 0
        for i, k in enumerate(style_keys):
            if ARTICLE_STYLES[k]["id"] == style_hint:
                hint_index = i
                break
        selected_style_key = st.selectbox(
            "文风",
            style_keys,
            index=hint_index,
            label_visibility="collapsed",
            format_func=lambda k: f"{k}",
        )
        style_obj = ARTICLE_STYLES[selected_style_key]

with st.container(border=True):
    st.markdown("**💎 主打卖点 (可多选)**")
    auto_sp = set(selected_scenario.get("selling_points", []))
    if "sp_overrides" not in st.session_state:
        st.session_state["sp_overrides"] = {}

    selected_sp_ids: list[str] = []
    sp_cols = st.columns(len(SELLING_POINT_GROUPS))
    for i, (group_name, items) in enumerate(SELLING_POINT_GROUPS.items()):
        with sp_cols[i]:
            st.caption(f"{group_name}")
            for sp_id, sp_label in items.items():
                default_val = sp_id in auto_sp
                override_key = f"sp_{sp_id}"
                checked = st.checkbox(sp_label, value=default_val, key=override_key)
                if checked:
                    selected_sp_ids.append(sp_id)

    selling_points_text = "、".join(
        SP_ID_TO_LABEL.get(sid, sid) for sid in selected_sp_ids
    ) if selected_sp_ids else "MPChat 全功能"

with st.container(border=True):
    st.markdown("**🔍 SEO 关键词**")
    st.caption("点击预设快速填充，或手动编辑（将被自然植入文章正文，提升 SEO 表现）")

    preset_cols = st.columns(len(KEYWORD_PRESETS))
    for i, preset in enumerate(KEYWORD_PRESETS):
        with preset_cols[i]:
            if st.button(f"{preset['label']}", key=f"kw_preset_{i}", use_container_width=True):
                st.session_state["keywords_val"] = preset["keywords"]

    scenario_kw = selected_scenario.get("keywords", "")
    default_kw = st.session_state.get("keywords_val", scenario_kw)

    keywords = st.text_area(
        "关键词（3-5个）",
        value=default_kw,
        height=60,
        label_visibility="collapsed",
    )

"""

content = content[:layout_start] + new_layout + content[layout_end:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
