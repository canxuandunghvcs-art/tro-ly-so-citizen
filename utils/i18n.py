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
    
    # CSS ÉP THANH NGÔN NGỮ GỌN GÀNG
    st.markdown("""
    <style>
        /* Ẩn label mặc định */
        div[data-testid="stSelectbox"] > label { display: none !important; }
        
        /* Làm gọn ô selectbox */
        div[data-testid="stSelectbox"] > div > div {
            background-color: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            min-height: 38px !important;
        }
        /* Màu chữ bên trong */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
            color: #0f172a !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.selectbox(
        "Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang_selector",
        index=list(LANGUAGES.keys()).index(st.session_state.lang),
        on_change=change_language,
        label_visibility="collapsed"
    )
