"""Cổng công dân – Giao diện Dark Mode, Premium UI."""
import os
import tempfile
import streamlit as st

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD

# Cấu hình trang
st.set_page_config(page_title="Cổng Công dân", page_icon="🛡️", layout="wide")

# ==========================================================
# CSS TÙY CHỈNH: GIAO DIỆN DARK MODE & HIỆU ỨNG GLOW
# ==========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. Cấu hình nền tối toàn trang */
    [data-testid="stAppViewContainer"] {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
        font-family: 'Inter', sans-serif;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. Giới hạn nội dung */
    .block-container {
        max-width: 900px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* 3. Hero Header (Dải màu tối) */
    .hero-section {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        padding: 40px 20px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5);
        border: 1px solid #334155;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
    }

    /* 4. Thẻ nội dung chính (White Card) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
        border: none;
        padding: 2rem;
        margin-bottom: 1rem;
    }

    /* 5. Tùy chỉnh Tabs (Nút bấm) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #1e293b;
        padding: 8px;
        border-radius: 12px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    }

    /* 6. Nút bấm Tra cứu (Glow Button) */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.8) !important;
    }

    /* 7. Tùy chỉnh khung Upload & Camera */
    [data-testid="stFileUploadDropzone"], [data-testid="stCameraInput"] {
        background-color: #f8fafc;
        border-radius: 12px;
        border: 2px dashed #cbd5e1;
        padding: 1.5rem;
    }
    
    /* 8. Custom Result Card (Hiển thị kết quả) */
    .result-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 30px;
        margin-top: 20px;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.2);
    }
    .result-success {
        border-left: 8px solid #10b981;
    }
    .result-error {
        border-left: 8px solid #ef4444;
    }
    .result-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 15px;
    }
    .result-data {
        font-size: 1.1rem;
        color: #334155;
        margin-bottom: 10px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 10px;
    }
    .phone-alert {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
    }
    .phone-number {
        font-size: 1.8rem;
        font-weight: 800;
        color: #dc2626;
        display: block;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

db = get_db()
FERNET_KEY = st.secrets["fernet_key"]

# ==========================================
# HEADER ĐẸP MẮT (Dùng HTML)
# ==========================================
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🛡️ CỔNG THÔNG TIN CÔNG DÂN</div>
    <div class="hero-subtitle">Hệ thống tra cứu thông tin và tuyên truyền phòng chống tội phạm</div>
</div>
""", unsafe_allow_html=True)

# Load data
@st.cache_data(ttl=60)
def load_categories():
    docs = list(db.collection("danh_muc").stream())
    return [(d.id, d.to_dict()) for d in docs]

@st.cache_data(ttl=60)
def load_docs_in(cat_id):
    docs = list(db.collection("tai_lieu").where("danh_muc_id", "==", cat_id).stream())
    return [d.to_dict() for d in docs]

def render_docs(cat_id):
    docs = load_docs_in(cat_id)
    if not docs:
        st.caption("*(Chưa có tài liệu)*")
        return
    for d in docs:
        with st.container(border=True):
            col1, col2 = st.columns([8, 2])
            col1.markdown(f"📄 **{d.get('tieu_de','')}** `[{d.get('file_type','?')}]`")
            col2.markdown(f"[⬇️ Tải xuống]({d.get('file_url','#')})")
            with st.expander("👁️ Xem trước nội dung"):
                st.text(d.get("noi_dung_text", "")[:5000])

# Tabs
tab_a, tab_b = st.tabs(["📚 Nội dung tuyên truyền", "🔎 Tra cứu thông tin"])

# ============================================================
# TAB A: TÀI LIỆU
# ============================================================
with tab_a:
    cats = load_categories()
    cat_dict = {cid: data for cid, data in cats}
    roots = [cid for cid, data in cat_dict.items() if not data.get("parent_id")]

    if not roots:
        st.info("Chưa có nội dung tuyên truyền.")
    
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

# ============================================================
# TAB B: TRA CỨU KHUÔN MẶT
# ============================================================
with tab_b:
    st.markdown("<h3 style='color: #0f172a; text-align: center;'>Tra cứu thông tin qua khuôn mặt</h3>", unsafe_allow_html=True)
    st.caption("Vui lòng cung cấp ảnh chân dung rõ mặt để hệ thống đối chiếu với cơ sở dữ liệu.")

    with st.container(border=True):
        sub_tab1, sub_tab2 = st.tabs(["📸 Chụp ảnh trực tiếp", "📂 Tải ảnh từ thiết bị"])
        
        photo = None
        
        with sub_tab1:
            photo_cam = st.camera_input("Nhấn vào đây để bật Camera", key="cam_photo", label_visibility="collapsed")
            if photo_cam is not None:
                photo = photo_cam
                
        with sub_tab2:
            photo_upload = st.file_uploader(
                "Chọn ảnh (jpg/png)", 
                type=["jpg", "jpeg", "png"], 
                key="upload_photo",
                label_visibility="collapsed"
            )
            if photo_upload is not None:
                photo = photo_upload

    if photo:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 BẮT ĐẦU TRA CỨU"):
            with st.spinner("Hệ thống đang phân tích khuôn mặt..."):
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
                        if not enc:
                            continue
                        stored = decrypt_embedding(enc, FERNET_KEY)
                        score = cosine_similarity(emb, stored)
                        if score > best_score:
                            best_score = score
                            best_doc = data

                    if best_doc and best_score >= MATCH_THRESHOLD:
                        # ===== KẾT QUẢ ĐẸP BẰNG HTML =====
                        st.markdown(f"""
                        <div class="result-card result-success">
                            <div class="result-title">✅ Tìm thấy thông tin trùng khớp</div>
                            <div style="color: #64748b; margin-bottom: 15px;">Độ tin cậy: <b>{best_score:.2%}</b></div>
                            
                            <div class="result-data"><b>Họ tên:</b> {best_doc.get('ho_ten','')}</div>
                            <div class="result-data"><b>Quốc tịch:</b> {best_doc.get('quoc_tich','')}</div>
                            <div class="result-data"><b>Số hộ chiếu:</b> <code>{best_doc.get('so_ho_chieu','')}</code></div>
                        </div>
                        """, unsafe_allow_html=True)

                        if best_doc.get("anh_url"):
                            st.image(best_doc["anh_url"], width=150, caption="Ảnh đối tượng")

                        # Hiển thị số điện thoại
                        contact = db.collection("cau_hinh").document("lien_he").get()
                        if contact.exists:
                            items = contact.to_dict().get("danh_sach", [])
                            if items:
                                for it in items:
                                    st.markdown(
                                        f"""<div class="phone-alert">
                                            <div style="color: #7f1d1d; font-weight: 600;">📞 Đường dây nóng: {it['ten']}</div>
                                            <span class="phone-number">{it['so_dien_thoai']}</span>
                                            <div style="color: #b91c1c; font-size: 0.9rem;">{it.get('mo_ta','')}</div>
                                        </div>""",
                                        unsafe_allow_html=True
                                    )
                    else:
                        # ===== KẾT QUẢ LỖI BẰNG HTML =====
                        st.markdown("""
                        <div class="result-card result-error">
                            <div class="result-title" style="color: #dc2626;">❌ Không tìm thấy thông tin</div>
                            <p style="color: #64748b;">Hình ảnh của bạn không trùng khớp với bất kỳ dữ liệu nào trên hệ thống.</p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Lỗi xử lý ảnh: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
