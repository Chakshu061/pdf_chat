# app.py - Minimal working version with performance improvements
from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import asyncio
import uuid
from typing import Dict, Any

# Import your existing modules
from parser import parse_pdf, smart_chunk_text
from embedder import OptimizedEmbedder  
from llm import query_llm

# ====== GLOBALS ======
app = FastAPI(title="AI PDF Processor", description="Process large PDFs with AI")

# Add CORS for web deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
pdf_sessions: Dict[str, Dict[str, Any]] = {}

class ProcessingStatus:
    UPLOADING = "uploading"
    PARSING = "parsing" 
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"

# ========= Helper Functions =========
def summarize_chunks_batch(chunks, batch_size=5):
    """Summarize chunks in batches for better performance"""
    summaries = []
    
    # Process in batches
    for i in range(0, min(len(chunks), 20), batch_size):  # Limit to first 20 chunks
        batch_chunks = chunks[i:i + batch_size]
        batch_text = "\n\n".join(batch_chunks)
        
        prompt = f"Summarize this section concisely, focusing on main points:\n\n{batch_text[:2000]}"
        summary = query_llm(prompt, model="llama3")
        summaries.append(summary)
    
    return summaries

def create_final_summary(chunk_summaries):
    """Create final summary from chunk summaries"""
    combined_summaries = "\n\n".join(chunk_summaries)
    
    prompt = f"Create a comprehensive summary from these section summaries:\n\n{combined_summaries}"
    return query_llm(prompt, model="llama3")

def generate_faqs_from_chunks(chunks, num_questions=5):
    """Generate FAQs from document chunks"""
    content = "\n\n".join(chunks[:3])[:2000]  # Use first 3 chunks
    
    prompt = f"""Based on this content, generate {num_questions} frequently asked questions with detailed answers:

{content}

Format as:
Q1: [Question]
A1: [Answer]

Q2: [Question] 
A2: [Answer]

etc."""
    
    return query_llm(prompt, model="llama3")

def generate_answer_from_context(question, retriever, max_context_length=2000):
    """Generate answer using retrieved context"""
    # Get relevant chunks
    relevant_chunks = retriever.query(question, top_k=5)
    
    if not relevant_chunks:
        return "I couldn't find relevant information in the document to answer your question."
    
    # Combine chunks, respecting max context length
    context = ""
    for chunk in relevant_chunks:
        if len(context) + len(chunk) <= max_context_length:
            context += chunk + "\n\n"
        else:
            break
    
    prompt = f"""Based on the following context from the document, answer the user's question accurately. If the answer is not in the context, say so.

Context:
{context}

Question: {question}

Answer:"""
    
    return query_llm(prompt, model="llama3")

# ========= STEP 1: Upload & Process PDF (Async) =========
@app.post("/upload_pdf/")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile):
    """Upload and process PDF asynchronously"""
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Initialize session
    pdf_sessions[session_id] = {
        "status": ProcessingStatus.UPLOADING,
        "filename": file.filename,
        "progress": 0,
        "retriever": None,
        "chunks": None,
        "error": None
    }
    
    # Save uploaded PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    # Process in background
    background_tasks.add_task(process_pdf_background, session_id, tmp_path, file.filename)
    
    return {
        "session_id": session_id,
        "status": "processing_started",
        "message": f"Processing {file.filename}..."
    }

async def process_pdf_background(session_id: str, tmp_path: str, filename: str):
    """Background task to process PDF"""
    try:
        session = pdf_sessions[session_id]
        
        # Step 1: Parse PDF
        session["status"] = ProcessingStatus.PARSING
        session["progress"] = 20
        pdf_text = parse_pdf(tmp_path)
        
        if len(pdf_text) < 100:
            raise Exception("PDF appears to be empty or corrupted")
        
        # Step 2: Smart chunking
        session["status"] = ProcessingStatus.CHUNKING  
        session["progress"] = 40
        chunks = smart_chunk_text(pdf_text, chunk_size=1200, overlap=200)
        
        # Step 3: Build index
        session["status"] = ProcessingStatus.INDEXING
        session["progress"] = 70
        retriever = OptimizedEmbedder()
        await asyncio.to_thread(retriever.build_index, chunks)
        
        # Step 4: Complete
        session.update({
            "status": ProcessingStatus.READY,
            "progress": 100,
            "retriever": retriever,
            "chunks": chunks,
            "chunks_count": len(chunks),
            "text_length": len(pdf_text)
        })
        
    except Exception as e:
        pdf_sessions[session_id].update({
            "status": ProcessingStatus.ERROR,
            "error": str(e)
        })
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ========= Check Processing Status =========
@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Check processing status"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "progress": session["progress"],
        "filename": session.get("filename"),
        "chunks_count": session.get("chunks_count", 0),
        "error": session.get("error")
    }

