import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load your OpenAI key

# Cache models to avoid rebuilding every request
_vector_db = None
_embedding_model = None
_llm = None


def get_nphies_answer(query: str, language: str = "English"):
    """
    🔬 Multilingual Retrieval-Augmented Generation (RAG) pipeline.
    Handles both English and Arabic queries automatically.

    Steps:
        1. Load and index Nphies Q&A file (FAISS + embeddings)
        2. Encode the query (semantic embedding)
        3. Retrieve similar context
        4. Generate answer using OpenAI GPT model in selected language
    """

    global _vector_db, _embedding_model, _llm

    if not query or not query.strip():
        return "⚠️ Please enter a question." if language == "English" else "⚠️ الرجاء إدخال سؤال."

    file_path = "Nphies Q-A.txt"
    if not os.path.exists(file_path):
        return (
            "⚠️ Nphies Q&A file not found."
            if language == "English"
            else "⚠️ ملف الأسئلة Nphies Q-A.txt غير موجود."
        )

    # 1️⃣ Build once (cache)
    if _vector_db is None:
        print("📚 Loading and indexing Nphies Q&A knowledge base...")

        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(documents)

        # multilingual embedding model
        _embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        _vector_db = FAISS.from_documents(docs, _embedding_model)
        print(f"✅ Indexed {len(docs)} text chunks.")

        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    # 2️⃣ Convert query → embedding vector
    print("\n🔹 Generating embedding for query...")
    query_vector = _embedding_model.embed_query(query)

    # 3️⃣ Retrieve top similar text chunks
    print("\n🔹 Performing FAISS similarity search...")
    results = _vector_db.similarity_search_by_vector(query_vector, k=3)
    if not results:
        return (
            "❌ No relevant answer found in the Nphies database."
            if language == "English"
            else "❌ لم يتم العثور على إجابة مشابهة في قاعدة بيانات نفيس."
        )

    # Combine retrieved context
    context = "\n\n".join([r.page_content for r in results])

    # 4️⃣ Language-aware prompt
    if language == "Arabic":
        system_prompt = (
            "أنت مساعد ذكي متخصص في نظام نفيس (NPHIES). "
            "استخدم المعلومات التالية للإجابة على السؤال بدقة وباللغة العربية:\n\n"
        )
        user_prompt = f"{system_prompt}{context}\n\nالسؤال: {query}\nالإجابة:"
    else:
        system_prompt = (
            "You are an intelligent assistant specialized in the NPHIES system. "
            "Use the following context to answer the question clearly and in English:\n\n"
        )
        user_prompt = f"{system_prompt}{context}\n\nQuestion: {query}\nAnswer:"

    # 5️⃣ Generate reasoning-based answer
    print("\n🔹 Sending to GPT reasoning model...")
    response = _llm.invoke(user_prompt)
    return response.content.strip()
