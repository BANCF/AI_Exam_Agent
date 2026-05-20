import os
import json
import streamlit as st

# Import các hàm sức mạnh từ 3 file module chúng ta vừa tạo
from utils import init_db, save_to_db, load_history, validate_python_code
from export_tools import create_word_document, create_themis_zip
from ai_core import generate_exam, generate_test_script

# Khởi chạy Database ngầm
init_db()

# ==========================================
# GIAO DIỆN WEB VỚI STREAMLIT
# ==========================================
st.set_page_config(page_title="Hệ Thống Đề Thi - SmartEdu", layout="wide", page_icon="📝")

# --- SIDEBAR: CẤU HÌNH API KEY TỪ NGƯỜI DÙNG ---
st.sidebar.header("🔐 Cấu hình Hệ thống")
st.sidebar.markdown("Vui lòng cung cấp API Key để sử dụng tài nguyên suy luận của AI.")
user_api_key = st.sidebar.text_input("Nhập Gemini API Key của bạn:", type="password")

if user_api_key:
    os.environ["GEMINI_API_KEY"] = user_api_key
    st.sidebar.success("✅ Đã ghi nhận API Key!")
else:
    st.sidebar.warning("⚠️ Hệ thống đang chờ khóa API.")

# --- QUẢN LÝ TRẠNG THÁI ---
if "exam_cart" not in st.session_state:
    st.session_state.exam_cart = []
if "current_problem" not in st.session_state:
    st.session_state.current_problem = None

# --- GIAO DIỆN CHÍNH ---
st.title("🤖 Hệ Thống Trí Tuệ Nhân Tạo Biên Soạn Đề Thi")
st.markdown("Sinh bài tập chuẩn VNOI/Codeforces, tự động viết script test cho Themis/CMS.")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.header("⚙️ Sáng tác câu hỏi mới")
    
    danh_sach_chu_de = [
        "🔹 TOÁN HỌC CƠ BẢN", 
        "🔹 TOÁN HỌC NÂNG CAO", 
        "🔹 MẢNG & HAI CON TRỎ", 
        "🔹 THUẬT TOÁN THAM LAM (Greedy)", 
        "🔹 CẤU TRÚC DỮ LIỆU NÂNG CAO", 
        "🔹 QUY HOẠCH ĐỘNG", 
        "🔹 ĐỒ THỊ"
    ]
    chu_de_chon = st.selectbox("📌 Chọn dạng bài chuyên sâu:", danh_sach_chu_de)
    muc_do = st.select_slider("🔥 Mức độ khó:", options=["Dễ (Cấp Trường)", "Trung bình (Tin học Trẻ/Quận)", "Khó (HSG Tỉnh/Thành phố)"])
    
    btn_tao_de = st.button("🚀 Yêu cầu AI sáng tác", use_container_width=True, type="primary")

    st.divider()
    st.header("📦 Đề Thi Của Bạn")
    st.metric("Số lượng câu hỏi trong đề:", len(st.session_state.exam_cart))
    if st.button("🗑️ Xóa làm lại đề", use_container_width=True):
        st.session_state.exam_cart = []
        st.rerun()

