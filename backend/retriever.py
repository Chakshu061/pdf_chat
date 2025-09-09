from embedder import OptimizedEmbedder
from llm import query_llm

def generate_answer(question: str, retriever: OptimizedEmbedder, max_context_length: int = 2000) -> str:
    """Generate answer using retrieved context."""
    
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