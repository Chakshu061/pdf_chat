# from fastapi import FastAPI, UploadFile, Form
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# import tempfile
# import os

# # PDF processing + embeddings
# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceInstructEmbeddings
# from langchain_community.llms import HuggingFaceHub
# from langchain.chains import ConversationalRetrievalChain

# # ====== GLOBALS ======
# app = FastAPI()
# vectorstore = None
# chat_history = []


# # ========= STEP 1: Upload & Process PDF =========
# @app.post("/upload_pdf/")
# async def upload_pdf(file: UploadFile):
#     global vectorstore, chat_history

#     # Save uploaded PDF temporarily
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#         tmp_file.write(await file.read())
#         tmp_path = tmp_file.name

#     # Load PDF
#     loader = PyPDFLoader(tmp_path)
#     documents = loader.load()

#     # Chunk into smaller texts
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
#     docs = text_splitter.split_documents(documents)

#     # Embeddings
#     embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")

#     # Build FAISS vector store
#     vectorstore = FAISS.from_documents(docs, embeddings)

#     # Reset history
#     chat_history = []

#     # Clean up temp file
#     os.remove(tmp_path)

#     return {"status": "success", "message": f"{file.filename} uploaded & processed"}


# # ========= STEP 2: Chat with PDF =========
# @app.post("/chat_pdf/")
# async def chat_pdf(question: str = Form(...)):
#     global vectorstore, chat_history
#     if vectorstore is None:
#         return JSONResponse(status_code=400, content={"error": "Upload a PDF first!"})

#     # Connect LLM
#     llm = HuggingFaceHub(
#         repo_id="google/flan-t5-large",  # free but decent model
#         model_kwargs={"temperature": 0, "max_length": 512}
#     )

#     # Retrieval + conversation chain
#     qa_chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=vectorstore.as_retriever(),
#         return_source_documents=True
#     )

#     # Run query
#     result = qa_chain({"question": question, "chat_history": chat_history})
#     chat_history.append((question, result["answer"]))

#     return {"question": question, "answer": result["answer"]}


# # ========= STEP 3: Summarize PDF =========
# @app.post("/summarize/")
# async def summarize_pdf():
#     global vectorstore
#     if vectorstore is None:
#         return JSONResponse(status_code=400, content={"error": "Upload a PDF first!"})

#     # Grab all docs
#     docs = vectorstore.docstore._dict.values()
#     full_text = " ".join([doc.page_content for doc in docs])

#     llm = HuggingFaceHub(
#         repo_id="google/flan-t5-large",
#         model_kwargs={"temperature": 0, "max_length": 1024}
#     )

#     summary_prompt = f"Summarize this PDF content in detail:\n\n{full_text[:5000]}"
#     summary = llm(summary_prompt)

#     return {"summary": summary}


# # ========= STEP 4: Generate FAQs =========
# @app.post("/faq/")
# async def faq_pdf():
#     global vectorstore
#     if vectorstore is None:
#         return JSONResponse(status_code=400, content={"error": "Upload a PDF first!"})

#     docs = vectorstore.docstore._dict.values()
#     full_text = " ".join([doc.page_content for doc in docs])

#     llm = HuggingFaceHub(
#         repo_id="google/flan-t5-large",
#         model_kwargs={"temperature": 0, "max_length": 1024}
#     )

#     faq_prompt = f"Generate 5 FAQs with answers based only on this content:\n\n{full_text[:5000]}"
#     faq_text = llm(faq_prompt)

#     return {"faq": faq_text}


# # ========= STEP 5: Root route =========
# @app.get("/")
# async def root():
#     return {"message": "PDF Chat Backend is running 🚀"}
