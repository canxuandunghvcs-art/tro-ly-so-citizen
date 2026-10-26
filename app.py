"""Cổng công dân – giao diện hiện đại, hỗ trợ tài liệu, tra cứu và cảnh báo đường dây nóng."""

import html
import os
import tempfile
import time
from urllib.parse import quote, urlparse

import requests
import streamlit as st
import streamlit.components.v1 as components
from cryptography.fernet import Fernet

from utils.firebase_client import get_db
from utils.face_utils import extract_embedding, decrypt_embedding, cosine_similarity
from utils.constants import MATCH_THRESHOLD
from utils.i18n import t, render_language_selector


st.set_page_config(
    page_title="Citizen Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# GIAO DIỆN
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --navy: #183653;
        --navy-deep: #10273f;
        --blue: #2864b4;
        --blue-soft: #eaf2ff;
        --ink: #1e293b;
        --muted: #64748b;
        --line: #e2e8f0;
        --surface: #ffffff;
        --page: #f4f7fb;
        --green: #12805c;
        --red: #b42318;
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 8% 0%, rgba(219,234,254,.65), transparent 35%),
            linear-gradient(180deg, #f7f9fc 0%, var(--page) 100%);
        color: var(--ink);
    }

    .block-container {
        max-width: 1120px !important;
        padding: 1.25rem 1.5rem 3.5rem !important;
    }

    /* Header */
    .hero-section {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        gap: 22px;
        padding: 30px 34px;
        margin: 8px 0 24px;
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 22px;
        background: linear-gradient(125deg, #10273f 0%, #183b60 58%, #24578a 100%);
        box-shadow: 0 16px 36px rgba(16,39,63,.15);
    }
    .hero-section::after {
        content: "";
        position: absolute;
        width: 280px;
        height: 280px;
        right: -95px;
        top: -145px;
        border: 38px solid rgba(255,255,255,.055);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-icon {
        display: flex;
        flex: 0 0 66px;
        width: 66px;
        height: 66px;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255,255,255,.22);
        border-radius: 19px;
        background: rgba(255,255,255,.12);
        font-size: 2rem;
    }
    .hero-copy { position: relative; z-index: 1; min-width: 0; }
    .hero-title {
        margin: 0 0 7px;
        color: #fff !important;
        font-size: clamp(1.45rem, 2.4vw, 2.1rem);
        font-weight: 800;
        line-height: 1.25;
        letter-spacing: -.035em;
    }
    .hero-subtitle {
        color: #d7e5f5 !important;
        font-size: .98rem;
        line-height: 1.65;
        max-width: 760px;
    }

    /* Widget language selector */
    [data-testid="stSelectbox"] label,
    [data-testid="stRadio"] label,
    [data-testid="stFileUploader"] label,
    [data-testid="stCameraInput"] label {
        color: var(--ink) !important;
        font-weight: 600;
    }
    [data-testid="stSelectbox"] > div > div {
        border-radius: 11px;
        border-color: #d7e0ec;
        background: rgba(255,255,255,.92);
    }

    /* Content sections and cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
        background: var(--surface) !important;
        box-shadow: 0 4px 18px rgba(15, 35, 60, .045);
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 1rem 1.1rem;
    }
    [data-testid="stExpander"] {
        overflow: hidden;
        margin: 0 0 14px;
        border: 1px solid var(--line) !important;
        border-radius: 15px !important;
        background: rgba(255,255,255,.95) !important;
        box-shadow: 0 3px 14px rgba(15,35,60,.035);
    }
    [data-testid="stExpander"] details summary {
        padding: .85rem 1.05rem;
        color: var(--navy) !important;
        font-weight: 700;
    }
    [data-testid="stExpander"] details summary:hover { color: var(--blue) !important; }
    [data-testid="stExpander"] details > div > div { padding: .4rem 1rem 1rem; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        gap: 7px;
        padding: 7px;
        border: 1px solid #e1e8f1;
        border-radius: 15px;
        background: #fff;
        box-shadow: 0 3px 12px rgba(15,35,60,.035);
    }
    .stTabs [data-baseweb="tab"] {
        min-height: 44px;
        padding: 9px 20px;
        border-radius: 10px;
        color: #64748b;
        font-size: .98rem;
        font-weight: 700;
        border: 0;
    }
    .stTabs [data-baseweb="tab"] p { font-size: .98rem; font-weight: 700; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #fff !important;
        background: var(--navy) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }
    .stTabs [data-baseweb="tab-border"] { background: transparent !important; }

    /* Buttons */
    .stButton > button {
        min-height: 43px;
        border: 1px solid #d6e0ec;
        border-radius: 11px;
        color: var(--navy);
        background: #fff;
        font-weight: 700;
        transition: all .18s ease;
    }
    .stButton > button:hover {
        color: var(--blue);
        border-color: #9dbce7;
        background: #f3f7ff;
        box-shadow: 0 5px 14px rgba(40,100,180,.10);
    }
    .stButton > button[kind="primary"] {
        color: #fff !important;
        border-color: var(--blue) !important;
        background: linear-gradient(135deg, #2d6cc0, #1d5298) !important;
        box-shadow: 0 6px 16px rgba(40,100,180,.18);
    }
    .stButton > button[kind="primary"]:hover { filter: brightness(1.05); }

    /* Document cards and action links */
    .document-title-row {
        display: flex;
        align-items: flex-start;
        gap: 11px;
        margin: 0 0 14px;
    }
    .document-icon {
        display: inline-flex;
        flex: 0 0 40px;
        width: 40px;
        height: 40px;
        justify-content: center;
        align-items: center;
        border-radius: 12px;
        background: var(--blue-soft);
        font-size: 1.2rem;
    }
    .document-name {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 750;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }
    .file-badge {
        display: inline-block;
        margin-top: 5px;
        padding: 3px 8px;
        border: 1px solid #dbe5f2;
        border-radius: 6px;
        color: #51657c;
        background: #f7f9fc;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .04em;
    }
    .action-btn {
        display: flex;
        min-height: 42px;
        align-items: center;
        justify-content: center;
        gap: 7px;
        padding: 9px 12px;
        border: 1px solid #cbdcf4;
        border-radius: 10px;
        color: #24579b !important;
        background: #f1f6ff;
        font-size: .84rem;
        font-weight: 750;
        line-height: 1.35;
        text-align: center;
        text-decoration: none !important;
        box-sizing: border-box;
        transition: all .18s ease;
    }
    .action-btn:hover {
        border-color: #8eb1e5;
        color: #173f76 !important;
        background: #e5efff;
        transform: translateY(-1px);
    }
    .action-btn.primary {
        border-color: #245ba5;
        color: #fff !important;
        background: linear-gradient(135deg, #2e6dc0, #1d4e8c);
    }
    .action-btn.primary:hover { color: #fff !important; background: #1d4e8c; }

    div[data-testid="stCheckbox"] { margin: 0 !important; padding: 8px 0 !important; }
    div[data-testid="stCheckbox"] label { gap: 8px; }
    div[data-testid="stCheckbox"] label p {
        color: #465970 !important;
        font-size: .84rem !important;
        font-weight: 650 !important;
        white-space: normal !important;
    }

    /* Search section */
    .section-heading {
        margin: 4px 0 7px;
        color: var(--navy);
        font-size: 1.35rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: -.02em;
    }
    .section-description {
        margin: 0 auto 18px;
        max-width: 740px;
        color: var(--muted);
        font-size: .94rem;
        line-height: 1.7;
        text-align: center;
    }
    [data-testid="stCameraInput"], [data-testid="stFileUploader"] {
        border-radius: 12px;
    }
    [data-testid="stFileUploader"] section {
        border: 1px dashed #bdcde1;
        border-radius: 12px;
        background: #f8fbff;
    }
    [data-testid="stCameraInput"] button {
        border-radius: 10px;
    }

    /* Results */
    .result-card {
        margin: 18px 0 14px;
        padding: 24px 26px;
        border: 1px solid var(--line);
        border-radius: 17px;
        background: #fff;
        box-shadow: 0 8px 26px rgba(15,35,60,.07);
    }
    .result-success { border-top: 4px solid #16936a; }
    .result-error { border-top: 4px solid #d64545; }
    .result-title {
        margin: 0 0 10px;
        color: var(--navy);
        font-size: 1.3rem;
        font-weight: 800;
    }
    .result-meta { margin-bottom: 14px; color: #64748b; font-size: .86rem; line-height: 1.7; }
    .result-data {
        display: grid;
        grid-template-columns: minmax(130px, .7fr) minmax(0, 1.3fr);
        gap: 12px;
        padding: 11px 0;
        border-top: 1px solid #edf1f6;
        color: #334155;
        font-size: .96rem;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }
    .result-label { color: #64748b; font-weight: 600; }
    .result-value { color: #172b43; font-weight: 700; }

    /* Hotline */
    .phone-alert {
        margin: 14px 0;
        padding: 22px;
        border: 1px solid #f2c8c8;
        border-radius: 15px;
        background: linear-gradient(135deg, #fffafa, #fff1f1);
        text-align: center;
    }
    .phone-alert-title { color: #8f2222; font-size: 1rem; font-weight: 800; }
    .phone-number {
        display: block;
        margin: 8px 0 5px;
        color: #c62828;
        font-size: clamp(1.8rem, 4vw, 2.4rem);
        font-weight: 850;
        letter-spacing: .04em;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }
    .phone-description { color: #9f3a3a; font-size: .9rem; line-height: 1.6; }

    [data-testid="stAlert"] { border-radius: 12px; }
    [data-testid="stStatusWidget"] { border-radius: 12px; }
    hr { border-color: #e7edf4 !important; }

    @media (max-width: 700px) {
        .block-container { padding: .8rem .8rem 2rem !important; }
        .hero-section { gap: 14px; padding: 23px 18px; border-radius: 17px; }
        .hero-icon { flex-basis: 48px; width: 48px; height: 48px; border-radius: 14px; font-size: 1.55rem; }
        .hero-subtitle { font-size: .86rem; }
        .stTabs [data-baseweb="tab"] { padding: 8px 10px; }
        .stTabs [data-baseweb="tab"] p { font-size: .85rem; }
        .result-card { padding: 18px 16px; }
        .result-data { grid-template-columns: 1fr; gap: 3px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def escaped(value) -> str:
    """Escape values before inserting database or translation text into HTML."""
    return html.escape(str(value if value is not None else ""), quote=True)


def http_url(value) -> str:
    """Only allow valid HTTP(S) links in document links and embedded previews."""
    candidate = str(value or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return candidate


# Thanh chọn ngôn ngữ
left_space, language_column = st.columns([7, 3], vertical_alignment="center")
with language_column:
    render_language_selector()

# Kết nối dữ liệu và khóa giải mã
# Giữ nguyên cơ chế kết nối, dữ liệu và so khớp đang dùng trong dự án.
db = get_db()
FERNET_KEY = st.secrets["fernet_key"]
cipher = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

st.markdown(
    f"""
    <section class="hero-section">
        <div class="hero-icon" aria-hidden="true">🛡️</div>
        <div class="hero-copy">
            <div class="hero-title">{escaped(t('portal_title'))}</div>
            <div class="hero-subtitle">{escaped(t('portal_sub'))}</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_categories():
    docs = list(db.collection("danh_muc").stream())
    return [(doc.id, doc.to_dict()) for doc in docs]


@st.cache_data(ttl=60)
def load_docs_in(cat_id):
    docs = list(db.collection("tai_lieu").where("danh_muc_id", "==", cat_id).stream())
    return [(doc.id, doc.to_dict()) for doc in docs]


def render_docs(cat_id):
    """Render a category's documents as consistent cards with safe links."""
    docs = load_docs_in(cat_id)
    if not docs:
        st.caption(t("no_docs"))
        return

    for doc_id, document in docs:
        title = escaped(document.get("tieu_de", "Tài liệu chưa có tiêu đề"))
        file_type = str(document.get("file_type", "")).strip().lower()
        file_label = escaped(file_type.upper() or "FILE")
        file_url = http_url(document.get("file_url"))

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="document-title-row">
                    <div class="document-icon" aria-hidden="true">📄</div>
                    <div style="min-width:0;flex:1">
                        <div class="document-name">{title}</div>
                        <span class="file-badge">{file_label}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_download, col_open, col_preview = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            with col_download:
                if file_url:
                    st.markdown(
                        f'<a href="{escaped(file_url)}" target="_blank" rel="noopener noreferrer" '
                        f'class="action-btn">📥 {escaped(t("btn_download"))}</a>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.button("📥 " + str(t("btn_download")), key=f"disabled_download_{doc_id}", disabled=True, use_container_width=True)

            with col_open:
                if file_url:
                    st.markdown(
                        f'<a href="{escaped(file_url)}" target="_blank" rel="noopener noreferrer" '
                        f'class="action-btn primary">↗ Xem toàn màn hình</a>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.button("↗ Xem toàn màn hình", key=f"disabled_open_{doc_id}", disabled=True, use_container_width=True)

            with col_preview:
                show_preview = st.checkbox(t("view_preview"), key=f"chk_preview_{doc_id}")

            if not file_url:
                st.caption("Tài liệu chưa có đường dẫn hợp lệ để mở hoặc tải xuống.")

            if show_preview:
                st.divider()
                if not file_url:
                    st.warning("Không thể xem trước vì tài liệu chưa có đường dẫn hợp lệ.")
                elif file_type == "pdf":
                    components.iframe(file_url, height=720, scrolling=True)
                elif file_type in {"docx", "doc", "pptx", "ppt", "xlsx", "xls"}:
                    # Office Web Viewer yêu cầu URL của tệp có thể truy cập từ Internet.
                    iframe_url = "https://view.officeapps.live.com/op/embed.aspx?src=" + quote(file_url, safe="")
                    components.iframe(iframe_url, height=720, scrolling=True)
                else:
                    text_content = str(document.get("noi_dung_text", "") or "")
                    if text_content.strip():
                        st.text(text_content[:10000])
                    else:
                        st.info("Chưa có nội dung xem trước cho định dạng tài liệu này.")


# -----------------------------------------------------------------------------
# NỘI DUNG CHÍNH
# -----------------------------------------------------------------------------
tab_documents, tab_lookup = st.tabs([t("tab_prop"), t("tab_search")])

# TAB 1: NỘI DUNG TUYÊN TRUYỀN
with tab_documents:
    categories = load_categories()
    category_map = {category_id: data for category_id, data in categories}
    root_categories = [
        (category_id, data)
        for category_id, data in categories
        if not data.get("parent_id")
    ]

    if not root_categories:
        st.info(t("no_prop"))
    else:
        for root_id, root in root_categories:
            root_name = str(root.get("ten", "Danh mục chưa có tên"))
            with st.expander(f"📁  {root_name}", expanded=True):
                description = str(root.get("mo_ta", "") or "").strip()
                if description:
                    st.caption(description)

                render_docs(root_id)

                children = [
                    (child_id, child)
                    for child_id, child in categories
                    if child.get("parent_id") == root_id
                ]
                for child_id, child in children:
                    st.markdown(
                        f'<div style="margin:18px 0 10px;color:#285581;font-weight:750;">'
                        f'↳ {escaped(child.get("ten", "Danh mục con"))}</div>',
                        unsafe_allow_html=True,
                    )
                    if child.get("mo_ta"):
                        st.caption(str(child.get("mo_ta")))
                    render_docs(child_id)

# TAB 2: TRA CỨU THÔNG TIN
with tab_lookup:
    st.markdown(
        f'<div class="section-heading">{escaped(t("search_h"))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="section-description">{escaped(t("search_desc"))}</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        sub_tab_camera, sub_tab_upload = st.tabs([t("cam_tab"), t("upload_tab")])
        photo = None

        with sub_tab_camera:
            camera_photo = st.camera_input(
                t("cam_btn"),
                key="cam_photo",
                label_visibility="collapsed",
            )
            if camera_photo is not None:
                photo = camera_photo

        with sub_tab_upload:
            uploaded_photo = st.file_uploader(
                t("upload_btn"),
                type=["jpg", "jpeg", "png"],
                key="upload_photo",
                label_visibility="collapsed",
            )
            if uploaded_photo is not None:
                photo = uploaded_photo

    if photo is not None:
        st.caption("Kiểm tra ảnh đã chọn trước khi bắt đầu tra cứu.")
        st.image(photo, caption="Ảnh được chọn", width=220)
        run_lookup = st.button(t("btn_search"), type="primary", use_container_width=True)

        if run_lookup:
            tmp_path = None
            with st.status("Hệ thống đang xử lý…", expanded=True) as status:
                try:
                    status.write("📸 Đang chuẩn bị ảnh trong bộ nhớ tạm…")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(photo.getvalue())
                        tmp_path = tmp_file.name

                    status.write("🧠 Đang phân tích ảnh…")
                    ai_started = time.time()
                    embedding = extract_embedding(tmp_path)
                    ai_elapsed = time.time() - ai_started

                    status.write("🔎 Đang đối chiếu với dữ liệu đã lưu…")
                    db_started = time.time()
                    best_document, best_score = None, -1.0
                    compared_count = 0

                    for record in db.collection("doi_tuong").stream():
                        record_data = record.to_dict() or {}
                        encrypted_embedding = record_data.get("embedding_encrypted")
                        if not encrypted_embedding:
                            continue
                        similarity = cosine_similarity(
                            embedding,
                            decrypt_embedding(encrypted_embedding, FERNET_KEY),
                        )
                        if similarity > best_score:
                            best_score, best_document = similarity, record_data
                        compared_count += 1

                    db_elapsed = time.time() - db_started
                    status.update(
                        label="✅ Đã hoàn tất xử lý",
                        state="complete",
                        expanded=False,
                    )

                    if best_document and best_score >= MATCH_THRESHOLD:
                        full_name = escaped(best_document.get("ho_ten", ""))
                        nationality = escaped(best_document.get("quoc_tich", ""))
                        passport_number = escaped(best_document.get("so_ho_chieu", ""))
                        st.markdown(
                            f"""
                            <section class="result-card result-success">
                                <div class="result-title">✅ {escaped(t('res_success'))}</div>
                                <div class="result-meta">
                                    {escaped(t('res_score'))} <strong>{best_score:.2%}</strong><br>
                                    Thời gian xử lý: {ai_elapsed:.1f}s · Đối chiếu {compared_count} hồ sơ: {db_elapsed:.1f}s
                                </div>
                                <div class="result-data"><span class="result-label">{escaped(t('res_name'))}</span><span class="result-value">{full_name}</span></div>
                                <div class="result-data"><span class="result-label">{escaped(t('res_nation'))}</span><span class="result-value">{nationality}</span></div>
                                <div class="result-data"><span class="result-label">{escaped(t('res_pass'))}</span><span class="result-value"><code>{passport_number}</code></span></div>
                            </section>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Giải mã và hiển thị ảnh theo cơ chế hiện có.
                        image_url = http_url(best_document.get("anh_url"))
                        if image_url:
                            try:
                                image_response = requests.get(image_url, timeout=(5, 20))
                                image_response.raise_for_status()
                                decrypted_image = cipher.decrypt(image_response.content)
                                st.image(decrypted_image, width=180, caption=t("res_img"))
                            except Exception:
                                st.warning("Không thể tải hoặc giải mã ảnh hồ sơ.")

                        contact_document = db.collection("cau_hinh").document("lien_he").get()
                        contact_data = contact_document.to_dict() if contact_document.exists else {}
                        contact_list = (contact_data or {}).get("danh_sach", []) or []

                        if contact_list:
                            st.markdown("#### 🚨 Thông tin đường dây nóng")
                            for item in contact_list:
                                item = item or {}
                                st.markdown(
                                    f"""
                                    <div class="phone-alert">
                                        <div class="phone-alert-title">🚨 {escaped(t('hotline_name'))} {escaped(item.get('ten', ''))}</div>
                                        <span class="phone-number">{escaped(item.get('so_dien_thoai', ''))}</span>
                                        <div class="phone-description">{escaped(item.get('mo_ta', ''))}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("Hệ thống chưa cấu hình số điện thoại đường dây nóng.")

                    else:
                        score_text = (
                            f"Điểm tương đồng cao nhất: {best_score:.2f} (ngưỡng cấu hình: {MATCH_THRESHOLD})"
                            if best_score > 0
                            else "Không có hồ sơ đủ dữ liệu để đối chiếu."
                        )
                        st.markdown(
                            f"""
                            <section class="result-card result-error">
                                <div class="result-title" style="color:#b42318;">❌ {escaped(t('res_fail'))}</div>
                                <p style="color:#64748b;line-height:1.7;">{escaped(t('res_fail_desc'))}</p>
                                <p style="font-size:.88rem;color:#64748b;margin-bottom:0;">{escaped(score_text)}</p>
                            </section>
                            """,
                            unsafe_allow_html=True,
                        )

                except ValueError as error:
                    status.update(
                        label="❌ Không thể phân tích ảnh",
                        state="error",
                        expanded=True,
                    )
                    st.error(str(error))
                except Exception:
                    status.update(
                        label="❌ Đã xảy ra lỗi khi xử lý",
                        state="error",
                        expanded=True,
                    )
                    st.error("Không thể hoàn tất tra cứu. Vui lòng kiểm tra kết nối dữ liệu và cấu hình hệ thống.")
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except OSError:
                            pass
