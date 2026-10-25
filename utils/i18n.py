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
    
    # CSS FIX LỖI CHỮ MỜ BẰNG CÁCH ÉP NỀN TRẮNG VÀ CHỮ ĐEN
    st.markdown("""
    <style>
        /* 1. Sửa phần Nhãn (Language / Ngôn ngữ): Nền trắng, chữ đen đậm */
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stSelectbox label p,
        [data-testid="stSidebar"] .stSelectbox [data-testid="stWidgetLabel"] {
            color: #000000 !important; /* Chữ màu đen tuyền */
            background-color: #ffffff !important; /* Nền trắng để nổi bật trên sidebar tối */
            font-weight: 800 !important; /* In đậm */
            font-size: 1rem !important;
            padding: 6px 10px !important;
            border-radius: 6px !important;
            margin-bottom: 8px !important;
            display: inline-block !important;
            width: 100% !important;
        }

        /* 2. Sửa phần Ô chọn (Nền trắng, viền xám) */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important; 
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        /* 3. Sửa phần chữ bên trong ô chọn thành màu đen đậm */
        [data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #000000 !important; 
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.selectbox(
        "🌐 Language / Ngôn ngữ",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang_selector",
        index=list(LANGUAGES.keys()).index(st.session_state.lang),
        on_change=change_language
    )
