"""Example client for the LLM Assistant API."""
import requests
import json

API_URL = "http://localhost:8000"


def check_health():
    """Check API health."""
    response = requests.get(f"{API_URL}/health")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    print()


def upload_document(filepath: str):
    """Upload a document to the RAG knowledge base."""
    with open(filepath, "rb") as f:
        response = requests.post(
            f"{API_URL}/documents/upload",
            files={"files": f}
        )
    print(f"Document Upload ({filepath}):")
    print(json.dumps(response.json(), indent=2))
    print()


def ask_question(question: str, conversation_id=None):
    """Ask a question to the assistant."""
    payload = {"message": question}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    response = requests.post(
        f"{API_URL}/chat",
        json=payload
    )
    result = response.json()
    
    print(f"Q: {question}")
    print(f"A: {result['response']}")
    print(f"Tools used: {', '.join([t['name'] for t in result['tools_used']])}")
    if result['sources']:
        print(f"Sources: {', '.join(result['sources'][:3])}")
    print()
    
    return result['conversation_id']


def main():
    """Run example scenarios."""
    print("=" * 80)
    print("LLM ASSISTANT - EXAMPLE CLIENT")
    print("=" * 80)
    print()
    
    # 1. Check health
    check_health()
    
    # 2. Upload sample documentation
    print("Uploading sample documentation...")
    try:
        upload_document("tests/test_sample_docs.txt")
    except Exception as e:
        print(f"Note: Could not upload document: {e}")
        print("Continuing with existing knowledge base...\n")
    
    # 3. Example: RAG question
    print("Example 1: Documentation Question (RAG)")
    print("-" * 80)
    ask_question("Что такое RAG и как он работает?")
    
    # 4. Example: SQL question
    print("Example 2: Database Query (SQL)")
    print("-" * 80)
    ask_question("Сколько человек работает в команде Machine Learning?")
    
    # 5. Example: Another SQL question
    print("Example 3: Team Information (SQL)")
    print("-" * 80)
    ask_question("Покажи всех сотрудников, которые знают Python")
    
    # 6. Example: Web search
    print("Example 4: Web Search")
    print("-" * 80)
    ask_question("Найди в интернете последние новости о GPT-4")
    
    # 7. Example: Conversation with context
    print("Example 5: Multi-turn Conversation")
    print("-" * 80)
    conv_id = ask_question("Кто занимает должность Senior ML Engineer?")
    ask_question("А какие у него навыки?", conversation_id=conv_id)
    ask_question("Когда он присоединился к команде?", conversation_id=conv_id)
    
    # 8. Example: Mixed query
    print("Example 6: Complex Query")
    print("-" * 80)
    ask_question("У кого в команде есть опыт работы с FastAPI?")
    
    print("=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

