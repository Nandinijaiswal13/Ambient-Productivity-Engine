import re
from html import escape
import streamlit as st

from database import (
    get_tasks,
    add_task,
    update_task_status,
    get_activities,
    add_activity,
    get_goals,
    add_goal,
    update_goal,
    get_reflections,
    add_reflection,
)

from llm import (
    generate_productivity_summary,
    generate_response,
    answer_common_question,
)

from rag_memory import search_personal_memory


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Ambient Productivity Engine",
    page_icon="🤖",
    layout="wide",
)

# ==================================================
# PROFESSIONAL FRONTEND THEME
# ==================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ==================================================
       PROFESSIONAL DARK THEME
       Neutral charcoal surfaces, one emerald accent, and
       semantic colours used only where they carry meaning.
       ================================================== */
    :root {
        color-scheme: dark;

        --bg: #0d0f12;
        --sidebar: #090b0e;
        --surface: #14171c;
        --surface-2: #191d23;
        --hover: #1f242b;
        --input: #0f1216;
        --popover: #181c22;
        --border: #252a32;
        --border-strong: #343a45;

        --text: #cdd3dc;
        --text-strong: #f3f5f8;
        --muted: #8a93a2;
        --placeholder: #5d6573;
        --track: #232830;

        --accent: #10b981;
        --accent-strong: #059669;
        --accent-hover: #34d399;
        --accent-text: #6ee7b7;
        --accent-soft: rgba(16, 185, 129, 0.12);
        --accent-ring: rgba(16, 185, 129, 0.34);

        --ok: #34d399;
        --warn: #fbbf24;
        --bad: #f87171;
        --info: #a78bfa;

        --shadow: 0 1px 2px rgba(0, 0, 0, 0.45),
                  0 12px 28px -14px rgba(0, 0, 0, 0.7);
        --shadow-lg: 0 20px 40px -16px rgba(0, 0, 0, 0.85);

        --radius: 14px;
        --radius-sm: 10px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    /* ==================================================
       BASE
       ================================================== */
    .stApp {
        background:
            radial-gradient(ellipse 55% 35% at 8% 0%, rgba(16, 185, 129, 0.10), transparent 70%),
            radial-gradient(ellipse 40% 30% at 100% 0%, rgba(167, 139, 250, 0.06), transparent 70%),
            var(--bg);
        background-attachment: fixed;
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(13, 15, 18, 0.75);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border);
    }

    [data-testid="stHeader"] * {
        color: var(--muted);
    }

    .block-container {
        padding-top: 2.4rem;
        padding-bottom: 3rem;
        max-width: 1140px;
        animation: fadeUp 0.4s ease both;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @media (prefers-reduced-motion: reduce) {
        .block-container { animation: none !important; }
    }

    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6,
    [data-testid="stMarkdownContainer"] strong {
        color: var(--text-strong);
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stText"],
    [data-testid="stText"] * {
        color: var(--text);
    }

    ::-webkit-scrollbar { width: 9px; height: 9px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2c323b; border-radius: 99px; }
    ::-webkit-scrollbar-thumb:hover { background: #3d4551; }

    ::selection {
        background: var(--accent-ring);
        color: #ffffff;
    }

    /* ==================================================
       SIDEBAR
       ================================================== */
    [data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    .brand {
        padding: 4px 6px 22px 6px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 22px;
    }

    .brand-icon {
        width: 46px;
        height: 46px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 13px;
        font-size: 23px;
        margin-bottom: 14px;
        box-shadow: 0 10px 22px -10px var(--accent),
                    inset 0 1px 0 rgba(255, 255, 255, 0.25);
    }

    .brand-name {
        color: var(--text-strong);
        font-size: 17.5px;
        font-weight: 700;
        letter-spacing: -0.4px;
        line-height: 1.3;
    }

    .brand-caption {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
        margin-top: 5px;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--accent-text);
        background: var(--accent-soft);
        border: 1px solid var(--accent-ring);
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        padding: 5px 13px;
        border-radius: 99px;
        margin-bottom: 14px;
    }

    [data-testid="stSidebar"] .eyebrow {
        background: transparent;
        border-color: var(--border-strong);
        color: var(--muted);
        margin-bottom: 10px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 3px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        padding: 11px 14px;
        border-radius: var(--radius-sm);
        border: 1px solid transparent;
        cursor: pointer;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {
        display: none;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label::before {
        font-size: 16px;
        width: 22px;
        text-align: center;
        opacity: 0.85;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(1)::before { content: "📊"; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(2)::before { content: "📋"; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(3)::before { content: "⏱️"; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(4)::before { content: "🎯"; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(5)::before { content: "📝"; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:nth-child(6)::before { content: "🧠"; }

    [data-testid="stSidebar"] [role="radiogroup"] > label p {
        color: var(--muted);
        font-size: 14px;
        font-weight: 500;
        margin: 0;
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {
        background: var(--hover);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:hover p {
        color: var(--text-strong);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
        background: var(--accent-soft);
        border-color: var(--accent-ring);
        box-shadow: inset 3px 0 0 var(--accent);
    }

    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {
        color: var(--accent-text);
        font-weight: 600;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--border);
    }

    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stSidebar"] button svg {
        color: var(--muted);
        fill: var(--muted);
    }

    /* ==================================================
       PAGE HEADER BANNER
       ================================================== */
    .hero-banner {
        position: relative;
        overflow: hidden;
        padding: 30px 34px 28px 34px;
        margin-bottom: 28px;
        border-radius: 18px;
        background:
            linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(16, 185, 129, 0.03) 55%),
            var(--surface);
        border: 1px solid var(--border-strong);
        box-shadow: var(--shadow);
    }

    .hero-banner::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--accent-hover), var(--accent-strong));
    }

    .hero-banner::after {
        content: "";
        position: absolute;
        width: 340px; height: 340px;
        right: -110px; top: -170px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.22), transparent 68%);
        pointer-events: none;
    }

    .hero-banner .eyebrow {
        position: relative;
    }

    .hero-title {
        position: relative;
        color: var(--text-strong);
        font-size: clamp(26px, 3vw, 36px);
        line-height: 1.15;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
        padding: 0;
    }

    .stApp p.hero-description {
        position: relative;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.7;
        margin: 10px 0 0 0;
        padding: 0;
        max-width: 720px;
        border: none;
    }

    .section-heading {
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--text-strong);
        font-size: 17.5px;
        font-weight: 700;
        letter-spacing: -0.3px;
        margin-top: 4px;
        margin-bottom: 4px;
    }

    .section-heading::before {
        content: "";
        width: 4px;
        height: 18px;
        border-radius: 4px;
        background: var(--accent);
    }

    .section-description {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 18px;
        padding-left: 14px;
    }

    /* ==================================================
       METRIC CARDS — neutral card, colour only on the icon
       ================================================== */
    [data-testid="stMetric"] {
        position: relative;
        overflow: hidden;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 22px 22px 20px 22px;
        min-height: 128px;
        box-shadow: var(--shadow);
        transition: transform 0.18s ease, border-color 0.18s ease,
                    box-shadow 0.18s ease;
        --metric: #10b981;
        --metric-soft: rgba(16, 185, 129, 0.14);
    }

    [data-testid="stMetric"]::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--metric);
    }

    [data-testid="stMetric"]::after {
        position: absolute;
        top: 20px;
        right: 18px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        border-radius: 12px;
        background: var(--metric-soft);
        border: 1px solid var(--border);
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: var(--border-strong);
        box-shadow: var(--shadow-lg);
    }

    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"]::after { content: "📋"; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"]::after { content: "✅"; }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"]::after { content: "⏳"; }
    [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"]::after { content: "⏱️"; }

    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"] { --metric: #10b981; --metric-soft: rgba(16, 185, 129, 0.14); }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] { --metric: #34d399; --metric-soft: rgba(52, 211, 153, 0.14); }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] { --metric: #fbbf24; --metric-soft: rgba(251, 191, 36, 0.14); }
    [data-testid="stHorizontalBlock"] > div:nth-child(4) [data-testid="stMetric"] { --metric: #a78bfa; --metric-soft: rgba(167, 139, 250, 0.14); }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {
        color: var(--muted) !important;
        font-size: 11.5px !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        color: var(--text-strong) !important;
        font-weight: 800;
        font-size: 34px !important;
        letter-spacing: -1px;
        font-variant-numeric: tabular-nums;
    }

    /* ==================================================
       CARDS & CONTAINERS
       ================================================== */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 8px 10px;
        box-shadow: var(--shadow);
        transition: border-color 0.18s ease;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--border-strong);
    }

    div[data-testid="stVerticalBlockBorderWrapper"]
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: none;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] h3 {
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.3px;
        color: var(--text-strong);
        padding-top: 0.2rem;
    }

    .record-card {
        position: relative;
        overflow: hidden;
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 14px 18px 14px 22px;
        margin: 9px 0;
        overflow-wrap: anywhere;
        transition: background 0.15s ease, border-color 0.15s ease,
                    transform 0.15s ease;
    }

    .record-card::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
        background: var(--accent);
    }

    .record-card:hover {
        background: var(--hover);
        border-color: var(--border-strong);
        transform: translateX(3px);
    }

    .record-title {
        color: var(--text-strong);
        font-size: 14.5px;
        font-weight: 600;
        margin-bottom: 6px;
    }

    .record-detail {
        color: var(--muted);
        font-size: 12.5px;
        line-height: 1.75;
    }

    .empty-state {
        background: var(--surface-2);
        border: 1px dashed var(--border-strong);
        border-radius: var(--radius);
        padding: 28px;
        color: var(--muted);
        font-size: 13.5px;
        line-height: 1.7;
        text-align: center;
    }

    /* ==================================================
       BUTTONS
       ================================================== */
    .stButton > button,
    .stFormSubmitButton > button {
        background: var(--accent-strong);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 14px;
        min-height: 44px;
        box-shadow: 0 8px 18px -10px var(--accent),
                    inset 0 1px 0 rgba(255, 255, 255, 0.12);
        transition: background 0.15s ease, transform 0.15s ease,
                    box-shadow 0.15s ease;
    }

    .stButton > button p,
    .stFormSubmitButton > button p {
        color: #ffffff !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--accent);
        color: #ffffff;
        border-color: rgba(255, 255, 255, 0.16);
        transform: translateY(-1px);
        box-shadow: 0 12px 22px -10px var(--accent);
    }

    .stButton > button:active,
    .stFormSubmitButton > button:active {
        transform: translateY(0);
    }

    .stButton > button:focus-visible,
    .stFormSubmitButton > button:focus-visible {
        outline: none;
        box-shadow: 0 0 0 3px var(--accent-ring);
    }

    /* ==================================================
       FORMS & INPUTS
       ================================================== */
    [data-testid="stForm"] {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 22px 22px 16px 22px;
    }

    [data-testid="stWidgetLabel"] p {
        color: var(--text);
        font-size: 13px;
        font-weight: 600;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input {
        background-color: var(--input) !important;
        color: var(--text-strong) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-sm);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-ring) !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--placeholder);
    }

    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="textarea"] {
        background-color: var(--input) !important;
    }

    .stNumberInput button {
        background: var(--hover);
        color: var(--text);
        border-color: var(--border-strong);
    }

    [data-baseweb="select"] > div {
        background-color: var(--input);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-sm);
        transition: border-color 0.15s ease;
    }

    [data-baseweb="select"] div,
    [data-baseweb="select"] span {
        color: var(--text-strong);
    }

    [data-baseweb="select"] svg {
        fill: var(--muted);
    }

    [data-baseweb="select"] > div:hover {
        border-color: var(--accent);
    }

    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] ul,
    [data-baseweb="menu"] {
        background: var(--popover);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-sm);
        box-shadow: var(--shadow-lg);
    }

    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li {
        color: var(--text);
    }

    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover {
        background: var(--accent-soft);
    }

    [data-baseweb="calendar"] {
        background: var(--popover);
        color: var(--text);
    }

    [data-baseweb="calendar"] button,
    [data-baseweb="calendar"] div {
        color: var(--text);
    }

    [data-testid="stSlider"] [role="slider"] {
        background: var(--accent);
        box-shadow: 0 0 0 5px var(--accent-ring);
    }

    [data-testid="stThumbValue"] {
        color: var(--accent-text);
        font-weight: 700;
    }

    [data-testid="stTickBarMin"],
    [data-testid="stTickBarMax"] {
        color: var(--muted);
    }

    /* ==================================================
       PROGRESS
       ================================================== */
    .stProgress > div > div {
        background-color: var(--track);
        border-radius: 99px;
        height: 9px;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-strong), var(--accent-hover));
        border-radius: 99px;
    }

    /* ==================================================
       EXPANDER, ALERTS, CHAT, JSON
       ================================================== */
    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow);
    }

    [data-testid="stExpander"] summary {
        font-weight: 600;
        color: var(--text-strong);
    }

    [data-testid="stExpander"] summary:hover {
        color: var(--accent-text);
        background: var(--hover);
    }

    [data-testid="stAlert"] {
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: var(--radius-sm);
    }

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] div {
        color: var(--text);
    }

    div[data-testid="stChatMessage"] {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface);
        padding: 14px;
        box-shadow: var(--shadow);
    }

    [data-testid="stJson"] {
        background: var(--input);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 10px 12px;
    }

    [data-testid="stJson"] span,
    [data-testid="stJson"] div {
        color: var(--text) !important;
    }

    /* ==================================================
       STATUS BADGES
       ================================================== */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: 0.2px;
        padding: 4px 11px;
        margin: 2px 8px 2px 0;
        border-radius: 99px;
        border: 1px solid transparent;
        line-height: 1.4;
    }

    .badge::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
    }

    .badge-success { color: var(--ok);   background: rgba(52, 211, 153, 0.10);  border-color: rgba(52, 211, 153, 0.28); }
    .badge-warn    { color: var(--warn); background: rgba(251, 191, 36, 0.10);  border-color: rgba(251, 191, 36, 0.28); }
    .badge-danger  { color: var(--bad);  background: rgba(248, 113, 113, 0.10); border-color: rgba(248, 113, 113, 0.28); }
    .badge-info    { color: var(--info); background: rgba(167, 139, 250, 0.10); border-color: rgba(167, 139, 250, 0.28); }
    .badge-neutral { color: var(--muted); background: var(--hover);             border-color: var(--border-strong); }

    /* ==================================================
       TEXT DETAILS & FOOTER
       ================================================== */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] *,
    [data-testid="stSpinner"] * {
        color: var(--muted);
    }

    .stMarkdown p, .stMarkdown li {
        line-height: 1.7;
    }

    code {
        background: var(--accent-soft);
        color: var(--accent-text);
        border-radius: 6px;
        padding: 2px 6px;
    }

    hr {
        border-color: var(--border);
    }

    .footer-note {
        text-align: center;
        color: var(--placeholder);
        font-size: 11.5px;
        letter-spacing: 0.5px;
        padding: 26px 0 8px 0;
        margin-top: 24px;
        border-top: 1px solid var(--border);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* ==================================================
       RESPONSIVE
       ================================================== */
    @media (max-width: 768px) {
        .block-container { padding-top: 1.5rem; }
        .hero-banner { padding: 24px 22px; border-radius: 16px; }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * { font-size: 28px !important; }
        .stApp p.hero-description { font-size: 14px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# REUSABLE FRONTEND COMPONENTS
# ==================================================

def page_header(title, description, icon):
    st.markdown(
        f"""
        <div class="hero-banner">
        <div class="eyebrow">{icon} &nbsp; PRODUCTIVITY WORKSPACE</div>
        <h1 class="hero-title">{title}</h1>
        <p class="hero-description">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, description=None):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )

    if description:
        st.markdown(
            f'<div class="section-description">{description}</div>',
            unsafe_allow_html=True,
        )


def record_card(title, details):
    st.markdown(
        f"""
        <div class="record-card">
            <div class="record-title">{title}</div>
            <div class="record-detail">{details}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message):
    st.markdown(
        f'<div class="empty-state">{message}</div>',
        unsafe_allow_html=True,
    )


BADGE_TONES = {
    "completed": "success", "good": "success",
    "excellent": "success", "low": "success",
    "pending": "warn", "medium": "warn", "okay": "warn",
    "in progress": "info",
    "high": "danger", "difficult": "danger",
}


def badge(text, tone_from=None):
    """Small coloured label. Display only."""
    tone = BADGE_TONES.get(
        str(tone_from).strip().lower(), "neutral"
    )
    return (
        f'<span class="badge badge-{tone}">'
        f'{escape(str(text))}</span>'
    )


# ==================================================
# SAFE VALUE HELPERS — ORIGINAL LOGIC PRESERVED
# ==================================================

def value(record, *keys, default=None):
    """Read a value from a dictionary or SQLite Row."""

    for key in keys:
        try:
            result = record[key]
            if result is not None:
                return result
        except (KeyError, IndexError, TypeError):
            continue

    return default


def task_name(task):
    return value(
        task, "title", "task_name", "name",
        default="Untitled task"
    )


def goal_name(goal):
    return value(
        goal, "title", "goal_name", "name",
        default="Untitled goal"
    )


def activity_name(activity):
    return value(
        activity,
        "activity_type",
        "activity_name",
        "name",
        "title",
        default="Activity",
    )


def activity_minutes(activity):
    duration = value(
        activity,
        "duration_minutes",
        "duration",
        "minutes",
        default=0,
    )

    try:
        return int(duration)
    except (ValueError, TypeError):
        return 0


def task_is_completed(task):
    return (
        str(value(task, "status", default=""))
        .strip()
        .lower() == "completed"
    )


def goal_progress(goal):
    progress = value(goal, "progress", default=0)

    try:
        return float(str(progress).replace("%", ""))
    except (ValueError, TypeError):
        return 0.0


def goal_is_completed(goal):
    status = (
        str(value(goal, "status", default=""))
        .strip()
        .lower()
    )

    return status == "completed" or goal_progress(goal) >= 100


def format_duration(minutes):
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours and remaining_minutes:
        return f"{hours}h {remaining_minutes}m"
    if hours:
        return f"{hours}h"

    return f"{remaining_minutes}m"


def record_text(record, *fields):
    values = []

    for field in fields:
        item = value(record, field, default=None)

        if item is not None and str(item).strip():
            values.append(f"{field}: {item}")

    return " | ".join(values)


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">🤖</div>
            <div class="brand-name">Ambient Productivity Engine</div>
            <div class="brand-caption">
                Your personal productivity workspace
            </div>
        </div>
        <div class="eyebrow">WORKSPACE MENU</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Tasks",
            "Activities",
            "Goals",
            "Reflections",
            "AI Memory Chat",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        <div class="record-card">
            <div class="record-title">✨ Daily reminder</div>
            <div class="record-detail">
                Small, consistent actions create meaningful progress.
                Plan your day, track your efforts, and reflect on what
                you learn.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    page_header(
        "Your Productivity Dashboard",
        "Review your productivity and get recommendations based on your saved records.",
        "📊",
    )

    tasks = get_tasks()
    activities = get_activities()
    goals = get_goals()
    reflections = get_reflections()

    completed_tasks = sum(
        1 for task in tasks if task_is_completed(task)
    )

    pending_tasks = len(tasks) - completed_tasks

    total_activity_minutes = sum(
        activity_minutes(activity)
        for activity in activities
    )

    productivity_score = (
        completed_tasks / len(tasks) * 100
        if tasks else 0
    )

    # METRICS — SAME VALUES AND CALCULATIONS

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tasks", len(tasks))
    col2.metric("Completed Tasks", completed_tasks)
    col3.metric("Pending Tasks", pending_tasks)
    col4.metric(
        "Recorded Focus Time",
        format_duration(total_activity_minutes),
    )

    st.write("")

    # RECENT TASKS

    with st.container(border=True):
        section_heading(
            "📋 Recent Tasks",
            "Your latest tasks and their current status.",
        )

        if tasks:
            for task in tasks[-5:][::-1]:
                title = task_name(task)
                status = value(task, "status", default="Pending")
                priority = value(
                    task, "priority", default="Not specified"
                )

                record_card(
                    str(title),
                    badge(f"Status: {status}", status)
                    + badge(f"Priority: {priority}", priority),
                )
        else:
            empty_state("No tasks have been recorded yet.")

    st.write("")

    # GOALS

    with st.container(border=True):
        section_heading(
            "🎯 Goal Progress",
            "Monitor your progress toward your saved goals.",
        )

        if goals:
            for goal in goals:
                progress = goal_progress(goal)

                st.markdown(
                    f"**{goal_name(goal)}**"
                )

                st.caption(f"{progress:g}% complete")

                st.progress(
                    min(max(progress / 100, 0.0), 1.0)
                )
        else:
            empty_state("No goals have been recorded yet.")

    st.write("")

    # ACTIVITIES

    with st.container(border=True):
        section_heading(
            "⏱️ Recorded Activities",
            "A recent view of how you have invested your time.",
        )

        if activities:
            for activity in activities[-10:][::-1]:
                name = activity_name(activity)
                duration = activity_minutes(activity)
                date = value(
                    activity, "date", default="Date not recorded"
                )

                record_card(
                    str(name),
                    f"{duration} minutes &nbsp; · &nbsp; {date}",
                )
        else:
            empty_state("No activities have been recorded yet.")

    st.write("")

    # REFLECTION DEBUG PANEL — PRESERVED

    with st.expander("🔍 Debug: Check saved reflection data"):

        st.write("Number of reflections:", len(reflections))

        if reflections:
            for reflection in reflections:
                st.write({
                    "date": value(reflection, "date", default=""),
                    "mood": value(reflection, "mood", default=""),
                    "energy_level": value(
                        reflection, "energy_level", default=""
                    ),
                    "accomplishments": value(
                        reflection, "accomplishments", default=""
                    ),
                    "challenges": value(
                        reflection, "challenges", default=""
                    ),
                    "learnings": value(
                        reflection, "learnings", default=""
                    ),
                    "tomorrow_focus": value(
                        reflection, "tomorrow_focus", default=""
                    ),
                })
        else:
            st.warning(
                "No reflections were returned by get_reflections()."
            )

    # AI PRODUCTIVITY SUMMARY — ORIGINAL LOGIC PRESERVED

    with st.container(border=True):
        section_heading(
            "🧠 Your AI Productivity Summary",
            "Generate a personalized report from your saved productivity records.",
        )

        if st.button(
            "✨ Generate My Productivity Summary",
            use_container_width=True,
        ):

            with st.spinner(
                "Analyzing your saved productivity records..."
            ):
                try:
                    summary = generate_productivity_summary(
                        tasks=tasks,
                        activities=activities,
                        goals=goals,
                        reflections=reflections,
                        focus_time=total_activity_minutes,
                        productivity_score=productivity_score,
                    )

                    if summary:
                        st.markdown(summary)
                    else:
                        st.warning("The AI returned an empty summary.")

                    st.caption(
                        f"Based on {len(tasks)} tasks, "
                        f"{len(activities)} activities, "
                        f"{len(goals)} goals, and "
                        f"{len(reflections)} reflections."
                    )

                except Exception as error:
                    st.error(
                        f"Unable to generate productivity summary: {error}"
                    )


# ==================================================
# TASKS PAGE
# ==================================================

elif page == "Tasks":

    page_header(
        "Task Manager",
        "Organize your workload, set priorities, and track what needs to get done.",
        "📋",
    )

    with st.container(border=True):
        section_heading(
            "Create a Task",
            "Add a task to your personal task list.",
        )

        with st.form("add_task_form"):

            title = st.text_input("Task title")
            description = st.text_area("Description")

            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High"],
            )

            deadline = st.date_input("Deadline")

            estimated_minutes = st.number_input(
                "Estimated time (minutes)",
                min_value=0,
                value=30,
            )

            submitted = st.form_submit_button("Add Task")

            if submitted:
                if not title.strip():
                    st.warning("Please enter a task title.")
                else:
                    try:
                        add_task(
                            title=title.strip(),
                            description=description,
                            priority=priority,
                            deadline=str(deadline),
                            estimated_minutes=int(estimated_minutes),
                        )

                        st.success("Task added successfully.")
                        st.rerun()

                    except Exception as error:
                        st.error(f"Unable to add task: {error}")

    st.write("")

    section_heading("Your Tasks", "Review and update your saved tasks.")

    tasks = get_tasks()

    if tasks:
        for task in tasks:
            task_id = value(task, "id")
            title = task_name(task)
            status = value(task, "status", default="Pending")
            priority = value(
                task, "priority", default="Not specified"
            )

            with st.container(border=True):
                st.markdown(f"### {title}")

                col1, col2 = st.columns(2)
                col1.markdown(
                    badge(f"Priority: {priority}", priority),
                    unsafe_allow_html=True,
                )
                col2.markdown(
                    badge(f"Status: {status}", status),
                    unsafe_allow_html=True,
                )

                description = value(
                    task, "description", default=""
                )

                if description:
                    st.write(description)

                if str(status).lower() != "completed":
                    if st.button(
                        "✓ Mark Completed",
                        key=f"complete_task_{task_id}",
                    ):
                        try:
                            update_task_status(
                                task_id, "Completed"
                            )

                            st.success(
                                "Task marked as completed."
                            )
                            st.rerun()

                        except Exception as error:
                            st.error(
                                f"Unable to update task: {error}"
                            )
    else:
        empty_state("No tasks recorded yet.")


# ==================================================
# ACTIVITIES PAGE
# ==================================================

elif page == "Activities":

    page_header(
        "Activity Tracker",
        "Record your study sessions, project work, and other activities.",
        "⏱️",
    )

    with st.container(border=True):
        section_heading(
            "Record an Activity",
            "Capture the time you spend on your work.",
        )

        with st.form("add_activity_form"):

            activity_type = st.text_input("Activity name")

            duration_minutes = st.number_input(
                "Duration in minutes",
                min_value=1,
                value=30,
            )

            activity_date = st.date_input("Activity date")
            description = st.text_area("What did you work on?")

            submitted = st.form_submit_button("Record Activity")

            if submitted:
                if not activity_type.strip():
                    st.warning("Please enter an activity name.")
                else:
                    try:
                        add_activity(
                            activity_name=activity_type.strip(),
                            duration=int(duration_minutes),
                            activity_date=str(activity_date),
                            description=description,
                        )

                        st.success("Activity recorded successfully.")
                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Unable to record activity: {error}"
                        )

    st.write("")
    section_heading(
        "Activity History",
        "Review your recorded activity sessions.",
    )

    activities = get_activities()

    if activities:
        for activity in activities[::-1]:
            with st.container(border=True):
                st.markdown(f"**{activity_name(activity)}**")

                st.caption(
                    f"{activity_minutes(activity)} minutes"
                )

                st.caption(
                    str(value(
                        activity, "date", default="Date not recorded"
                    ))
                )

                description = value(
                    activity, "description", default=""
                )

                if description:
                    st.write(description)
    else:
        empty_state("No activities recorded yet.")


# ==================================================
# GOALS PAGE
# ==================================================

elif page == "Goals":

    page_header(
        "Goal Tracker",
        "Turn your ambitions into milestones and monitor your progress.",
        "🎯",
    )

    with st.container(border=True):
        section_heading(
            "Create a Goal",
            "Define an outcome and set a target deadline.",
        )

        with st.form("add_goal_form"):

            title = st.text_input("Goal title")
            description = st.text_area("Description")
            deadline = st.date_input("Deadline")

            progress = st.slider(
                "Initial progress (%)",
                min_value=0,
                max_value=100,
                value=0,
            )

            submitted = st.form_submit_button("Add Goal")

            if submitted:
                if not title.strip():
                    st.warning("Please enter a goal title.")
                else:
                    try:
                        # ORIGINAL DATABASE OPERATIONS PRESERVED

                        add_goal(
                            title=title.strip(),
                            description=description,
                            deadline=str(deadline),
                        )

                        goals_after_add = get_goals()

                        if not goals_after_add:
                            raise RuntimeError(
                                "The goal was not returned after saving."
                            )

                        newest_goal = max(
                            goals_after_add,
                            key=lambda goal: value(
                                goal, "id", default=0
                            )
                        )

                        update_goal(
                            value(newest_goal, "id"),
                            int(progress),
                        )

                        st.success("Goal added successfully.")
                        st.rerun()

                    except Exception as error:
                        st.error(f"Unable to add goal: {error}")

    st.write("")
    section_heading(
        "Your Goals",
        "Track progress toward each of your milestones.",
    )

    goals = get_goals()

    if goals:
        for goal in goals:
            goal_id = value(goal, "id")
            title = goal_name(goal)
            progress = goal_progress(goal)

            with st.container(border=True):
                st.markdown(f"### {title}")

                st.progress(
                    min(max(progress / 100, 0.0), 1.0)
                )

                st.caption(f"Current progress: {progress:g}%")

                description = value(
                    goal, "description", default=""
                )

                if description:
                    st.write(description)

                new_progress = st.slider(
                    f"Update progress — {title}",
                    min_value=0,
                    max_value=100,
                    value=int(min(max(progress, 0), 100)),
                    key=f"goal_progress_{goal_id}",
                )

                if st.button(
                    "Save Progress",
                    key=f"save_goal_{goal_id}",
                ):
                    try:
                        update_goal(goal_id, new_progress)

                        st.success("Goal progress updated.")
                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Unable to update goal: {error}"
                        )
    else:
        empty_state("No goals recorded yet.")


