# Примеры API запросов

## Базовые запросы

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_available": true,
  "vector_store_available": true,
  "database_available": true
}
```

### Корневой endpoint

```bash
curl -X GET http://localhost:8000/
```

## Работа с документами

### Загрузка документа

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@document.txt"
```

### Загрузка нескольких документов

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@doc1.txt" \
  -F "files=@doc2.txt" \
  -F "files=@doc3.txt"
```

### Очистка базы документов

```bash
curl -X DELETE http://localhost:8000/documents/clear
```

## Запросы к ассистенту

### Простой вопрос

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет! Расскажи о себе"
  }'
```

### Вопрос с использованием RAG

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Что такое RAG и как он работает?"
  }'
```

Ответ:
```json
{
  "response": "RAG (Retrieval-Augmented Generation) - это архитектурный подход...",
  "conversation_id": "abc-123-def-456",
  "tools_used": [
    {
      "name": "RAG",
      "description": "Retrieved information from documentation",
      "result_summary": "Found 3 relevant documents"
    }
  ],
  "sources": ["test_sample_docs.txt"]
}
```

### SQL запрос (информация о команде)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Сколько человек работает в команде Machine Learning?"
  }'
```

### Веб-поиск

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Найди в интернете последние новости о ChatGPT"
  }'
```

### Продолжение диалога

```bash
# Первый запрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Кто работает Senior ML Engineer?"
  }'

# Сохраните conversation_id из ответа и используйте в следующем запросе
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "А какие у него навыки?",
    "conversation_id": "abc-123-def-456"
  }'
```

### Отключение определенных инструментов

```bash
# Только SQL, без RAG и Web Search
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Покажи информацию о команде",
    "use_rag": false,
    "use_sql": true,
    "use_web_search": false
  }'
```

## Примеры запросов для разных сценариев

### RAG: Вопросы по документации

```bash
# Концептуальный вопрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Объясни, что такое embeddings"}'

# Технический вопрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Как работают векторные базы данных?"}'

# Вопрос о применении
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Где применяется RAG?"}'
```

### SQL: Запросы к базе данных

```bash
# Подсчет
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Сколько сотрудников в отделе Engineering?"}'

# Фильтрация
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Покажи всех, кто знает Docker"}'

# Поиск по атрибутам
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Кто присоединился к команде в 2021 году?"}'

# Информация о проектах
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Какие проекты находятся в статусе active?"}'

# Сложный запрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "У кого в команде есть навыки NLP или LangChain?"}'
```

### Web Search: Поиск в интернете

```bash
# Прямой запрос на поиск
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Найди в интернете информацию о GPT-4"}'

# Актуальные новости
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Поищи последние новости об искусственном интеллекте"}'

# Технические вопросы
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Найди информацию о последней версии LangChain"}'
```

### Многоинструментальные запросы

```bash
# Может использовать SQL + RAG
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Расскажи о команде и о технологиях, которые они используют"}'

# Может использовать RAG + Web Search
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое RAG и какие есть новости об этой технологии?"}'
```

## Python примеры

### Базовый клиент

```python
import requests
import json

API_URL = "http://localhost:8000"

def ask_question(question: str):
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": question}
    )
    result = response.json()
    print(f"Q: {question}")
    print(f"A: {result['response']}")
    print(f"Tools: {[t['name'] for t in result['tools_used']]}")
    print()
    return result

# Примеры использования
ask_question("Что такое RAG?")
ask_question("Сколько людей в команде ML?")
ask_question("Найди информацию о LangChain")
```

### Диалог с контекстом

```python
import requests

API_URL = "http://localhost:8000"

class AssistantClient:
    def __init__(self):
        self.conversation_id = None
    
    def ask(self, question: str):
        payload = {"message": question}
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        
        response = requests.post(f"{API_URL}/chat", json=payload)
        result = response.json()
        
        self.conversation_id = result["conversation_id"]
        return result["response"]
    
    def reset(self):
        self.conversation_id = None

