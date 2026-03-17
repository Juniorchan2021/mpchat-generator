import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. We need to restore the sidebar visibility and improve the UI based on Linear/Stripe style (Dark mode, glassmorphism, nice gradients).

# Let's check the CSS first
css_start = content.find("<style>")
css_end = content.find("</style>") + 8

new_css = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global Reset & Font */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0E0E11;
    color: #EDEDED;
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Linear/Stripe Dark Theme Overrides */
.stApp {
    background-color: #0E0E11;
    background-image: radial-gradient(circle at 50% 0%, #1a1a24 0%, #0E0E11 70%);
}

/* Banner with Stripe-like Gradient */
.mp-banner {
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 32px;
    display: flex; align-items: center; gap: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
    overflow: hidden;
}
.mp-banner::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.15), transparent 60%);
    z-index: 0; pointer-events: none;
}
.mp-banner > div { position: relative; z-index: 1; }
.mp-banner h1 { 
    color: #FFFFFF; font-size: 2.2rem; font-weight: 700; margin: 0; letter-spacing: -0.02em;
    background: linear-gradient(to right, #fff, #a5b4fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.mp-banner p  { color: #A1A1AA; font-size: 1rem; margin: 8px 0 0 0; font-weight: 400; }
.mp-badge {
    background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); color: #818CF8;
    border-radius: 20px; padding: 4px 12px; font-size: 0.75rem;
    font-weight: 600; display: inline-block; margin-top: 12px; letter-spacing: 0.05em; text-transform: uppercase;
}

/* Glassmorphism Cards (Linear style) */
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background: rgba(24, 24, 27, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2) !important;
    backdrop-filter: blur(12px) !important;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
    border-color: rgba(255, 255, 255, 0.15) !important;
}

/* Typography for labels */
.stMarkdown p { color: #D4D4D8; }
.stMarkdown strong { color: #F4F4F5; font-weight: 600; letter-spacing: -0.01em; }
.stCaption { color: #A1A1AA !important; font-size: 0.85rem !important; margin-bottom: 8px !important; }

/* Primary Button (Linear style) */
.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #6366F1 0%, #4F46E5 100%);
    color: white; font-weight: 600; border: none;
    border-radius: 8px; padding: 12px 24px; transition: all 0.2s ease;
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3), inset 0 1px 0 rgba(255,255,255,0.2);
    letter-spacing: 0.02em;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #818CF8 0%, #6366F1 100%);
    transform: translateY(-1px); box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4), inset 0 1px 0 rgba(255,255,255,0.2);
}

/* Secondary Button */
.stButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.05);
    color: #E4E4E7; font-weight: 500; border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px; transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2);
}

/* Inputs & Selectboxes */
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea {
    background-color: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    color: #F4F4F5 !important;
    transition: border-color 0.2s ease;
}
.stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within, .stTextArea textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.5) !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] { 
    background-color: #121217 !important; 
    border-right: 1px solid rgba(255,255,255,0.05) !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F4F4F5; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 16px;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: transparent !important;
    border: none !important;
    color: #D4D4D8 !important;
    font-weight: 500 !important;
}
.streamlit-expanderContent {
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    padding-top: 16px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px;
    color: #A1A1AA;
    padding: 8px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: #F4F4F5 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* Checkboxes */
.stCheckbox label span { color: #D4D4D8 !important; font-size: 0.9rem; }

/* Dividers */
hr { border-color: rgba(255,255,255,0.08) !important; margin: 32px 0 !important; }

/* Keyword Badges */
.kw-badge {
    display: inline-block; padding: 4px 10px; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600; margin-left: 4px;
}
.kw-low  { background: rgba(16, 185, 129, 0.1); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.2); }
.kw-med  { background: rgba(245, 158, 11, 0.1); color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.2); }
.kw-high { background: rgba(239, 68, 68, 0.1); color: #F87171; border: 1px solid rgba(248, 113, 113, 0.2); }

/* Score Ring */
.score-ring {
    display: inline-flex; align-items: center; justify-content: center;
    width: 64px; height: 64px; border-radius: 50%;
    font-size: 1.4rem; font-weight: 700;
    background: rgba(0,0,0,0.3);
    box-shadow: inset 0 0 0 4px currentColor;
}
</style>"""

content = content[:css_start] + new_css + content[css_end:]

# 2. Fix config.toml to be Dark Mode
import os
os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/config.toml", "w") as f:
    f.write("""[theme]
base = "dark"
primaryColor = "#6366F1"
backgroundColor = "#0E0E11"
secondaryBackgroundColor = "#18181B"
textColor = "#EDEDED"
font = "sans serif"

[client]
toolbarMode = "minimal"
""")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
