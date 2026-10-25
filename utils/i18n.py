import streamlit as st
from utils.translations import TRANSLATIONS, LANGUAGES

def init_language():
    if "lang" not in st.session_state:
        st.session_state.lang = "vi"

def change_language():
    st.session_state.lang = st.session_state.lang_selector

def t(key):
    lang = st.session_state.get("lang", "vi")
    return TRANSLATIONS.get(lang, TRANSLATIONS["vi"]).get(key, key)

def render_language_selector():
    init_language()
    
    # CSS ĐỂ ÉP NHÃN VÀ Ô CHỌN NẰM NGANG, KHÔNG RỚT DÒNG
    st.markdown("""
    <style>
        /* Ẩn nhãn mặc định của Streamlit */
        div[data-testid="stSelectbox"] > label { display: none !important; }
        
        /* Làm đẹp ô chọn ngôn ngữ */
        div[data-testid="stSelectbox"] > div > div {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            width: 100% !important;
        }
        /* Chữ bên trong ô chọn */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #0f172a !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Tạo layout 1 hàng: Icon + Text + Selectbox
    col1, col2 = st.columns([1, 2], vertical_alignment="center")
    with col1:
        st.markdown("<div style='color: #0f172a; font-weight: 600; font-size: 0.95rem; padding-top: 5px;'>🌐 Language</div>", unsafe_allow_html=True)
    with col2:
        st.selectbox(
            "Language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            key="lang_selector",
            index=list(LANGUAGES.keys()).index(st.session_state.lang),
            on_change=change_language,
            label_visibility="collapsed"
        )
