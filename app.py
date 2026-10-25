"""Cổng công dân – deploy độc lập trên Streamlit Cloud."""
import os
import tempfile

import streamlit as st

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD

st.set_page_config(page_title="Cổng Công dân", page_icon="🌐", layout="wide")

db = get_db()
FERNET_KEY = st.secrets["fernet_key"]

st.title("🌐 Cổng thông tin Công dân")
st.caption("Xem nội dung tuyên truyền và tra cứu thông tin người nước ngoài.")


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
        st.caption("_(Chưa có tài liệu)_")
        return
    for d in docs:
        with st.container(border=True):
            st.markdown(f"**📄 {d.get('tieu_de','')}** `[{d.get('file_type','?')}]`")
            st.markdown(f"[⬇️ Tải file gốc]({d.get('file_url','#')})")
            with st.expander("👁️ Xem trước nội dung"):
                st.text(d.get("noi_dung_text", "")[:5000])


tab_a, tab_b = st.tabs(["📚 Nội dung tuyên truyền", "🔎 Tra cứu khuôn mặt"])

with tab_a:
    st.subheader("Chọn đề mục để xem nội dung")
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
            children = [
                cid for cid, data in cat_dict.items()
                if data.get("parent_id") == root_id
            ]
            for child_id in children:
                child = cat_dict[child_id]
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;**↳ {child['ten']}**",
                    unsafe_allow_html=True,
                )
                if child.get("mo_ta"):
                    st.caption(child["mo_ta"])
                render_docs(child_id)

with tab_b:
    st.subheader("Tải ảnh khuôn mặt để tra cứu")
    st.caption("Hệ thống sẽ so khớp với cơ sở dữ liệu đối tượng do cán bộ nhập.")

    photo = st.file_uploader(
        "Chọn ảnh chân dung (jpg/png)",
        type=["jpg", "jpeg", "png"],
        key="citizen_photo",
    )

    if photo and st.button("🔍 Tra cứu", type="primary"):
        with st.spinner("Đang phân tích khuôn mặt..."):
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
                    st.success(f"✅ Trùng khớp (độ tin cậy {best_score:.2%})")
                    st.markdown(
                        f"- **Họ tên:** {best_doc.get('ho_ten','')}\n"
                        f"- **Quốc tịch:** {best_doc.get('quoc_tich','')}\n"
                        f"- **Số hộ chiếu:** `{best_doc.get('so_ho_chieu','')}`"
                    )
                    if best_doc.get("anh_url"):
                        st.image(best_doc["anh_url"], width=180)

                    st.divider()
                    st.warning("📞 **Đường dây nóng phản ánh / hỗ trợ**")
                    contact = db.collection("cau_hinh").document("lien_he").get()
                    if contact.exists:
                        items = contact.to_dict().get("danh_sach", [])
                        if items:
                            for it in items:
                                st.markdown(
                                    f"**{it['ten']}** — `{it['so_dien_thoai']}`  \n"
                                    f"_{it.get('mo_ta','')}_"
                                )
                        else:
                            st.info("Chưa có số điện thoại được cấu hình.")
                    else:
                        st.info("Chưa có số điện thoại được cấu hình.")
                else:
                    st.error("❌ Không tìm thấy thông tin trùng khớp trong hệ thống.")
            except Exception as e:
                st.error(f"Lỗi xử lý ảnh: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)