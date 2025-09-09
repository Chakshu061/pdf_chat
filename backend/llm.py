import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def query_llm(prompt, model="llama3"):
    """Query Ollama via its persistent API server."""
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60  # prevents hanging forever
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"Error querying Ollama: {e}"