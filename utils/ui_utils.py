import streamlit as st

def apply_custom_css():
    """Áp dụng CSS toàn cục để làm đẹp giao diện."""
    st.markdown("""
    <style>
        /* Nhúng Font chữ hiện đại (Inter) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Ẩn các thành phần mặc định của Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Tùy chỉnh khoảng cách */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }

        /* 1. SIDEBAR TỐI MÀU (Dark Theme) */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b;
        }
        [data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }
        /* Nút điều hướng trong sidebar */
        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            margin: 4px 12px;
            padding: 10px;
        }
        [data-testid="stSidebarNav"] a:hover {
            background-color: #1e293b !important;
        }

        /* 2. NÚT BẤM (Buttons) */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid #cbd5e1;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .stButton > button:hover {
            border-color: #3b82f6;
            color: #3b82f6;
        }
        /* Nút Primary (Nút chính) */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
            color: white !important;
            border: none;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
            box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.4);
        }

        /* 3. Ô NHẬP LIỆU (Input, Selectbox) */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            transition: border-color 0.2s ease;
        }
        .stTextInput > div > div > input:focus, 
        .stTextArea > div > div > textarea:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
        }

        /* 4. THẺ (Cards) & CONTAINER CÓ VIỀN */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            transition: transform 0.2s ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        /* 5. TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            background-color: #f8fafc;
            padding: 8px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            color: #64748b;
            transition: all 0.3s ease;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #2563eb !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        /* 6. HỘP THOẠI (Dialog Modal) */
        [data-testid="stDialog"] > div {
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            border: none;
        }

        /* 7. THẺ THÔNG BÁO KẾT QUẢ (Dùng cho trang người dân) */
        .result-card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            border-left: 6px solid #10b981;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        .result-card.error {
            border-left-color: #ef4444;
        }
        .result-card h3 {
            margin-top: 0;
            color: #0f172a;
        }
    </style>
    """, unsafe_allow_html=True)
