import os
import json
from pydantic import BaseModel
from typing import List

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from crewai import Agent, Task, Crew, LLM

# ==========================================
# 1. CẤU HÌNH API KEY
# ==========================================
os.environ["GEMINI_API_KEY"] = "AIzaSyCnjl_VmQ9e11CcFnyp6zb1cI2SkJmzHug"

llm = LLM(
    model="gemini/gemini-3.5-flash",
    temperature=0.5,
    api_key=os.environ["GEMINI_API_KEY"]
)

# ==========================================
# 2. ĐỊNH NGHĨA CẤU TRÚC ĐẦU RA JSON
# ==========================================
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
    test_cases: List[TestCase]

# ==========================================
# 3. HÀM ĐỌC DỮ LIỆU TỪ NGÂN HÀNG ĐỀ THI RAG
# ==========================================
def get_context_from_rag(topic):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    docs = db.similarity_search(topic, k=1)
    if docs:
        return docs[0].page_content
    return "Không tìm thấy dữ liệu tham khảo."

# ==========================================
# 4. LUỒNG CHẠY CHÍNH CỦA HỆ THỐNG
# ==========================================
def main():
    topic = "Quy hoạch động - Bài toán dãy con tăng dài nhất (LIS)"
    print(f"1. Đang lục tìm dữ liệu mẫu trong kho RAG cho chủ đề: {topic}...\n")
    context = get_context_from_rag(topic)

    print("2. Khởi tạo các Chuyên gia AI (Gemini 3.5 Flash)...\n")
    
    problem_setter = Agent(
        role='Cục trưởng Ban ra đề thi Tin học',
        goal='Sáng tác một bài toán lập trình thi đấu chuẩn xác, có cốt truyện thú vị.',
        backstory='Bạn là giáo viên chuyên bồi dưỡng học sinh giỏi Tin học Quốc gia. Bạn am hiểu cách ra đề với các Subtask phân loại học sinh.',
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    judge_solver = Agent(
        role='Huấn luyện viên Thuật toán',
        goal='Viết mã nguồn tối ưu và sinh test case chuẩn.',
        backstory='Bạn là Grandmaster trên Codeforces, chuyên viết code C++ và Python mẫu mực, độ phức tạp tối ưu nhất.',
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    task_generate = Task(
        description=f'''Dựa trên phong cách và cấu trúc của đề thi mẫu sau:
{context}

Hãy sáng tác một đề thi mới hoàn toàn về chủ đề: "{topic}".
Yêu cầu:
- Có một cốt truyện (Legend) hấp dẫn.
- Rõ ràng Input/Output và Giới hạn dữ liệu (Constraints).
- Bắt buộc chia ít nhất 2 Subtask để phân loại điểm.''',
        expected_output='Nội dung đề thi dạng Markdown (không có lời giải hay mã nguồn).',
        agent=problem_setter
    )

    task_solve = Task(
        description='Đọc đề bài vừa tạo. Viết code giải mẫu chuẩn xác bằng C++ và Python 3. Sau đó tạo ra 3 bộ test case (Input/Output) kèm giải thích logic.',
        expected_output='Đề bài, code giải và test case đóng gói theo cấu trúc JSON.',
        output_pydantic=CodingProblem,
        agent=judge_solver
    )

    print("3. Hệ thống đa tác tử đang làm việc...\n")
    
    crew = Crew(
        agents=[problem_setter, judge_solver],
        tasks=[task_generate, task_solve],
        verbose=True
    )

    # Chạy CrewAI và nhận kết quả
    result = crew.kickoff()

    # Lưu kết quả ra file JSON
# Xử lý làm sạch và lưu JSON đẹp mắt
    ten_file = "de_thi_lis.json"
    with open(ten_file, "w", encoding="utf-8") as f:
        try:
            # Đôi khi AI bọc JSON trong ký tự markdown (```json ... ```), cần xóa đi
            clean_text = result.raw.strip().replace('```json', '').replace('```', '')
            # Phân tách và ghi file với tham số indent=4 để thụt lề 4 dấu cách
            parsed_json = json.loads(clean_text)
            json.dump(parsed_json, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("AI trả về định dạng hơi lỗi, lưu dạng thô...")
            f.write(result.raw)

    print("\n=======================================================")
    print(f"HOÀN TẤT! Toàn bộ đề thi và code giải đã được lưu vào file: {ten_file}")
    print("=======================================================\n")

# Dòng này kiểm tra xem file có đang được chạy trực tiếp không
if __name__ == "__main__":
    main()