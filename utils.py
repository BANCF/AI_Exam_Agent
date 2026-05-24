import os
import json
import re
import psycopg2

# ==========================================
# CẤU HÌNH KẾT NỐI CLOUD DATABASE (SUPABASE)
# ==========================================
SUPABASE_URL = os.environ.get(
    "SUPABASE_DB_URL", 
    "postgresql://postgres:Bangbadao0212@db.zaobfjkxbeltnvqaqlri.supabase.co:5432/postgres"
)

def get_db_connection():
    """Khởi tạo kết nối an toàn tới Cloud Database Supabase"""
    try:
        conn = psycopg2.connect(SUPABASE_URL)
        return conn
    except Exception as e:
        print(f"Lỗi kết nối Supabase: {e}")
        return None

def init_db():
    """Khởi tạo cấu trúc các bảng trên Đám mây nếu chưa tồn tại"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        json_data TEXT,
                        created_by TEXT DEFAULT 'anonymous',
                        is_public BOOLEAN DEFAULT FALSE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS giao_vien (
                        email TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        ho_ten TEXT
                    );
                """)
                conn.commit()
        except Exception as e:
            print(f"Lỗi khi khởi tạo các bảng: {e}")
        finally:
            conn.close()

# ==========================================
# TÍNH NĂNG ĐĂNG NHẬP / ĐĂNG KÝ THÀNH VIÊN
# ==========================================

def register_user(email, password, ho_ten):
    conn = get_db_connection()
    if not conn:
        return False, "Lỗi kết nối cơ sở dữ liệu."
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email FROM giao_vien WHERE email = %s;", (email,))
            if cursor.fetchone():
                return False, "Email này đã được đăng ký trước đó!"
            
            cursor.execute(
                "INSERT INTO giao_vien (email, password, ho_ten) VALUES (%s, %s, %s);",
                (email, password, ho_ten)
            )
            conn.commit()
            return True, "Đăng ký tài khoản thành công!"
    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"
    finally:
        conn.close()

def login_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None, "Lỗi kết nối cơ sở dữ liệu."
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT email, ho_ten FROM giao_vien WHERE email = %s AND password = %s;",
                (email, password)
            )
            user = cursor.fetchone()
            if user:
                return {"email": user[0], "ho_ten": user[1]}, "Đăng nhập thành công!"
            else:
                return None, "Sai tên tài khoản hoặc mật khẩu!"
    except Exception as e:
        return None, f"Lỗi hệ thống: {e}"
    finally:
        conn.close()

# ==========================================
# CÁC HÀM QUẢN LÝ ĐỀ THI & PHÂN QUYỀN CHIA SẺ
# ==========================================

def save_to_db(title, problem_json, user_email="anonymous"):
    """Lưu bài toán kèm theo Email người tạo"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            json_str = json.dumps(problem_json, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO history (title, json_data, created_by, is_public) VALUES (%s, %s, %s, FALSE);",
                (title, json_str, user_email)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Lỗi khi ghi dữ liệu đề thi vào Supabase: {e}")
        raise e  # Đẩy lỗi lên app.py hiển thị thông báo chi tiết
    finally:
        conn.close()

def load_user_history(user_email):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, json_data, is_public FROM history WHERE created_by = %s ORDER BY id DESC;", 
                (user_email,)
            )
            return cursor.fetchall()
    except Exception as e:
        print(f"Lỗi khi đọc kho lưu trữ cá nhân: {e}")
        return []
    finally:
        conn.close()

def load_public_gallery():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, json_data, created_by FROM history WHERE is_public = TRUE ORDER BY id DESC;"
            )
            return cursor.fetchall()
    except Exception as e:
        print(f"Lỗi khi đọc thư viện cộng đồng: {e}")
        return []
    finally:
        conn.close()

def toggle_share_status(problem_id, current_status):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            new_status = not current_status
            cursor.execute(
                "UPDATE history SET is_public = %s WHERE id = %s;",
                (new_status, problem_id)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Lỗi khi thay đổi trạng thái chia sẻ bài toán: {e}")
        return False
    finally:
        conn.close()

# ==========================================
# CÁC TÍNH NĂNG ĐỒNG BỘ GIỮ NGUYÊN
# ==========================================
def validate_python_code(code_str):
    try:
        compile(code_str, '<string>', 'exec')
        return True, "✅ Code Python chuẩn cú pháp, không phát hiện lỗi."
    except SyntaxError as e:
        return False, f"❌ Lỗi cú pháp Python: Dòng {e.lineno} - {e.msg}"
    except Exception as e:
        return False, f"❌ Lỗi biên dịch: {e}"

def clean_latex_for_word(text):
    if not text: return ""
    text = text.replace('$', '').replace('\\le', '≤').replace('\\ge', '≥')
    text = text.replace('\\times', '×').replace('\\dots', '...').replace('\\neq', '≠')
    text = text.replace('\\approx', '≈').replace('\\rightarrow', '→').replace('\\leftarrow', '←')
    text = text.replace('\\sum', '∑').replace('\\infty', '∞')
    
    superscripts = {'0':'⁰', '1':'¹', '2':'²', '3':'³', '4':'⁴', '5':'⁵', '6':'⁶', '7':'⁷', '8':'⁸', '9':'⁹'}
    text = re.sub(r'\^(\d+|\{\d+\})', lambda m: "".join([superscripts.get(c, c) for c in m.group(1).replace('{', '').replace('}', '')]), text)
    
    subscripts = {'0':'₀', '1':'₁', '2':'₂', '3':'₃', '4':'₄', '5':'₅', '6':'₆', '7':'₇', '8':'₈', '9':'₉', 'i':'ᵢ', 'j':'ⱼ', 'k':'ₖ', 'N':'ₙ', 'n':'ₙ', 'm':'ₘ'}
    text = re.sub(r'\_([a-zA-Z0-9]+|\{[a-zA-Z0-9]+\})', lambda m: "".join([subscripts.get(c, c) for c in m.group(1).replace('{', '').replace('}', '')]), text)
    return text.replace('\\', '')