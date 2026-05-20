import os
from pydantic import BaseModel
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from crewai import Agent, Task, Crew, LLM

# --- CẤU TRÚC JSON ---
class TestCase(BaseModel):
    input_data: str
    output_data: str
    explanation: str

class CodingProblem(BaseModel):
    title: str
    legend: str 
    input_format: str
    output_format: str
    constraints: str
    c_plus_plus_solution: str
    python_solution: str
    editorial: str
    hints: List[str]
    test_cases: List[TestCase]

class TestGeneratorScript(BaseModel):
    generator_code: str

# --- HÀM TẠO LLM ---
def create_llm():
    return LLM(
        model="gemini/gemini-3.5-flash",
        temperature=0.7,
        api_key=os.environ.get("GEMINI_API_KEY", "")
    )

# --- HÀM ĐỌC RAG (NGÂN HÀNG KIẾN THỨC) ---
def get_context_from_rag(topic):
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        docs = db.similarity_search(topic, k=1)
        if docs:
            return docs[0].page_content
    except Exception as e:
        pass
    return "Hãy tự do sáng tạo theo chuẩn thi đấu Tin học."

# --- HÀM TẠO ĐỀ THI (HÀM CHÍNH ĐANG BỊ THIẾU) ---
def generate_exam(topic_name, difficulty):
    llm_instance = create_llm()
    context = get_context_from_rag(topic_name)
    
    problem_setter = Agent(
        role='Cục trưởng Ban ra đề thi Tin học Quốc Gia',
        goal='Sáng tác bài toán lập trình thi đấu cực hay, có cốt truyện thu hút.',
        backstory='Bạn là Admin của VNOI. Chuyên ra đề thi HSG Tin học, văn phong rõ ràng, lôi cuốn.',
        verbose=False, 
        llm=llm_instance
    )
    
    judge_solver = Agent(
        role='Huấn luyện viên Thuật toán',
        goal='Viết mã nguồn, lời giải chi tiết (Editorial) và gợi ý (Hints).',
        backstory='Bạn là Grandmaster Codeforces, am hiểu kỹ thuật thi đấu hiện đại và rất giỏi sư phạm.',
        verbose=False, 
        llm=llm_instance
    )
    
    task_generate = Task(
        description=f'''Dựa trên bối cảnh: {context}
Hãy sáng tác 1 bài toán Tin học mới về chủ đề: "{topic_name}". Mức độ khó: {difficulty}.
YÊU CẦU:
- Có cốt truyện (Legend) sáng tạo, hấp dẫn.
- Rõ ràng Input/Output và Giới hạn dữ liệu.
- Chia ít nhất 2 Subtask để phân loại điểm học sinh.''',
        expected_output='Đề thi Markdown.', 
        agent=problem_setter
    )
    
    task_solve = Task(
        description='''Đọc đề bài vừa tạo. Viết code giải mẫu và Lời giải.
YÊU CẦU ĐỐI VỚI BẠN:
1. C++ Solution: Dùng `#include <bits/stdc++.h>`, `using namespace std;`, `cin.tie(NULL);`.
2. Editorial: Viết 1 đoạn văn giải thích ngắn gọn tư duy thuật toán để học sinh đọc hiểu được.
3. Hints: 3 gạch đầu dòng gợi ý mở khóa tư duy.
4. Test Cases: 3 test cases mẫu có giải thích.''',
        expected_output='JSON chứa đề, code, editorial, hints và test cases.', 
        output_pydantic=CodingProblem, 
        agent=judge_solver
    )
    
    crew = Crew(agents=[problem_setter, judge_solver], tasks=[task_generate, task_solve], verbose=False, max_rpm=10)
    return crew.kickoff().raw

# --- HÀM TẠO SCRIPT SINH TEST CASE ---
def generate_test_script(problem_dict, folder_name):
    llm_instance = create_llm()
    tc_generator = Agent(
        role='Chuyên gia sinh Script Test (Themis/CMS)',
        goal='Viết script Python sinh dữ liệu khổng lồ bám sát subtask.',
        backstory='Bạn chuyên viết script tự động. Code chạy mượt, không lỗi cú pháp.',
        verbose=False, 
        llm=llm_instance
    )
    
    task_tc = Task(
        description=f'''Dưới đây là bài toán:
Giới hạn: {problem_dict.get('constraints')}
Code Python chuẩn: 
{problem_dict.get('python_solution')}

NHIỆM VỤ: Viết nội dung file `generator.py` để sinh 10 bộ Test (Test01-Test10).
1. Import `os`, `random`.
2. Tạo vòng lặp sinh 10 thư mục.
3. Phân bổ N bám sát Subtask.
4. Mở file `TestXX/{folder_name}.INP` ghi Input sinh ngẫu nhiên.
5. Đọc lại Input, chạy qua logic Code Python chuẩn, ghi kết quả vào `TestXX/{folder_name}.OUT`.
CHỈ TRẢ VỀ MÃ PYTHON DẠNG THUẦN.''',
        expected_output='Một file code Python hoàn chỉnh.',
        output_pydantic=TestGeneratorScript, 
        agent=tc_generator
    )
    
    crew = Crew(agents=[tc_generator], tasks=[task_tc], verbose=False, max_rpm=10)
    return crew.kickoff().raw