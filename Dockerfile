# Sử dụng Python phiên bản gọn nhẹ chuẩn hóa
FROM python:3.10-slim

# Thiết lập thư mục làm việc bên trong Container
WORKDIR /app

# Cài đặt các công cụ hệ thống cần thiết cho C++ và PostgreSQL (Nếu cần biên dịch mã nguồn mẫu)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy danh sách thư viện và tiến hành cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn dự án vào trong Container
COPY . .

# Mở cổng 8501 mặc định của Streamlit
EXPOSE 8501

# Cấu hình các tham số chạy Streamlit tối ưu trên môi trường Production
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]