import io
import zipfile
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from utils import clean_latex_for_word

def create_word_document(exam_data_list):
    doc = Document()
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_so = p_header.add_run('SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ NỘI\n')
    run_so.font.name = 'Times New Roman'; run_so.font.size = Pt(13)
    run_ky_thi = p_header.add_run('KỲ THI CHỌN HỌC SINH GIỎI CẤP THÀNH PHỐ\n')
    run_ky_thi.font.name = 'Times New Roman'; run_ky_thi.font.size = Pt(13)
    run_nam = p_header.add_run('NĂM HỌC 2025 - 2026\n')
    run_nam.font.name = 'Times New Roman'; run_nam.font.size = Pt(12)
    doc.add_paragraph('________________________').alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p_mon = doc.add_paragraph()
    p_mon.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_mon = p_mon.add_run('\nĐỀ THI MÔN: TIN HỌC (LẬP TRÌNH)\n')
    run_mon.bold = True; run_mon.font.name = 'Times New Roman'; run_mon.font.size = Pt(16)
    run_tg = p_mon.add_run('Thời gian làm bài: 150 phút\n(Đề thi gồm có 0{} trang)\n'.format(len(exam_data_list)))
    run_tg.italic = True; run_tg.font.name = 'Times New Roman'; run_tg.font.size = Pt(12)

    doc.add_heading('TỔNG QUAN BÀI THI', level=2)
    table_tong_quan = doc.add_table(rows=1, cols=4)
    table_tong_quan.style = 'Table Grid'
    hdr = table_tong_quan.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Tên bài', 'File chương trình', 'File dữ liệu vào', 'File dữ liệu ra'
    for c in hdr:
        for p in c.paragraphs:
            for r in p.runs: r.bold = True

    for idx, prob in enumerate(exam_data_list):
        row = table_tong_quan.add_row().cells
        file_name = prob.get('title', f'BAI{idx+1}').split()[0].upper()
        row[0].text = f"Bài {idx + 1}: {prob.get('title', '')}"
        row[1].text = f"{file_name}.CPP / .PY"
        row[2].text = f"{file_name}.INP"
        row[3].text = f"{file_name}.OUT"
        for i in range(1, 4):
            for p in row[i].paragraphs:
                for r in p.runs: r.font.name = 'Courier New'

    doc.add_paragraph("\n")

    for idx, prob in enumerate(exam_data_list):
        doc.add_heading(f"BÀI {idx + 1} ( {prob.get('title', 'Bài toán')} )", level=1)
        doc.add_paragraph(clean_latex_for_word(prob.get('legend', '')))
        doc.add_heading('Dữ liệu vào (Input):', level=3)
        doc.add_paragraph(clean_latex_for_word(prob.get('input_format', '')))
        doc.add_heading('Kết quả ra (Output):', level=3)
        doc.add_paragraph(clean_latex_for_word(prob.get('output_format', '')))
        doc.add_heading('Giới hạn:', level=3)
        doc.add_paragraph(clean_latex_for_word(prob.get('constraints', '')))
        
        doc.add_heading('Ví dụ (Sample Test Cases):', level=3)
        for i, tc in enumerate(prob.get("test_cases", [])):
            doc.add_paragraph(f"Ví dụ {i+1}:", style='List Bullet')
            table = doc.add_table(rows=2, cols=2)
            table.style = 'Table Grid'
            table.rows[0].cells[0].text = 'Input'; table.rows[0].cells[1].text = 'Output'
            table.rows[1].cells[0].paragraphs[0].add_run(tc.get('input_data', '')).font.name = 'Courier New'
            table.rows[1].cells[1].paragraphs[0].add_run(tc.get('output_data', '')).font.name = 'Courier New'
            doc.add_paragraph(f"Giải thích: {clean_latex_for_word(tc.get('explanation', ''))}\n")
        
        if idx < len(exam_data_list) - 1: doc.add_page_break()

    byte_io = io.BytesIO()
    doc.save(byte_io)
    byte_io.seek(0)
    return byte_io

def create_themis_zip(exam_data_list):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, prob in enumerate(exam_data_list):
            folder_name = prob.get('title', f'BAI{idx+1}').split()[0].upper()
            zip_file.writestr(f"{folder_name}/{folder_name}.cpp", prob.get("c_plus_plus_solution", ""))
            zip_file.writestr(f"{folder_name}/{folder_name}.py", prob.get("python_solution", ""))
            if gen_script := prob.get("generator_script", ""):
                zip_file.writestr(f"{folder_name}/generator.py", gen_script)
                bat_content = f"@echo off\ncd /d %~dp0\necho Dang sinh 10 Test Cases cho {folder_name}...\npython generator.py\npause"
                zip_file.writestr(f"{folder_name}/make_test.bat", bat_content)
    zip_buffer.seek(0)
    return zip_buffer