with col2:
    # XỬ LÝ NÚT BẤM TẠO ĐỀ
    if btn_tao_de:
        if not user_api_key:
            st.error("🔒 Bạn phải nhập API Key ở cột bên trái!")
        else:
            with st.spinner(f"AI đang biên soạn bài toán..."):
                try:
                    # Gọi hàm từ ai_core.py
                    ket_qua_raw = generate_exam(chu_de_chon, muc_do)
                    clean_text = ket_qua_raw.strip().replace('```json', '').replace('```', '')
                    parsed_problem = json.loads(clean_text)
                    st.session_state.current_problem = parsed_problem
                    
                    # Gọi hàm từ utils.py để lưu DB
                    save_to_db(parsed_problem.get('title', 'Untitled'), parsed_problem)
                except Exception as e:
                    st.error(f"Lỗi hệ thống: {e}")

    # CHIA TABS GIAO DIỆN
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Câu hỏi hiện tại", "💻 Dữ liệu JSON", "📑 ĐỀ THI TỔNG HỢP", "🗄️ NGÂN HÀNG ĐỀ"])
    
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
                with tc_col1:
                    st.code(tc.get("input_data", ""), language="text")
                with tc_col2:
                    st.code(tc.get("output_data", ""), language="text")
                st.markdown(f"***Giải thích:*** *{tc.get('explanation', '')}*")
                st.write("---")

            st.markdown("### 📖 Gợi ý & Lời giải (Editorial)")
            if prob.get("hints"):
                for idx, hint in enumerate(prob.get("hints", [])):
                    st.markdown(f"**Gợi ý {idx + 1}:** {hint}")
            st.info(prob.get("editorial", "Chưa có lời giải chi tiết."))

            with st.expander("🔐 Khu vực Giáo viên: Mã nguồn giải mẫu"):
                # Kiểm tra code bằng hàm từ utils.py
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
        with tab1:
            st.info("👈 Hãy nhập API Key, chọn chủ đề và bấm 'Yêu cầu AI sáng tác' để bắt đầu.")

    # TAB 3: QUẢN LÝ ĐỀ THI
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
                if not user_api_key:
                    st.error("🔒 Vui lòng nhập API Key!")
                else:
                    with st.spinner("AI đang lập trình file Generator.py..."):
                        try:
                            for idx, p in enumerate(st.session_state.exam_cart):
                                if "generator_script" not in p:
                                    folder_name = p.get('title', f'BAI{idx+1}').split()[0].upper()
                                    # Gọi hàm AI từ ai_core.py
                                    raw_script = generate_test_script(p, folder_name)
                                    clean_script_json = raw_script.strip().replace('```json', '').replace('```', '')
                                    parsed_script = json.loads(clean_script_json)
                                    script_code = parsed_script.get("generator_code", "")
                                    
                                    # Chạy Validator check lỗi cú pháp file sinh Test
                                    is_ok, msg = validate_python_code(script_code)
                                    if not is_ok:
                                        st.warning(f"Cảnh báo tại bài {folder_name}: {msg}")
                                    
                                    st.session_state.exam_cart[idx]["generator_script"] = script_code
                            st.success("Tuyệt vời! Đã lập trình xong các file Generator.")
                        except Exception as e:
                            st.error(f"Lỗi hệ thống. Chi tiết: {e}")

            st.divider()
            st.markdown("### 📥 Tải xuống Đề Thi & Đáp Án")
            
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            
            with dl_col1:
                # Gọi hàm tạo Word từ export_tools.py
                word_file = create_word_document(st.session_state.exam_cart)
                st.download_button(
                    label="📄 TẢI ĐỀ THI (.docx)",
                    file_name="De_Thi.docx",
                    data=word_file,
                    use_container_width=True
                )

            with dl_col2:
                exam_string = json.dumps({"problems": st.session_state.exam_cart}, ensure_ascii=False, indent=4)
                st.download_button(
                    label="💾 TẢI DỮ LIỆU (JSON)",
                    file_name="de_thi.json",
                    data=exam_string,
                    use_container_width=True
                )

            with dl_col3:
                # Gọi hàm tạo ZIP từ export_tools.py
                zip_file = create_themis_zip(st.session_state.exam_cart)
                st.download_button(
                    label="🗂 TẢI BỘ ĐÁP ÁN (.ZIP)",
                    file_name="Dap_An.zip",
                    data=zip_file,
                    type="primary",
                    use_container_width=True
                )

    # TAB 4: NGÂN HÀNG ĐỀ (SQLITE CACHE)
    with tab4:
        st.subheader("🗄️ Lịch sử các bài toán đã tạo")
        st.markdown("Các bài toán này được lưu an toàn trong máy tính của bạn (Cơ sở dữ liệu SQLite).")
        
        # Gọi hàm tải DB từ utils.py
        history_rows = load_history()
        
        if not history_rows:
            st.info("Ngân hàng đề hiện đang trống. Hãy tạo thêm các bài toán mới!")
        else:
            for row in history_rows:
                db_id, db_title, db_json_str = row
                with st.expander(f"📚 {db_title} (ID: {db_id})"):
                    if st.button(f"➕ Thêm bài '{db_title}' vào đề hiện tại", key=f"add_{db_id}"):
                        st.session_state.exam_cart.append(json.loads(db_json_str))
                        st.success("Đã thêm vào Đề thi tổng hợp!")
                        st.rerun()