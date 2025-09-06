from llm import query_llm
from summarizer import summarize_pdf

def generate_answer(question, retriever, full_text):
    context_chunks = retriever.query(question)
    context = "\n".join(context_chunks)

    if not context.strip():
        # Fallback: summarize instead of "I don't know"
        return summarize_pdf(full_text)

    prompt = f"""
    You are a helpful assistant. Answer the question based strictly on the provided context.
    If the answer is not in the context, summarize the PDF instead.

    Context:
    {context}

    Question: {question}
    Answer:
    """
    return query_llm(prompt)
