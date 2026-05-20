import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# Đã cập nhật thư viện mới theo khuyến nghị của LangChain
from langchain_huggingface import HuggingFaceEmbeddings

def build_vector_db():
    print("1. Đang đọc dữ liệu từ thư mục 'data/'...")
    
    # SỬA LỖI Ở ĐÂY: Ép dùng TextLoader và bảng mã utf-8 để đọc tiếng Việt chuẩn xác
    loader = DirectoryLoader(
        './data', 
        glob="**/*.txt", 
        loader_cls=TextLoader, 
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()
    
    if not documents:
        print("Lỗi: Không tìm thấy file .txt nào trong thư mục 'data/'!")
        return

    print(f"2. Đã tìm thấy {len(documents)} tài liệu. Đang phân mảnh...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    if not docs:
        print("Lỗi: Đã đọc được file nhưng không có chữ bên trong. Hãy kiểm tra lại file txt.")
        return

    print("3. Đang nhúng dữ liệu (Embedding)...")
    # Đã cập nhật class HuggingFaceEmbeddings từ langchain_huggingface
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("4. Đang tạo Vector Database và lưu xuống ổ cứng...")
    db = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
    
    print("===============")
    print("HOÀN TẤT! Đã xây dựng xong Ngân hàng đề thi RAG.")

if __name__ == "__main__":
    build_vector_db()