from langchain_ollama import OllamaLLM

llm_view = OllamaLLM(model="llama3.1:8b", temperature=0.5)

def ask_llm(question):
    try:
        return llm_view.invoke(question)

    except Exception as e:
        return f"Ошибка {e}"

print(ask_llm("Привет"))