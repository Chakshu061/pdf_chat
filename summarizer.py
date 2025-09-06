from llm import query_llm
from parser import chunk_text

def summarize_pdf(text):
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    partial_summaries = []

    # Step 1: Summarize each chunk
    for chunk in chunks:
        prompt = f"""
        Summarize the following text clearly and concisely:

        {chunk}
        """
        summary = query_llm(prompt)
        partial_summaries.append(summary)

    # Step 2: Merge summaries
    combined_text = "\n".join(partial_summaries)
    final_prompt = f"""
    Combine these partial summaries into a single, concise summary:

    {combined_text}
    """
    return query_llm(final_prompt)