# ==================================================
# REFLECTIONS PAGE
# ==================================================

elif page == "Reflections":

    page_header(
        "Daily Reflections",
        "Recognize your progress, capture lessons, and plan your next steps.",
        "📝",
    )

    with st.container(border=True):
        section_heading(
            "Write a Reflection",
            "Take a moment to review your day.",
        )

        with st.form("reflection_form"):

            reflection_date = st.date_input("Date")

            mood = st.selectbox(
                "How was your day?",
                ["Excellent", "Good", "Okay", "Difficult"],
            )

            energy_level = st.slider(
                "Energy level",
                min_value=1,
                max_value=5,
                value=3,
            )

            accomplishments = st.text_area(
                "What did you accomplish today?"
            )

            challenges = st.text_area(
                "What challenges did you face?"
            )

            learnings = st.text_area(
                "What did you learn today?"
            )

            tomorrow_focus = st.text_area(
                "What will you focus on tomorrow?"
            )

            submitted = st.form_submit_button("Save Reflection")

            if submitted:
                try:
                    # ORIGINAL DATABASE CALL PRESERVED

                    add_reflection(
                        date=str(reflection_date),
                        mood=mood,
                        energy_level=int(energy_level),
                        accomplishments=accomplishments,
                        challenges=challenges,
                        learnings=learnings,
                        tomorrow_focus=tomorrow_focus,
                    )

                    st.success("Reflection saved successfully.")
                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Unable to save reflection: {error}"
                    )

    st.write("")
    section_heading(
        "Reflection History",
        "Revisit your past reflections and learnings.",
    )

    reflections = get_reflections()

    if reflections:
        for reflection in reflections[::-1]:
            date = value(
                reflection, "date", default="Unknown date"
            )

            with st.container(border=True):
                st.markdown(f"### 📝 Reflection — {date}")

                col1, col2 = st.columns(2)

                mood_value = value(
                    reflection, "mood",
                    default="Not recorded"
                )

                col1.markdown(
                    badge("Mood: " + str(mood_value), mood_value),
                    unsafe_allow_html=True,
                )

                col2.markdown(
                    badge("Energy: " + str(value(
                        reflection, "energy_level",
                        default="Not recorded"
                    ))),
                    unsafe_allow_html=True,
                )

                st.divider()

                st.markdown("**Accomplishments**")
                st.write(value(
                    reflection, "accomplishments",
                    default="Not recorded"
                ))

                st.markdown("**Challenges**")
                st.write(value(
                    reflection, "challenges",
                    default="Not recorded"
                ))

                st.markdown("**Learnings**")
                st.write(value(
                    reflection, "learnings",
                    default="Not recorded"
                ))

                st.markdown("**Tomorrow's focus**")
                st.write(value(
                    reflection, "tomorrow_focus",
                    default="Not recorded"
                ))
    else:
        empty_state("No reflections recorded yet.")


