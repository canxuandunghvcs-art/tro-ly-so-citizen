"""Cổng công dân – Giao diện Dark Mode, Tách biệt thẻ tài liệu."""
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD
from utils.i18n import t, render_language_selector

st.set_page_config(page_title="Citizen Portal", page_icon="🛡️", layout="wide")

# 1. ẨN SIDEBAR & CSS TOÀN CỤC
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stAppViewContainer"] {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        font-family: 'Inter', sans-serif;
    }
    .block-container { max-width: 900px !important; padding-top: 2rem !important; }

    /* ==========================================
       FIX LỖI PHÂN CÁCH: THÊM VIỀN XANH BÊN TRÁI
       ========================================== */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: #ffffff; 
        border-radius: 8px; 
        border: 1px solid #e2e8f0;
        border-left: 5px solid #3b82f6; /* Vạch xanh phân cách cực đẹp */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        padding: 1.2rem; 
        margin-bottom: 1.2rem; /* Tăng khoảng cách giữa các thẻ */
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #1e293b; padding: 8px; border-radius: 12px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; color: #94a3b8; font-weight: 600; font-size: 1.15rem !important; padding: 10px 24px; border: none; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: white !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); }

    /* Nút Tải Về (HTML) */
    .action-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #eff6ff;
        color: #2563eb !important;
        border: 1.5px solid #bfdbfe;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        text-decoration: none !important;
        transition: all 0.2s ease;
        cursor: pointer;
        width: 100%;
        box-sizing: border-box;
    }
    .action-btn:hover {
        background-color: #dbeafe;
        border-color: #93c5fd;
        color: #1e40af !important;
    }

    /* Xóa nền trắng của Checkbox và căn giữa */
    div[data-testid="stCheckbox"] { 
        margin: 0 !important; 
        padding: 0 !important; 
        background: transparent !important; 
        display: flex;
        align-items: center;
        height: 100%;
    }
    div[data-testid="stCheckbox"] label {
        background: transparent !important;
        padding: 0 !important;
    }
    div[data-testid="stCheckbox"] label p {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
        white-space: nowrap !important;
    }

    /* Header */
    .hero-section { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 30px 20px; border-radius: 16px; text-align: center; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); border: 1px solid #334155; margin-bottom: 1.5rem; }
    .hero-title { font-size: clamp(1.4rem, 2.5vw, 2rem); font-weight: 800; color: #ffffff; margin-bottom: 0.5rem; line-height: 1.2; }
    .hero-subtitle { font-size: clamp(0.8rem, 1.5vw, 1rem); color: #94a3b8; }

    /* Kết quả tra cứu */
    .result-card { background: #ffffff; border-radius: 16px; padding: 25px; margin-top: 20px; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.2); }
    .result-success { border-left: 8px solid #10b981; }
    .result-error { border-left: 8px solid #ef4444; }
    .result-title { font-size: 1.6rem; font-weight: 800; margin-bottom: 15px; }
    .result-data { font-size: 1.2rem; color: #334155; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }
    .phone-alert { background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 20px; margin-top: 20px; }
    .phone-number { font-size: 2.2rem; font-weight: 800; color: #dc2626; display: block; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# THANH CHỌN NGÔN NGỮ GỌN GÀNG
col_space, col_lang = st.columns([7, 3])
with col_lang:
    render_language_selector()

db = get_db()
FERNET_KEY = st.secrets["fernet_key"]

st.markdown(f"""
<div class="hero-section">
    <div class="hero-title">🛡️ {t('portal_title')}</div>
    <div class="hero-subtitle">{t('portal_sub')}</div>
</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_categories():
    docs = list(db.collection("danh_muc").stream())
    return [(d.id, d.to_dict()) for d in docs]

@st.cache_data(ttl=60)
def load_docs_in(cat_id):
    docs = list(db.collection("tai_lieu").where("danh_muc_id", "==", cat_id).stream())
    return [(d.id, d.to_dict()) for d in docs]

# ==========================================
# HÀM HIỂN THỊ TÀI LIỆU
# ==========================================
def render_docs(cat_id):
    docs = load_docs_in(cat_id)
    if not docs:
        st.caption(t('no_docs'))
        return
        
    for doc_id, d in docs:
        with st.container(border=True):
            # HÀNG 1: TÊN FILE
            st.markdown(
                f"<div style='font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-bottom: 12px;'>"
                f"📄 {d.get('tieu_de','')} "
                f"<span style='color:#64748b; font-size:0.85rem; font-weight:500;'>[{d.get('file_type','?').upper()}]</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
            
            # HÀNG 2: 2 NÚT BẤM NẰM NGANG
            col_btn_dl, col_btn_prev = st.columns([1, 1], gap="small")
            
            with col_btn_dl:
                # Nút Tải Về (HTML)
                st.markdown(
                    f'<a href="{d.get("file_url","#")}" target="_blank" class="action-btn">📥 {t("btn_download")}</a>',
                    unsafe_allow_html=True
                )
                
            with col_btn_prev:
                # SỬA LỖI 2 CON MẮT: Bỏ emoji ở đây vì trong translations.py đã có
                show_preview = st.checkbox(t('view_preview'), key=f"chk_preview_{doc_id}")
            
            # NẾU CHỌN XEM TRƯỚC
            if show_preview:
                st.markdown("<hr style='margin: 15px 0 10px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
                file_type = d.get('file_type', '').lower()
                file_url = d.get('file_url', '')
                
                if file_type == 'pdf':
                    components.iframe(file_url, height=500, scrolling=True)
                elif file_type in ['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls']:
                    iframe_url = f"https://view.officeapps.live.com/op/embed.aspx?src={file_url}"
                    components.iframe(iframe_url, height=500, scrolling=True)
                else:
                    st.text(d.get("noi_dung_text", "")[:5000])

tab_a, tab_b = st.tabs([t('tab_prop'), t('tab_search')])

with tab_a:
    cats = load_categories()
    cat_dict = {cid: data for cid, data in cats}
    roots = [cid for cid, data in cat_dict.items() if not data.get("parent_id")]

    if not roots:
        st.info(t('no_prop'))
    
    for root_id in roots:
        root = cat_dict[root_id]
        with st.expander(f"📁 {root['ten']}", expanded=True):
            if root.get("mo_ta"):
                st.caption(root["mo_ta"])
            render_docs(root_id)
            
            children = [cid for cid, data in cat_dict.items() if data.get("parent_id") == root_id]
            for child_id in children:
                child = cat_dict[child_id]
                st.markdown(f"&nbsp;&nbsp;&nbsp;↳ **{child['ten']}**", unsafe_allow_html=True)
                render_docs(child_id)

with tab_b:
    st.markdown(f"<h3 style='color: #0f172a; text-align: center;'>{t('search_h')}</h3>", unsafe_allow_html=True)
    st.caption(t('search_desc'))

    with st.container(border=True):
        sub_tab1, sub_tab2 = st.tabs([t('cam_tab'), t('upload_tab')])
        photo = None
        with sub_tab1:
            photo_cam = st.camera_input(t('cam_btn'), key="cam_photo", label_visibility="collapsed")
            if photo_cam is not None: photo = photo_cam
        with sub_tab2:
            photo_upload = st.file_uploader(t('upload_btn'), type=["jpg", "jpeg", "png"], key="upload_photo", label_visibility="collapsed")
            if photo_upload is not None: photo = photo_upload

    if photo:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t('btn_search'), use_container_width=True):
            with st.spinner(t('processing')):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(photo.read())
                    tmp_path = tmp.name
                try:
                    # BƯỚC 1: Trích xuất đặc trưng (Có thể ném lỗi nếu ảnh mờ)
                    emb = extract_embedding(tmp_path)
                    
                    # BƯỚC 2: So khớp
                    best_doc, best_score = None, -1.0
                    count = 0
                    for doc in db.collection("doi_tuong").stream():
                        data = doc.to_dict()
                        enc = data.get("embedding_encrypted")
                        if not enc: continue
                        score = cosine_similarity(emb, decrypt_embedding(enc, FERNET_KEY))
                        if score > best_score: best_score, best_doc = score, data
                        count += 1

                    if best_doc and best_score >= MATCH_THRESHOLD:
                        # ... (Hiển thị kết quả thành công) ...
                        pass
                    else:
                        # Hiển thị điểm số cao nhất để dễ debug
                        score_text = f"Điểm tương đồng cao nhất: {best_score:.2f} (Cần >= {MATCH_THRESHOLD})" if best_score > 0 else ""
                        st.markdown(f"""
                        <div class="result-card result-error">
                            <div class="result-title" style="color: #dc2626;">❌ Không tìm thấy thông tin</div>
                            <p style="color: #64748b;">Hình ảnh không trùng khớp với dữ liệu hệ thống.</p>
                            <p style="font-size: 0.9rem; color: #94a3b8;">{score_text}</p>
                        </div>""", unsafe_allow_html=True)
                
                except ValueError as ve:
                    # BẮT LỖI KHÔNG TÌM THẤY MẶT
                    st.error(f"⚠️ {ve}")
                except Exception as e:
                    st.error(f"Lỗi xử lý ảnh: {e}")