# ========= STEP 2: Chat with PDF =========
@app.post("/chat/{session_id}")
async def chat_pdf(session_id: str, question: str = Form(...)):
    """Chat with processed PDF"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    if session["status"] != ProcessingStatus.READY:
        return JSONResponse(status_code=400, content={
            "error": f"PDF not ready. Status: {session['status']}"
        })

    try:
        retriever = session["retriever"]
        answer = await asyncio.to_thread(generate_answer_from_context, question, retriever)
        
        return {"question": question, "answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ========= STEP 3: Summarize PDF =========
@app.post("/summarize/{session_id}")
async def summarize_pdf_endpoint(session_id: str):
    """Generate hierarchical summary"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    if session["status"] != ProcessingStatus.READY:
        return JSONResponse(status_code=400, content={
            "error": f"PDF not ready. Status: {session['status']}"
        })

    try:
        chunks = session["chunks"]
        
        # Generate summary using hierarchical approach
        chunk_summaries = await asyncio.to_thread(summarize_chunks_batch, chunks)
        final_summary = await asyncio.to_thread(create_final_summary, chunk_summaries)
        
        return {
            "summary": final_summary,
            "word_count": len(final_summary.split()),
            "sections_processed": len(chunk_summaries)
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ========= STEP 4: Generate FAQs =========
@app.post("/faq/{session_id}")
async def faq_pdf(session_id: str, num_questions: int = Form(5)):
    """Generate FAQs from PDF content"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    if session["status"] != ProcessingStatus.READY:
        return JSONResponse(status_code=400, content={
            "error": f"PDF not ready. Status: {session['status']}"
        })

    try:
        chunks = session["chunks"]
        faq_text = await asyncio.to_thread(
            generate_faqs_from_chunks, 
            chunks, 
            min(num_questions, 5)
        )
        
        return {"faq": faq_text}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ========= Health Check =========
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Quick test of Ollama connection
        test_response = query_llm("Hello", model="llama3")
        ollama_status = "healthy" if "Error" not in test_response else "unhealthy"
    except:
        ollama_status = "unhealthy"
    
    return {
        "status": "healthy",
        "ollama": ollama_status,
        "active_sessions": len(pdf_sessions)
    }

# ========= Document Statistics =========
@app.get("/stats/{session_id}")
async def get_document_stats(session_id: str):
    """Get comprehensive document statistics"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    if session["status"] != ProcessingStatus.READY:
        return JSONResponse(status_code=400, content={
            "error": f"PDF not ready. Status: {session['status']}"
        })

    chunks = session.get("chunks", [])
    text_length = session.get("text_length", 0)
    
    # Calculate statistics
    avg_chunk_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
    total_words = sum(len(chunk.split()) for chunk in chunks)
    
    return {
        "filename": session.get("filename"),
        "total_text_length": text_length,
        "total_chunks": len(chunks),
        "total_words": total_words,
        "average_chunk_size": int(avg_chunk_size),
        "estimated_pages": len(chunks) // 3,  # Rough estimate
        "processing_coverage": "Full document" if len(chunks) > 20 else f"First {len(chunks)} chunks only"
    }
@app.get("/debug/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to see session details"""
    if session_id not in pdf_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = pdf_sessions[session_id]
    debug_info = {
        "session_id": session_id,
        "status": session["status"],
        "progress": session["progress"],
        "filename": session.get("filename"),
        "error": session.get("error"),
        "has_retriever": session.get("retriever") is not None,
        "has_chunks": session.get("chunks") is not None,
        "chunks_count": len(session["chunks"]) if session.get("chunks") else 0,
        "text_length": session.get("text_length", 0)
    }
    
    # If there are chunks, show first chunk preview
    if session.get("chunks"):
        debug_info["first_chunk_preview"] = session["chunks"][0][:200] + "..." if len(session["chunks"][0]) > 200 else session["chunks"][0]
    
    return debug_info

# ========= Root route =========
@app.get("/")
async def root():
    return {
        "message": "🚀 AI PDF Processor - Ready for large documents!",
        "features": [
            "📄 Large PDF processing (500+ pages)",
            "🤖 Hierarchical AI summarization", 
            "💬 Intelligent chat with documents",
            "❓ Auto-generated FAQs",
            "⚡ Optimized for performance"
        ],
        "endpoints": {
            "upload": "/upload_pdf/",
            "status": "/status/{session_id}",
            "chat": "/chat/{session_id}", 
            "summarize": "/summarize/{session_id}",
            "faq": "/faq/{session_id}"
        }
    }

# ========= Session Management =========
@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up session data"""
    if session_id in pdf_sessions:
        del pdf_sessions[session_id]
        return {"message": "Session deleted"}
    return JSONResponse(status_code=404, content={"error": "Session not found"})

@app.get("/sessions")
async def list_sessions():
    """List all active sessions (for debugging)"""
    return {
        "active_sessions": len(pdf_sessions),
        "sessions": {
            sid: {
                "status": session["status"],
                "filename": session.get("filename"),
                "progress": session["progress"]
            }
            for sid, session in pdf_sessions.items()
        }
    }