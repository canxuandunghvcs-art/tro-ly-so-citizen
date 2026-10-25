"""Cổng công dân – Giao diện hiện đại, thân thiện."""
import os
import tempfile
import streamlit as st

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD
from utils.ui_utils import apply_custom_css

st.set_page_config(page_title="Cổng Công dân", page_icon="🌐", layout="centered")
apply_custom_css()

db = get_db()
FERNET_KEY = st.secrets["fernet_key"]

# Header
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #1e3a8a; font-weight: 800; margin-bottom: 5px;">🌐 CỔNG THÔNG TIN CÔNG DÂN</h1>
    <p style="color: #64748b; font-size: 1.1rem;">Tra cứu thông tin và xem nội dung tuyên truyền</p>
</div>
""", unsafe_allow_html=True)

# Load data (cache)
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
# TAB B: TRA CỨU KHUÔN MẶT (CÓ 2 LỰA CHỌN: CHỤP HOẶC TẢI LÊN)
# ============================================================
with tab_b:
    st.markdown("<h3 style='color: #0f172a; text-align: center;'>Tra cứu thông tin qua khuôn mặt</h3>", unsafe_allow_html=True)
    st.caption("Vui lòng cung cấp ảnh chân dung rõ mặt để hệ thống đối chiếu với cơ sở dữ liệu.")

    # Tạo 2 tab nhỏ để người dùng chọn cách tải ảnh
    sub_tab1, sub_tab2 = st.tabs(["📸 Chụp ảnh trực tiếp", "📂 Tải ảnh từ thiết bị"])
    
    photo = None
    
    # Cách 1: Chụp ảnh (hiển thị trên điện thoại hoặc webcam máy tính)
    with sub_tab1:
        photo_cam = st.camera_input("Nhấn vào đây để bật Camera", key="cam_photo")
        if photo_cam is not None:
            photo = photo_cam
            
    # Cách 2: Tải ảnh lên từ thư viện
    with sub_tab2:
        photo_upload = st.file_uploader(
            "Chọn ảnh (jpg/png)", 
            type=["jpg", "jpeg", "png"], 
            key="upload_photo"
        )
        if photo_upload is not None:
            photo = photo_upload

    # Nếu đã có ảnh (từ 1 trong 2 tab) thì hiển thị nút Tra cứu
    if photo:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 BẮT ĐẦU TRA CỨU", type="primary", use_container_width=True):
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
                        # HIỂN THỊ KẾT QUẢ ĐẸP MẮT
                        st.markdown(f"""
                        <div class="result-card">
                            <h3>✅ Tìm thấy thông tin trùng khớp</h3>
                            <p><b>Độ tin cậy:</b> <span style="color:#10b981; font-weight:bold;">{best_score:.2%}</span></p>
                            <hr style="margin: 15px 0; border: none; border-top: 1px solid #e2e8f0;">
                            <p><b>Họ tên:</b> {best_doc.get('ho_ten','')}</p>
                            <p><b>Quốc tịch:</b> {best_doc.get('quoc_tich','')}</p>
                            <p><b>Số hộ chiếu:</b> <code>{best_doc.get('so_ho_chieu','')}</code></p>
                        </div>
                        """, unsafe_allow_html=True)

                        if best_doc.get("anh_url"):
                            st.image(best_doc["anh_url"], width=150, caption="Ảnh đối tượng")

                        st.divider()
                        st.error("📞 **ĐƯỜNG DÂY NÓNG PHẢN ÁNH / HỖ TRỢ**")
                        contact = db.collection("cau_hinh").document("lien_he").get()
                        if contact.exists:
                            items = contact.to_dict().get("danh_sach", [])
                            if items:
                                for it in items:
                                    st.markdown(
                                        f"<div style='background:#fee2e2; padding:10px; border-radius:8px; margin-bottom:5px;'>"
                                        f"<b>{it['ten']}</b> — <span style='font-size:1.2rem; color:#dc2626; font-weight:bold;'>{it['so_dien_thoai']}</span><br>"
                                        f"<i>{it.get('mo_ta','')}</i></div>",
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.info("Chưa có số điện thoại được cấu hình.")
                        else:
                            st.info("Chưa có số điện thoại được cấu hình.")
                    else:
                        st.markdown("""
                        <div class="result-card error">
                            <h3>❌ Không tìm thấy thông tin</h3>
                            <p>Hình ảnh của bạn không trùng khớp với bất kỳ dữ liệu nào trên hệ thống.</p>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Lỗi xử lý ảnh: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
