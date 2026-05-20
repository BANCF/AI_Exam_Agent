import sqlite3
import json
import re

# Khởi tạo DB
def init_db():
    conn = sqlite3.connect('exam_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  json_data TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(title, problem_json):
    conn = sqlite3.connect('exam_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (title, json_data) VALUES (?, ?)", (title, json.dumps(problem_json)))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect('exam_history.db')
    c = conn.cursor()
    c.execute("SELECT id, title, json_data FROM history ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# Trình kiểm tra lỗi code Python
def validate_python_code(code_str):
    try:
        compile(code_str, '<string>', 'exec')
        return True, "✅ Code Python chuẩn cú pháp, không phát hiện lỗi."
    except SyntaxError as e:
        return False, f"❌ Lỗi cú pháp Python: Dòng {e.lineno} - {e.msg}"
    except Exception as e:
        return False, f"❌ Lỗi biên dịch: {e}"

# Làm sạch LaTeX cho Word
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