# Использование
client = AssistantClient()
print(client.ask("Кто работает Senior ML Engineer?"))
print(client.ask("Какие у него навыки?"))
print(client.ask("Когда он присоединился к команде?"))
```

### Загрузка документов

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def upload_document(filepath: str):
    with open(filepath, 'rb') as f:
        response = requests.post(
            f"{API_URL}/documents/upload",
            files={"files": f}
        )
    return response.json()

# Загрузить один файл
result = upload_document("documentation.txt")
print(f"Uploaded: {result['documents_processed']} docs, "
      f"{result['chunks_created']} chunks")

# Загрузить все txt файлы из папки
docs_dir = Path("docs")
for doc_file in docs_dir.glob("*.txt"):
    result = upload_document(str(doc_file))
    print(f"Uploaded {doc_file.name}")
```

### Асинхронный клиент

```python
import asyncio
import aiohttp

API_URL = "http://localhost:8000"

async def ask_async(question: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/chat",
            json={"message": question}
        ) as response:
            return await response.json()

async def main():
    questions = [
        "Что такое RAG?",
        "Сколько людей в команде?",
        "Какие проекты активны?"
    ]
    
    tasks = [ask_async(q) for q in questions]
    results = await asyncio.gather(*tasks)
    
    for q, r in zip(questions, results):
        print(f"Q: {q}")
        print(f"A: {r['response'][:100]}...")
        print()

asyncio.run(main())
```

## JavaScript примеры

### Fetch API

```javascript
const API_URL = 'http://localhost:8000';

async function askQuestion(question) {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: question })
    });
    
    const result = await response.json();
    console.log('Q:', question);
    console.log('A:', result.response);
    console.log('Tools:', result.tools_used.map(t => t.name));
    
    return result;
}

// Использование
askQuestion('Что такое RAG?');
```

### Axios

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';

class AssistantClient {
    constructor() {
        this.conversationId = null;
    }
    
    async ask(question) {
        const payload = { message: question };
        if (this.conversationId) {
            payload.conversation_id = this.conversationId;
        }
        
        const response = await axios.post(`${API_URL}/chat`, payload);
        this.conversationId = response.data.conversation_id;
        
        return response.data.response;
    }
    
    reset() {
        this.conversationId = null;
    }
}

// Использование
const client = new AssistantClient();
client.ask('Кто работает в команде ML?')
    .then(response => console.log(response));
```

## Тестирование

### Health check

```bash
#!/bin/bash
response=$(curl -s http://localhost:8000/health)
status=$(echo $response | jq -r '.status')

if [ "$status" == "healthy" ]; then
    echo "✓ Service is healthy"
    exit 0
else
    echo "✗ Service is unhealthy"
    exit 1
fi
```

### Smoke test

```bash
#!/bin/bash

echo "Testing API endpoints..."

# Test health
echo "1. Health check..."
curl -s http://localhost:8000/health | jq .

# Test chat
echo "2. Chat test..."
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' | jq .

echo "✓ All tests passed"
```

## Ограничения и рекомендации

1. **Timeout**: Для сложных запросов увеличьте timeout до 60 секунд
2. **Rate limiting**: В production добавьте ограничение частоты запросов
3. **Размер документов**: Рекомендуемый максимум - 10MB на файл
4. **Длина сообщений**: Максимум ~4000 токенов для контекста
5. **История диалогов**: Хранятся последние 10 сообщений

## Troubleshooting

### Ошибка 503 (Service Unavailable)

```bash
# Проверить статус сервиса
curl http://localhost:8000/health

# Проверить логи
docker-compose logs app
```

### Ошибка 500 (Internal Server Error)

```bash
# Проверить подробные логи
docker-compose logs -f app

# Проверить .env конфигурацию
cat .env
```

### Медленные ответы

- Используйте локальные LLM модели
- Уменьшите количество результатов RAG (k=2 вместо 4)
- Отключите неиспользуемые инструменты