# ==================================================
# AI MEMORY CHAT
# ==================================================

elif page == "AI Memory Chat":

    page_header(
        "AI Personal Memory Chat",
        "Ask questions about your saved tasks, activities, goals, and reflections.",
        "🧠",
    )

    with st.container(border=True):
        section_heading(
            "Your Personal AI Assistant",
            "Ask a question about your saved productivity history.",
        )

        st.write(
            "Answers use retrieved memories and your configured local AI model."
        )

        question = st.text_input(
            "Ask a question about your productivity history",
            placeholder="What did I learn on October 9, 2026?",
            key="memory_question",
        )

        if st.button(
            "🔍 Ask AI",
            key="ask_memory_ai",
            use_container_width=True,
        ):

            if not question.strip():
                st.warning("Please enter a question.")

            else:
                with st.spinner("Searching your personal memories..."):

                    try:
                        # ORIGINAL MEMORY AND AI LOGIC PRESERVED

                        memories = search_personal_memory(question)
                        st.write("**Question received by app:**", question)

                        # NORMALIZE RETRIEVED MEMORIES

                        context_parts = []

                        if isinstance(memories, str):
                            if memories.strip():
                                context_parts.append(memories)

                        elif isinstance(memories, dict):
                            memory_text = (
                                memories.get("text")
                                or memories.get("content")
                                or memories.get("document")
                                or ""
                            )

                            if memory_text:
                                context_parts.append(str(memory_text))

                        elif memories:
                            for memory in memories:
                                if isinstance(memory, dict):
                                    memory_text = (
                                        memory.get("text")
                                        or memory.get("content")
                                        or memory.get("document")
                                        or ""
                                    )

                                    if memory_text:
                                        context_parts.append(
                                            str(memory_text)
                                        )

                                elif memory:
                                    context_parts.append(str(memory))

                        context = "\n\n".join(context_parts).strip()

                        if not context:
                            st.warning(
                                "No relevant memories were returned. "
                                "Check that your records have been "
                                "indexed in ChromaDB."
                            )

                        else:
                            with st.expander(
                                "📚 View retrieved memories"
                            ):
                                st.text(context)

                            # ORIGINAL ANSWER GENERATION PRESERVED

                            answer = answer_common_question(
                                question,
                                context,
                            )

                            if answer is None:
                                answer = generate_response(
                                    question,
                                    context=context,
                                )

                            st.subheader("💬 AI Answer")
                            st.markdown(answer)

                    except Exception as error:
                        st.error(
                            f"Unable to answer your question: {error}"
                        )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    """
    <div class="footer-note">
        LLM-Driven Ambient Productivity and Reflection Engine
    </div>
    """,
    unsafe_allow_html=True,
)