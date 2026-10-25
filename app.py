"""Cổng công dân – Giao diện Dark Mode, Chuẩn Font, Xem trước Office/PDF."""
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD
from utils.i18n import t, render_language_selector

st.set_page_config(page_title="Citizen Portal", page_icon="🛡️", layout="wide")

# ==========================================
# 1. ẨN SIDEBAR (Vì trang người dân không cần menu)
# ==========================================
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CSS GIAO DIỆN DARK MODE & LÀM ĐẸP THẺ TÀI LIỆU
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    [data-testid="stAppViewContainer"] {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Giới hạn chiều rộng nội dung */
    .block-container { max-width: 950px !important; padding-top: 2rem !important; padding-bottom: 2rem !important; }

    /* Header */
    .hero-section { background: linear-gradient(135deg, #1e293b, #0f172a); padding: 35px 20px; border-radius: 20px; text-align: center; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); border: 1px solid #334155; margin-bottom: 2rem; }
    .hero-title { font-size: clamp(1.4rem, 2.5vw, 2rem); font-weight: 800; color: #ffffff; margin-bottom: 0.5rem; line-height: 1.2; }
    .hero-subtitle { font-size: clamp(0.8rem, 1.5vw, 1rem); color: #94a3b8; }

    /* Thẻ chứa tài liệu */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: #ffffff; 
        border-radius: 12px; 
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.2); 
        border: none; 
        padding: 1rem 1.5rem; 
        margin-bottom: 0.8rem; 
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #1e293b; padding: 8px; border-radius: 12px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; color: #94a3b8; font-weight: 600; font-size: 1.1rem; padding: 10px 20px; border: none; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: white !important; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); }

    /* Nút bấm */
    .stButton > button, .stLinkButton > a { 
        width: 100%; 
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important; 
        padding: 0.6rem 1rem !important; 
        font-size: 1rem !important; 
        font-weight: 600 !important; 
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important; 
        transition: all 0.3s ease !important; 
        text-decoration: none !important;
        display: inline-block;
        text-align: center;
    }
    .stButton > button:hover, .stLinkButton > a:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.6) !important; 
        color: white !important;
    }

    /* Checkbox */
    .stCheckbox label p { font-weight: 600; color: #334155; }
    
    /* Kết quả */
    .result-card { background: #ffffff; border-radius: 16px; padding: 25px; margin-top: 20px; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.2); }
    .result-success { border-left: 8px solid #10b981; }
    .result-error { border-left: 8px solid #ef4444; }
    .result-title { font-size: 1.6rem; font-weight: 800; margin-bottom: 15px; }
    .result-data { font-size: 1.2rem; color: #334155; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }
    .phone-alert { background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 20px; margin-top: 20px; }
    .phone-number { font-size: 2.2rem; font-weight: 800; color: #dc2626; display: block; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# Nút chọn ngôn ngữ góc trên phải
_, col_lang = st.columns([4, 1])
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
    return [d.to_dict() for d in docs]

# ==========================================
# HÀM HIỂN THỊ TÀI LIỆU (THIẾT KẾ LẠI)
# ==========================================
def render_docs(cat_id):
    docs = load_docs_in(cat_id)
    if not docs:
        st.caption(t('no_docs'))
        return
    for d in docs:
        with st.container(border=True):
            # Chia 3 cột: Tên file | Nút tải | Checkbox xem trước
            col1, col2, col3 = st.columns([5, 2, 3], vertical_alignment="center")
            
            with col1:
                st.markdown(
                    f"📄 **{d.get('tieu_de','')}** <span style='color:#64748b; font-size:0.85rem;'>[{d.get('file_type','?').upper()}]</span>", 
                    unsafe_allow_html=True
                )
            
            with col2:
                # Dùng st.link_button thay vì markdown để nút trông đẹp và dễ nhấn hơn
                st.link_button(t('btn_download'), d.get('file_url','#'), use_container_width=True)
            
            with col3:
                # Dùng checkbox thay vì expander để tránh lỗi lồng nhau
                show_preview = st.checkbox(t('view_preview'), key=f"chk_{d.get('file_url')}")
            
            # Nếu người dùng tích vào ô xem trước, hiển thị iframe bên dưới thẻ
            if show_preview:
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
        # Thư mục lớn
        with st.expander(f"📁 {root['ten']}", expanded=True):
            if root.get("mo_ta"):
                st.caption(root["mo_ta"])
            render_docs(root_id)
            
            # Thư mục con
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
                    emb = extract_embedding(tmp_path)
                    best_doc = None
                    best_score = -1.0
                    
                    for doc in db.collection("doi_tuong").stream():
                        data = doc.to_dict()
                        enc = data.get("embedding_encrypted")
                        if not enc: continue
                        stored = decrypt_embedding(enc, FERNET_KEY)
                        score = cosine_similarity(emb, stored)
                        if score > best_score:
                            best_score = score
                            best_doc = data

                    if best_doc and best_score >= MATCH_THRESHOLD:
                        st.markdown(f"""
                        <div class="result-card result-success">
                            <div class="result-title">{t('res_success')}</div>
                            <div style="color: #64748b; margin-bottom: 15px;">{t('res_score')} <b>{best_score:.2%}</b></div>
                            <div class="result-data"><b>{t('res_name')}</b> {best_doc.get('ho_ten','')}</div>
                            <div class="result-data"><b>{t('res_nation')}</b> {best_doc.get('quoc_tich','')}</div>
                            <div class="result-data"><b>{t('res_pass')}</b> <code>{best_doc.get('so_ho_chieu','')}</code></div>
                        </div>
                        """, unsafe_allow_html=True)

                        if best_doc.get("anh_url"):
                            st.image(best_doc["anh_url"], width=150, caption=t('res_img'))

                        contact = db.collection("cau_hinh").document("lien_he").get()
                        if contact.exists:
                            items = contact.to_dict().get("danh_sach", [])
                            if items:
                                for it in items:
                                    st.markdown(
                                        f"""<div class="phone-alert">
                                            <div style="color: #7f1d1d; font-weight: 600; font-size: 1.1rem;">{t('hotline_name')} {it['ten']}</div>
                                            <span class="phone-number">{it['so_dien_thoai']}</span>
                                            <div style="color: #b91c1c; font-size: 1rem;">{it.get('mo_ta','')}</div>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.info(t('no_phone'))
                        else:
                            st.info(t('no_phone'))
                    else:
                        st.markdown(f"""
                        <div class="result-card result-error">
                            <div class="result-title" style="color: #dc2626;">{t('res_fail')}</div>
                            <p style="color: #64748b;">{t('res_fail_desc')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"{t('err_img')} {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
