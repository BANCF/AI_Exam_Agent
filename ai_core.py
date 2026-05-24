import os
import json
from crewai import Agent, Task, Crew, LLM
from langchain_google_genai import ChatGoogleGenerativeAI

# ==========================================
# KHỞI TẠO BỘ NÃO AI (LLM) ĐÃ ĐƯỢC FIX TRIỆT ĐỂ
# ==========================================
def create_llm(model_name="gemini/3.5-flash"):
    """
    Khởi tạo mô hình AI chuẩn hóa theo quy định của CrewAI và Google.
    Giải quyết triệt để lỗi 'Unable to initialize LLM'.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Lỗi hệ thống: Không tìm thấy API Key. Vui lòng cấu hình ở thanh bên trái!")

    # Chuẩn hóa tên model để tránh lỗi nhận diện cấu trúc hệ thống
    # CrewAI yêu cầu định dạng: "gemini/tên_model_gốc"
    
    # 👉 THÊM ĐIỀU KIỆN CHO DÒNG PRO TẠI ĐÂY
    if "2.5-pro" in model_name or "2.5-pro" in model_name:
        target_model = "gemini/gemini-2.5-pro"
        current_temp = 0.2  # Mô hình suy luận toán học cần temp thấp để tránh "bốc phét" số liệu
    elif "3.5" in model_name:
        target_model = "gemini/gemini-3.5-flash"
        current_temp = 0.5  
    elif "2.5-flash-lite" in model_name:
        target_model = "gemini/gemini-2.5-flash-lite"
        current_temp = 0.5
    elif "2.5-flash" in model_name:
        target_model = "gemini/gemini-2.5-flash"
        current_temp = 0.5
    else:
        target_model = "gemini/gemini-1.5-flash" # Bản dự phòng ổn định nhất
        current_temp = 0.5

    return LLM(
        model=target_model,
        temperature=current_temp,  # Áp dụng mức nhiệt độ động tương ứng với từng dòng model
        api_key=api_key
    )

# ==========================================
# LUỒNG 1: SÁNG TÁC ĐỀ THI
# ==========================================
def generate_exam(topic_name, difficulty, model_name="gemini/3.5-flash"):
    # Gọi hàm khởi tạo LLM với model được chọn
    llm_instance = create_llm(model_name)
    
    exam_creator = Agent(
        role='Chuyên gia ra đề thi Tin học Quốc gia (VNOI/Codeforces)',
        goal=f'Sáng tác 1 bài toán lập trình thi đấu chuẩn về chủ đề {topic_name} với độ khó {difficulty}',
        backstory='Bạn là một giáo viên Tin học chuyên nghiệp tại Việt Nam, chuyên biên soạn đề thi Học sinh giỏi. Bài toán phải có cốt truyện hấp dẫn, logic chặt chẽ, giới hạn dữ liệu phân tách theo từng Subtask điểm và bắt buộc có chính xác 10 test cases mẫu.',
        llm=llm_instance,
        allow_delegation=False
    )

    create_task = Task(
        description=f'''
        Sáng tác MỘT (01) bài toán lập trình thi đấu duy nhất. 
        Chủ đề: {topic_name}. Mức độ: {difficulty}.
        
        👉 QUY TRÌNH TƯ DUY RỜI RẠC (CHAIN-OF-THOUGHT) BẮT BUỘC:
        Trước khi viết chuỗi JSON kết quả, bạn phải tự chạy các bước phân tích và lập luận ngầm sau đây:
        - Bước 1: Xác định thuật toán tối ưu nhất cho chủ đề này (Ví dụ: Quy hoạch động, Cây phân đoạn Segment Tree, hay Tham lam).
        - Bước 2: Xác định rõ ràng vị trí của các "bẫy biên". Nếu mảng toàn số 0, mảng có 1 phần tử, hoặc số âm thì thuật toán tối ưu có bị chạy sai không?
        - Bước 3: Lên kế hoạch phân bổ con số cho chính xác 10 testcases. Đảm bảo các Test 8, 9, 10 phải có giá trị số lớn chạm sát cấu hình `long long` trong C++ ($10^{18}$) để kiểm tra xem học sinh có biết tối ưu kiểu dữ liệu hay không.

        YÊU CẦU NGHIÊM NGẶT VỀ THIẾT KẾ ĐỀ THI:
        1. Cấu trúc trường "constraints": Bắt buộc phải phân tách giới hạn dữ liệu rõ ràng thành 3 Subtask kèm theo tỷ lệ điểm cụ thể như sau để cấu hình hệ thống chấm tự động:
           - Subtask 1 (40% số điểm): Giới hạn dữ liệu cực nhỏ (Ví dụ: N <= 100 hoặc N <= 15) dành cho thuật toán duyệt trâu/vét cạn/quay lui.
           - Subtask 2 (30% số điểm): Giới hạn dữ liệu trung bình (Ví dụ: N <= 10^5) dành cho thuật toán tối ưu xấp xỉ O(N) hoặc O(N log N).
           - Subtask 3 (30% số điểm): Giới hạn dữ liệu kịch trần (Ví dụ: N <= 10^9 hoặc 10^18) hoặc các trường hợp đặc biệt cực hạn, đòi hỏi xử lý bẫy tràn số, tối ưu bộ nhớ hoặc thuật toán toán học nâng cao.
        
        2. Cấu trúc mảng "test_cases": Bắt buộc phải sinh ra chính xác ĐỦ MƯỜI (10) TESTCASES mẫu. Dữ liệu của 10 testcase này phải được phân bổ nghiêm ngặt để kiểm thử trực tiếp 3 Subtask trên theo đúng tỷ lệ:
           - Test 1 đến Test 4: Dữ liệu thuộc phạm vi Subtask 1.
           - Test 5 đến Test 7: Dữ liệu thuộc phạm vi Subtask 2.
           - Test 8 đến Test 10: Dữ liệu kịch trần kịch khung của Subtask 3, đồng thời chủ động chèn các test bẫy biên (Ví dụ: mảng toàn số âm, số lớn nhất, số nhỏ nhất, dữ liệu rỗng hoặc không có kết quả) để test độ chặt chẽ của code học sinh.

        Yêu cầu trả về DUY NHẤT một chuỗi JSON hợp lệ theo cấu trúc sau (không có văn bản thừa, không dùng markdown block):
        {{
            "title": "Tên bài toán (Ngắn gọn, in hoa)",
            "legend": "Cốt truyện và yêu cầu chi tiết của bài toán",
            "input_format": "Định dạng dữ liệu vào (Ví dụ: Dòng đầu ghi số N...)",
            "output_format": "Định dạng dữ liệu ra (Ví dụ: In ra một số nguyên duy nhất...)",
            "constraints": "Mô tả chi tiết giới hạn và ràng buộc của từng Subtask 1, 2, 3 kèm tỷ lệ điểm cụ thể như yêu cầu bên trên",
            "test_cases": [
                {{"input_data": "dữ liệu test 1 (Subtask 1)", "output_data": "kết quả chuẩn 1", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 2 (Subtask 1)", "output_data": "kết quả chuẩn 2", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 3 (Subtask 1)", "output_data": "kết quả chuẩn 3", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 4 (Subtask 1)", "output_data": "kết quả chuẩn 4", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 5 (Subtask 2)", "output_data": "kết quả chuẩn 5", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 6 (Subtask 2)", "output_data": "kết quả chuẩn 6", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 7 (Subtask 2)", "output_data": "kết quả chuẩn 7", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 8 (Subtask 3 - Biên bẫy)", "output_data": "kết quả chuẩn 8", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 9 (Subtask 3 - Biên bẫy)", "output_data": "kết quả chuẩn 9", "explanation": "giải thích"}},
                {{"input_data": "dữ liệu test 10 (Subtask 3 - Dữ liệu kịch trần cực đại)", "output_data": "kết quả chuẩn 10", "explanation": "giải thích"}}
            ],
            "hints": ["Gợi ý 1", "Gợi ý 2"],
            "editorial": "Hướng dẫn thuật toán chi tiết và độ phức tạp thời gian không gian tối ưu để ăn trọn điểm cả 3 subtask",
            "c_plus_plus_solution": "Mã nguồn C++ mẫu chuẩn chỉnh, xử lý được dữ liệu cực đại của Subtask 3",
            "python_solution": "Mã nguồn Python mẫu chuẩn chỉnh, xử lý được dữ liệu cực đại của Subtask 3"
        }}
        ''',
        expected_output='Chuỗi JSON hợp lệ chứa toàn bộ thông tin bài toán có đầy đủ 3 subtask và cấu trúc chính xác 10 testcases sau khi đã chạy qua quy trình tư duy Chain-of-Thought.',
        agent=exam_creator
    )

    # Thêm memory=True vào Crew để lưu trữ chuỗi tư duy logic giữa Agent và Task
    crew = Crew(
        agents=[exam_creator],
        tasks=[create_task],
        memory=True,
        verbose=False
    )

    result = crew.kickoff()
    return result.raw
# ==========================================
# LUỒNG 2: LẬP TRÌNH SCRIPT TẠO TEST CASE
# ==========================================
def generate_test_script(problem_json, folder_name, model_name="gemini/3.5-flash"):
    # Gọi hàm khởi tạo LLM với model được chọn
    llm_instance = create_llm(model_name)
    
    constraints = problem_json.get('constraints', '')
    input_format = problem_json.get('input_format', '')
    title_name = problem_json.get('title', folder_name)
    
    script_coder = Agent(
        role='Kỹ sư kiểm thử phần mềm chuyên nghiệp (Senior Test Engineer)',
        goal=f'Viết bộ mã nguồn Python (generator.py) tự động sinh và phân bổ 10 thư mục test case chuẩn Themis cho bài toán {folder_name}',
        backstory='Bạn là chuyên gia lão luyện về xây dựng hệ thống test case tự động cho các kỳ thi Học sinh giỏi Tin học sử dụng phần mềm chấm bài Themis. Bạn am hiểu sâu sắc cách viết các hàm sinh ngẫu nhiên phân chia theo từng phân vùng giới hạn dữ liệu (Subtasks).',
        llm=llm_instance,
        allow_delegation=False
    )
    
    coding_task = Task(
        description=f'''
        Dựa vào thông tin chi tiết của bài toán {title_name} (Tên viết tắt cấu trúc file: {folder_name}):
        - Ràng buộc và Subtasks: {constraints}
        - Cấu trúc dữ liệu Input: {input_format}
        
        Nhiệm vụ của bạn là lập trình MỘT file mã nguồn Python hoàn chỉnh (đặt tên là generator.py) có khả năng tự động tạo ra toàn bộ bộ dữ liệu chấm thi. 
        
        MÃ NGUỒN PYTHON TRONG FILE GENERATOR.PY BẮT BUỘC PHẢI THỰC HIỆN ĐỦ CÁC BƯỚC SAU:
        1. import đầy đủ các thư viện cần thiết như `os`, `random`, `sys`, `subprocess`.
        2. Viết các hàm sinh dữ liệu ngẫu nhiên (sinh số, sinh mảng, sinh chuỗi...) bám sát định dạng cấu trúc Input yêu cầu. Các biến cách nhau bằng dấu cách hoặc xuống dòng chuẩn chỉ.
        3. Sử dụng vòng lặp để tự động hóa việc tạo ra đúng mười (10) thư mục con đặt tên từ 'Test01', 'Test02', ..., 'Test10' nằm trong thư mục gốc của bài toán.
        4. Trong cấu trúc vòng lặp sinh 10 testcase, bạn phải khống chế chặt chẽ giới hạn dữ liệu ngẫu nhiên phân bổ theo đúng 3 Subtask của đề bài:
           - Từ Test01 đến Test04 (Thỏa mãn Subtask 1): Khống chế sinh dữ liệu cực nhỏ (Ví dụ: N <= 100 hoặc N <= 15) dành cho thuật toán duyệt trâu/vét cạn.
           - Từ Test05 đến Test07 (Thỏa mãn Subtask 2): Khống chế sinh dữ liệu trung bình (Ví dụ: N <= 10^5) dành cho thuật toán tối ưu xấp xỉ O(N) hoặc O(N log N).
           - Từ Test08 đến Test10 (Thỏa mãn Subtask 3): Sinh dữ liệu kịch trần biên giới hạn (Ví dụ: N <= 10^9 hoặc 10^18). Đặc biệt, trong các test này phải chủ động chèn cố định các trường hợp biên nguy hiểm (mảng toàn số âm, mảng rỗng, giá trị lớn nhất, nhỏ nhất, số 0...) để test bẫy học sinh.
        5. Quy trình ghi file ở mỗi thư mục Test (Ví dụ tại thư mục Test01):
           - Tạo file đầu vào đặt tên chính xác là: `{folder_name}.INP` và ghi dữ liệu vừa sinh ngẫu nhiên vào đó.
           - Sử dụng thư viện `subprocess` để gọi thực thi ngầm file giải mẫu (hệ thống sẽ tự biên dịch mã nguồn mẫu thành file chạy, code generator của bạn chỉ cần gọi thực thi file chạy đó, đọc dữ liệu từ `{folder_name}.INP` và xuất kết quả chuẩn ra file `{folder_name}.OUT` nằm cùng thư mục Test đó).
        
        Mã nguồn Python được sinh ra phải sạch sẽ, có chú thích rõ ràng bằng tiếng Việt và chạy được ngay lập tức.

        Trả về DUY NHẤT một chuỗi JSON theo cấu trúc sau (không có văn bản thừa, không bọc trong ký hiệu markdown block):
        {{
            "generator_code": "import os\\nimport random\\nimport subprocess\\n# Mã nguồn Python hoàn chỉnh sinh 10 folder test bám sát cấu trúc Subtask tại đây..."
        }}
        ''',
        expected_output='Chuỗi JSON chứa mã nguồn Python hoàn chỉnh lập trình bộ sinh test case phân chia theo Subtask và tạo thư mục Themis.',
        agent=script_coder
    )

    crew = Crew(
        agents=[script_coder],
        tasks=[coding_task],
        memory=True,
        verbose=False
    )

    result = crew.kickoff()
    return result.raw