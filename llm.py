import subprocess

def query_llm(prompt, model="llama3"):
    """Run a query against Ollama locally."""
    process = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE
    )
    return process.stdout.decode("utf-8")
