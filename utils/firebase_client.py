"""Kết nối Firebase – chỉ dùng Firestore (Storage đã thay bằng Cloudinary).

Thứ tự tìm serviceAccount.json:
1. st.secrets (dùng cho Streamlit Cloud khi deploy citizen_web)
2. Thư mục dự án streamlit_app/ (tiện khi DEV)
3. %APPDATA%/TroLySo/ (PRODUCTION trên máy người dùng cuối)
"""
import os
import json
from pathlib import Path

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore


@st.cache_resource
def _init_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred = None

    # Ưu tiên 1: st.secrets (Streamlit Cloud)
    if "firebase" in st.secrets and "service_account" in st.secrets["firebase"]:
        sa_dict = dict(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(sa_dict)

    # Ưu tiên 2: thư mục dự án (tiện cho DEV)
    if cred is None:
        project_root = Path(__file__).resolve().parent.parent  # = streamlit_app/
        dev_sa = project_root / "serviceAccount.json"
        if dev_sa.exists():
            with open(dev_sa, "r", encoding="utf-8") as f:
                sa_json = json.load(f)
            cred = credentials.Certificate(sa_json)

    # Ưu tiên 3: %APPDATA%/TroLySo/ (PRODUCTION)
    if cred is None:
        appdata = os.environ.get("APPDATA") or str(Path.home() / ".config")
        prod_sa = Path(appdata) / "TroLySo" / "serviceAccount.json"
        if prod_sa.exists():
            with open(prod_sa, "r", encoding="utf-8") as f:
                sa_json = json.load(f)
            cred = credentials.Certificate(sa_json)

    # Không tìm thấy file ở đâu cả
    if cred is None:
        project_root = Path(__file__).resolve().parent.parent
        appdata = os.environ.get("APPDATA") or str(Path.home() / ".config")
        st.error(
            "Không tìm thấy file cấu hình Firebase. Vui lòng đặt "
            "`serviceAccount.json` tại MỘT trong các vị trí sau:\n\n"
            f"1. `{project_root / 'serviceAccount.json'}` (khuyến nghị khi dev)\n"
            f"2. `{Path(appdata) / 'TroLySo' / 'serviceAccount.json'}` (production)\n"
        )
        st.stop()

    return firebase_admin.initialize_app(cred)


def get_db():
    """Trả về Firestore client."""
    return firestore.client(app=_init_firebase())


def login_admin() -> bool:
    """Đăng nhập bằng mật khẩu quản trị (lưu trong st.secrets)."""
    if st.session_state.get("admin_ok"):
        return True

    with st.form("login_admin_form"):
        st.markdown("### 🔐 Đăng nhập cán bộ")
        pwd = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

    if submitted:
        expected = st.secrets.get("admin_password", "admin")
        if pwd == expected:
            st.session_state.admin_ok = True
            st.rerun()
        else:
            st.error("Sai mật khẩu. Vui lòng thử lại.")
    return False


def require_admin():
    """Guard: dừng trang nếu chưa đăng nhập."""
    if not st.session_state.get("admin_ok"):
        st.warning("Vui lòng đăng nhập tại trang chủ.")
        st.stop()