import os
import json
import time
import streamlit as st
import extra_streamlit_components as stx

# Import các hàm xử lý dữ liệu và phân quyền từ 3 file module
from utils import (
    init_db, save_to_db, load_user_history, load_public_gallery, 
    toggle_share_status, validate_python_code, login_user, register_user
)
from export_tools import create_word_document, create_themis_zip
from ai_core import generate_exam, generate_test_script

init_db()

# ==========================================
# CẤU HÌNH TRANG & CSS XÓA KHOẢNG TRẮNG
# ==========================================
st.set_page_config(page_title="Hệ Thống Đề Thi - SmartEdu", layout="wide", page_icon="📝")

st.markdown("""
    <style>
    .block-container { padding-top: 3.5rem; padding-bottom: 2rem; }
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display: none;}
    header {background-color: transparent !important;}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 45px; border-radius: 6px 6px 0px 0px; padding: 10px 16px; }
    .stTabs [aria-selected="true"] { background-color: rgba(255, 75, 75, 0.1); border-bottom: 2px solid #FF4B4B; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# XỬ LÝ LƯU ĐĂNG NHẬP QUA COOKIE & TIMEOUT (15 PHÚT = 900 GIÂY)
# ==========================================
TIMEOUT_SECONDS = 900 

if "exam_cart" not in st.session_state:
    st.session_state.exam_cart = []
if "current_problem" not in st.session_state:
    st.session_state.current_problem = None

# Khởi tạo bộ quản lý Cookie với KEY định danh duy nhất
def get_cookie_manager():
    return stx.CookieManager(key="smartedu_session_cookie_key")

cookie_manager = get_cookie_manager()

# Đọc gói dữ liệu session duy nhất từ trình duyệt
session_cookie = cookie_manager.get("smartedu_session")

# Kiểm tra logic duy trì đăng nhập 15 phút
if session_cookie and isinstance(session_cookie, dict):
    cookie_user = session_cookie.get("user")
    cookie_time = session_cookie.get("timestamp")
    
    if cookie_user and cookie_time:
        elapsed_time = time.time() - float(cookie_time)
        if elapsed_time < TIMEOUT_SECONDS:
            st.session_state.logged_in = True
            st.session_state.user_info = cookie_user
        else:
            # Hết hạn 15 phút -> Xóa sạch session
            st.session_state.logged_in = False
            st.session_state.user_info = None
            cookie_manager.delete("smartedu_session")
            st.warning("⏰ Đã hết phiên đăng nhập (15 phút không hoạt động). Vui lòng đăng nhập lại để bảo mật tài nguyên!")
else:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

# ==========================================
# MÀN HÌNH CHẶN 1: CHƯA ĐĂNG NHẬP
# ==========================================
if not st.session_state.logged_in:
    st.title("🧠 Hệ thống Ngân hàng đề thông minh SmartEdu AI")
    st.caption("Nền tảng hỗ trợ giáo viên Tin học biên soạn, quản lý và chia sẻ tài nguyên giáo dục đóng.")
    st.divider()
    
    _, login_col, _ = st.columns([1, 1.5, 1])
    
    with login_col:
        tab_login, tab_register = st.tabs(["🔐 Đăng Nhập", "📝 Đăng Ký Giáo Viên"])
        
        with tab_login:
            with st.form("form_dang_nhap"):
                email = st.text_input("📬 Email trường / cá nhân:")
                password = st.text_input("🔑 Mật khẩu:", type="password")
                btn_login = st.form_submit_button("Đăng Nhập Ngay", use_container_width=True)
                
                if btn_login:
                    if email and password:
                        user, msg = login_user(email, password)
                        if user:
                            # ĐÓNG GÓI TẤT CẢ VÀO 1 OBJECT VÀ CHỈ GỌI LỆNH COKIE MANAGER SET ĐÚNG 1 LẦN DUY NHẤT
                            session_data = {
                                "user": user,
                                "timestamp": time.time()
                            }
                            cookie_manager.set("smartedu_session", session_data, max_age=TIMEOUT_SECONDS)
                            
                            st.session_state.logged_in = True
                            st.session_state.user_info = user
                            st.success(f"🎉 {msg} (Hệ thống đang chuyển hướng...)")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("⚠️ Vui lòng điền đầy đủ Email và Mật khẩu!")
                        
        with tab_register:
            with st.form("form_dang_ky"):
                reg_name = st.text_input("👤 Họ và tên Thầy/Cô:")
                reg_email = st.text_input("📬 Email đăng ký:")
                reg_pass = st.text_input("🔑 Tạo mật khẩu:", type="password")
                btn_register = st.form_submit_button("Đăng Ký Tài Khoản", use_container_width=True)
                
                if btn_register:
                    if reg_name and reg_email and reg_pass:
                        success, msg = register_user(reg_email, reg_pass, reg_name)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("⚠️ Vui lòng điền trọn vẹn thông tin yêu cầu!")

# ==========================================
# MÀN HÌNH CHÍNH 2: ĐÃ ĐĂNG NHẬP THÀNH CÔNG
# ==========================================
else:
    teacher_name = st.session_state.user_info["ho_ten"]
    teacher_email = st.session_state.user_info["email"]

    with st.sidebar:
        st.title("🤖 AutoExam AI")
        st.markdown(f"👋 Xin chào, **Thầy/Cô {teacher_name}**")
        st.caption(f"Tài khoản: {teacher_email}")
        
        if st.button("🚪 Đăng xuất khỏi hệ thống", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            cookie_manager.delete("logged_in_user")
            cookie_manager.delete("login_timestamp")
            st.rerun()
            
        st.divider()
        
        st.subheader("🔐 Cấu hình API")
        st.markdown("Vui lòng cung cấp API Key để sử dụng tài nguyên AI.")
        user_api_key = st.text_input("Nhập Gemini API Key của bạn:", type="password")
        
        # 👉 CẬP NHẬT TẠI ĐÂY: Thêm gemini/2.5-pro vào danh sách chọn
        st.session_state.ai_model = st.selectbox(
            "🧠 Chọn phiên bản AI:",
            ["gemini/2.5-pro", "gemini/3.5-flash", "gemini/2.5-flash", "gemini/2.5-flash-lite"],
            index=["gemini/2.5-pro", "gemini/3.5-flash", "gemini/2.5-flash", "gemini/2.5-flash-lite"].index(st.session_state.ai_model)
        )
        
        if user_api_key:
            os.environ["GEMINI_API_KEY"] = user_api_key
            st.success("✅ Đã ghi nhận API Key!")
        else:
            st.warning("⚠️ Hệ thống đang chờ khóa API.")
            st.markdown("[👉 Lấy API Key miễn phí tại đây](https://aistudio.google.com/app/apikey)")
        
        st.divider()
        st.subheader("📦 Đề Thi Của Bạn")
        st.info(f"Số lượng câu hỏi trong đề: **{len(st.session_state.exam_cart)}**")
        if st.button("🗑️ Xóa làm lại đề", use_container_width=True):
            st.session_state.exam_cart = []
            st.rerun()

    # Giao diện thân trang web
    col_left, col_right = st.columns([1, 2.5])

    with col_left:
        st.header("⚙️ Sáng tác mới")
        danh_sach_chu_de = [
            "🔹 TOÁN HỌC CƠ BẢN", "🔹 TOÁN HỌC NÂNG CAO", "🔹 MẢNG & HAI CON TRỎ", 
            "🔹 THUẬT TOÁN THAM LAM (Greedy)", "🔹 CẤU TRÚC DỮ LIỆU NÂNG CAO", 
            "🔹 QUY HOẠCH ĐỘNG", "🔹 ĐỒ THỊ"
        ]
        chu_de_chon = st.selectbox("📌 Chọn dạng bài chuyên sâu:", danh_sach_chu_de)
        muc_do = st.select_slider("🔥 Mức độ khó:", options=["Dễ (Cấp Trường)", "Trung bình (Tin học Trẻ/Quận)", "Khó (HSG Tỉnh/Thành phố)"])
        btn_tao_de = st.button("🚀 Yêu cầu AI sáng tác", use_container_width=True, type="primary")

    with col_right:
        if btn_tao_de:
            if not user_api_key:
                st.error("🔒 Bạn phải nhập API Key ở thanh bên trái!")
            else:
                with st.spinner(f"AI đang biên soạn bài toán..."):
                    try:
                        ket_qua_raw = generate_exam(chu_de_chon, muc_do, st.session_state.ai_model)
                        clean_text = ket_qua_raw.strip().replace('```json', '').replace('```', '')
                        parsed_problem = json.loads(clean_text)
                        st.session_state.current_problem = parsed_problem
                        
                        # Gọi hàm lưu DB (Bây giờ bảng Supabase đã đủ cột, sẽ lưu mượt mà)
                        success = save_to_db(parsed_problem.get('title', 'Untitled'), parsed_problem, user_email=teacher_email)
                        if success:
                            st.toast("🎉 Đã lưu tự động bài toán vào Kho cá nhân của bạn!")
                        else:
                            st.error("❌ Không thể đẩy bài toán lên Cloud. Hãy kiểm tra lại kết nối!")
                        
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
                            st.error("⏳ **API Key này đã hết hạn mức sử dụng tạm thời!**")
                        elif "json" in error_msg:
                            st.error("⚠️ AI vừa trả về kết quả không chuẩn định dạng. Vui lòng bấm tạo lại!")
                        else:
                            st.error(f"🔴 Lỗi hệ thống: {e}")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📖 Câu hỏi hiện tại", "💻 Dữ liệu JSON", "📑 ĐỀ THI TỔNG HỢP", 
            "📂 KHO BÀI CỦA TÔI", "🌐 THƯ VIỆN CỘNG ĐỒNG"
        ])
        
        if st.session_state.current_problem:
            prob = st.session_state.current_problem
            with tab1:
                st.header(prob.get("title", "Bài toán chưa có tên"))
                if st.button("➕ THÊM BÀI TOÁN NÀY VÀO ĐỀ THI TỔNG HỢP", type="primary"):
                    st.session_state.exam_cart.append(prob)
                    st.success("Đã thêm vào đề thi! Chuyển sang Tab 3.")
                    st.rerun()

                st.divider()
                st.markdown("### 📝 Cốt truyện & Yêu cầu")
                st.write(prob.get("legend", ""))
                
                in_col, out_col = st.columns(2)
                with in_col:
                    st.markdown("### 📥 Đầu vào (Input)")
                    st.info(prob.get("input_format", ""))
                with out_col:
                    st.markdown("### 📤 Đầu ra (Output)")
                    st.warning(prob.get("output_format", ""))
                    
                st.markdown("### 🛑 Giới hạn & Subtask")
                st.error(prob.get("constraints", ""))
                
                st.markdown("### 💡 Ví dụ (Test Cases)")
                for i, tc in enumerate(prob.get("test_cases", [])):
                    st.markdown(f"**Ví dụ {i+1}:**")
                    tc_col1, tc_col2 = st.columns(2)
                    with tc_col1: st.code(tc.get("input_data", ""), language="text")
                    with tc_col2: st.code(tc.get("output_data", ""), language="text")
                    st.markdown(f"***Giải thích:*** *{tc.get('explanation', '')}*")
                    st.write("---")

                st.markdown("### 📖 Gợi ý & Lời giải")
                if prob.get("hints"):
                    for idx, hint in enumerate(prob.get("hints", [])):
                        st.markdown(f"**Gợi ý {idx + 1}:** {hint}")
                st.info(prob.get("editorial", "Chưa có lời giải chi tiết."))

                with st.expander("🔐 Khu vực Giáo viên: Mã nguồn giải mẫu"):
                    is_valid, val_msg = validate_python_code(prob.get("python_solution", ""))
                    if is_valid:
                        st.success(val_msg)
                    else:
                        st.error(val_msg)
                    st.markdown("**C++:**")
                    st.code(prob.get("c_plus_plus_solution", ""), language="cpp")
                    st.markdown("**Python:**")
                    st.code(prob.get("python_solution", ""), language="python")
            with tab2:
                st.json(prob, expanded=False)
        else:
            with tab1: st.info("👈 Hãy nhập API Key và tạo đề bài mới để bắt đầu.")
            with tab2: st.info("Chưa có dữ liệu JSON.")

        with tab3:
            if len(st.session_state.exam_cart) == 0:
                st.warning("Đề thi đang trống.")
            else:
                st.subheader("Danh sách các câu hỏi:")
                for idx, p in enumerate(st.session_state.exam_cart):
                    st.markdown(f"**Câu {idx + 1}:** {p.get('title', 'N/A')}")
                
                st.divider()
                st.markdown("### ⚙️ Xây dựng Script Sinh Test Chấm Tự Động")
                if st.button("🏭 Viết Script sinh Test (Generator.py) cho toàn bộ Đề", type="primary"):
                    with st.spinner("AI đang lập trình file Generator.py..."):
                        try:
                            for idx, p in enumerate(st.session_state.exam_cart):
                                if "generator_script" not in p:
                                    folder_name = p.get('title', f'BAI{idx+1}').split()[0].upper()
                                    raw_script = generate_test_script(p, folder_name, st.session_state.ai_model)
                                    clean_script_json = raw_script.strip().replace('```json', '').replace('```', '')
                                    parsed_script = json.loads(clean_script_json)
                                    script_code = parsed_script.get("generator_code", "")
                                    
                                    is_ok, msg = validate_python_code(script_code)
                                    if not is_ok:
                                        st.warning(f"Cảnh báo tại bài {folder_name}: {msg}")
                                        
                                    st.session_state.exam_cart[idx]["generator_script"] = script_code
                            st.success("Tuyệt vời! Đã lập trình xong các file Generator.")
                        except Exception as e:
                            error_msg = str(e).lower()
                            if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
                                st.error(f"⏳ **Hệ thống quá tải khi đang xử lý đến bài số {idx + 1}. API Key đã hết hạn mức!**")
                                st.warning("💡 Vui lòng nhập API Key mới ở thanh bên, sau đó bấm nút này lần nữa (hệ thống sẽ tự động chạy tiếp các bài chưa làm).")
                            else:
                                st.error(f"Lỗi hệ thống: {e}")

                st.divider()
                st.markdown("### 📥 Tải xuống Đề Thi & Đáp Án")
                dl_col1, dl_col2, dl_col3 = st.columns(3)
                with dl_col1:
                    word_file = create_word_document(st.session_state.exam_cart)
                    st.download_button(label="📄 TẢI ĐỀ THI (.docx)", file_name="De_Thi.docx", data=word_file, use_container_width=True)
                with dl_col2:
                    exam_string = json.dumps({"problems": st.session_state.exam_cart}, ensure_ascii=False, indent=4)
                    st.download_button(label="💾 TẢI DỮ LIỆU (JSON)", file_name="de_thi.json", data=exam_string, use_container_width=True)
                with dl_col3:
                    zip_file = create_themis_zip(st.session_state.exam_cart)
                    st.download_button(label="🗂 TẢI BỘ ĐÁP ÁN (.ZIP)", file_name="Dap_An.zip", data=zip_file, type="primary", use_container_width=True)

        # TAB 4: KHO BÀI CỦA TÔI
        with tab4:
            st.subheader("📂 Kho lưu trữ đề thi cá nhân")
            user_rows = load_user_history(teacher_email)
            
            if not user_rows:
                st.info("📭 Kho cá nhân của bạn hiện đang trống. Hãy tạo đề mới ở cột bên trái!")
            else:
                for row in user_rows:
                    db_id, db_title, db_json_str, is_public = row
                    status_label = "🌐 Đang công khai" if is_public else "🔒 Chỉ mình tôi"
                    
                    with st.expander(f"📚 {db_title} ({status_label})"):
                        share_col, add_col = st.columns(2)
                        with share_col:
                            share_btn_text = "🔒 Thu hồi về riêng tư" if is_public else "🌐 Chia sẻ lên cộng đồng"
                            if st.button(share_btn_text, key=f"toggle_{db_id}"):
                                if toggle_share_status(db_id, is_public):
                                    st.success("🔄 Đã cập nhật trạng thái chia sẻ!")
                                    st.rerun()
                        with add_col:
                            if st.button(f"➕ Thêm bài vào đề tổng hợp", key=f"add_user_{db_id}"):
                                st.session_state.exam_cart.append(json.loads(db_json_str))
                                st.success("Đã thêm bài!")
                                st.rerun()
                        st.json(json.loads(db_json_str), expanded=False)

        # TAB 5: THƯ VIỆN CỘNG ĐỒNG
        with tab5:
            st.subheader("🌐 Ngân hàng đề thi chia sẻ nội bộ giáo viên")
            public_rows = load_public_gallery()
            
            if not public_rows:
                st.info("📭 Hiện chưa có bài viết nào được chia sẻ trong cộng đồng.")
            else:
                for row in public_rows:
                    pub_id, pub_title, pub_json_str, pub_author = row
                    author_tag = "Bạn đóng góp" if pub_author == teacher_email else f"Tác giả: {pub_author}"
                    
                    with st.expander(f"📖 {pub_title} ({author_tag})"):
                        if st.button(f"➕ Lấy bài này đưa vào đề tổng hợp", key=f"add_pub_{pub_id}"):
                            st.session_state.exam_cart.append(json.loads(pub_json_str))
                            st.success("Đã lấy bài!")
                            st.rerun()
                        st.json(json.loads(pub_json_str), expanded=False)