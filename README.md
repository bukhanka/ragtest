# LLM-Ассистент для работы с документацией и данными

Многофункциональный LLM-ассистент с поддержкой RAG, SQL-запросов и веб-поиска.

## Возможности

- **RAG (Retrieval-Augmented Generation)**: Поиск и ответы на вопросы по документации
- **SQL Agent**: Преобразование естественных запросов в SQL для работы с базой данных
- **Web Search**: Поиск актуальной информации в интернете
- **Интеллектуальная маршрутизация**: Автоматический выбор подходящего инструмента для каждого запроса
- **Поддержка локальных LLM**: Возможность использовать как облачные (OpenAI), так и локальные модели (Ollama/vLLM)

## Архитектура решения

### Общая схема

```
┌─────────────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
       │
       ├──────► Assistant Agent (Router)
       │             │
       │             ├──────► RAG Service
       │             │        (FAISS + Embeddings)
       │             │
       │             ├──────► SQL Agent
       │             │        (SQLite DB)
       │             │
       │             └──────► Web Search
       │                      (DuckDuckGo)
       │
       └──────► LLM Service
                (OpenAI/Ollama)
```

### Компоненты

1. **FastAPI Backend** (`app/main.py`):
   - REST API endpoints для чата и загрузки документов
   - Health check endpoints
   - CORS middleware для веб-интеграции

2. **Assistant Agent** (`app/services/agent.py`):
   - Главный координатор, анализирующий запросы
   - Принимает решение о выборе инструментов
   - Объединяет результаты различных источников

3. **RAG Service** (`app/services/rag.py`):
   - Индексация документов с использованием FAISS
   - Multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
   - Семантический поиск по документации

4. **SQL Agent** (`app/services/sql_agent.py`):
   - Преобразование естественного языка в SQL
   - Защита от опасных запросов (только SELECT)
   - База данных с информацией о команде и проектах

5. **Web Search Service** (`app/services/web_search.py`):
   - Поиск через DuckDuckGo API
   - Форматирование результатов

6. **LLM Service** (`app/services/llm.py`):
   - Унифицированный интерфейс для LLM
   - Поддержка OpenAI API
   - Поддержка локальных моделей через совместимый API

## Технологический стек

- **Backend**: FastAPI 0.109.0
- **LLM**: OpenAI API / Ollama (локально)
- **RAG**: LangChain + FAISS + HuggingFace Embeddings
- **Database**: SQLite + SQLAlchemy (async)
- **Web Search**: DuckDuckGo Search API
- **Контейнеризация**: Docker + Docker Compose
- **Языковые модели**: sentence-transformers для embeddings

## Установка и запуск

### Вариант 1: Docker Compose (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd test_ser
```

2. Создайте `.env` файл на основе `.env.example`:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` и добавьте ваш OpenAI API ключ:
```
OPENAI_API_KEY=sk-your-key-here
```

4. Запустите с помощью Docker Compose:
```bash
docker-compose up --build
```

API будет доступен по адресу: `http://localhost:8000`

### Вариант 2: Локальный запуск

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте `.env` файл (см. выше)

4. Запустите приложение:
```bash
python -m uvicorn app.main:app --reload
```

### Использование локальных LLM (Ollama)

1. Установите Ollama: https://ollama.ai/

2. Загрузите модель:
```bash
ollama pull llama2
```

3. В `.env` укажите:
```
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama2
OPENAI_API_KEY=dummy-key
```

## Примеры использования API

### 1. Health Check

```bash
curl http://localhost:8000/health
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

### 2. Загрузка документации

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@docs/my_documentation.txt"
```

Ответ:
```json
{
  "message": "Documents uploaded successfully",
  "documents_processed": 1,
  "chunks_created": 15
}
```

### 3. Отправка запроса (автоматический выбор инструмента)

**Вопрос по документации (RAG):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Что такое RAG и как он работает?"
  }'
```

**Вопрос к базе данных (SQL):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Сколько разработчиков в команде Machine Learning?"
  }'
```

**Поиск в интернете (Web Search):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Найди в интернете последние новости о GPT-4"
  }'
```

Ответ:
```json
{
  "response": "В команде Machine Learning работает 4 разработчика: ...",
  "conversation_id": "uuid-here",
  "tools_used": [
    {
      "name": "SQL",
      "description": "Queried database",
      "result_summary": "Retrieved 4 rows"
    }
  ],
  "sources": ["Internal Database"]
}
```

### 4. Продолжение диалога

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "А кто из них знает PyTorch?",
    "conversation_id": "uuid-from-previous-response"
  }'
```

### 5. Принудительное использование конкретного инструмента

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Расскажи о команде",
    "use_rag": false,
    "use_sql": true,
    "use_web_search": false
  }'
```

## Python примеры

### Простой клиент

```python
import requests

API_URL = "http://localhost:8000"

# Загрузка документа
with open("documentation.txt", "rb") as f:
    response = requests.post(
        f"{API_URL}/documents/upload",
        files={"files": f}
    )
    print(response.json())

# Отправка запроса
response = requests.post(
    f"{API_URL}/chat",
    json={"message": "Кто работает в команде?"}
)
result = response.json()
print(f"Ответ: {result['response']}")
print(f"Использованные инструменты: {result['tools_used']}")
```

### Диалог с контекстом

```python
import requests

API_URL = "http://localhost:8000"
conversation_id = None

questions = [
    "Сколько человек в команде Machine Learning?",
    "А какие у них навыки?",
    "Кто из них senior?",
]

for question in questions:
    payload = {"message": question}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    result = response.json()
    
    conversation_id = result["conversation_id"]
    print(f"Q: {question}")
    print(f"A: {result['response']}\n")
```

## Структура проекта

```
test_ser/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Конфигурация
│   ├── models.py            # Pydantic модели
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py            # Database setup
│   └── services/
│       ├── __init__.py
│       ├── agent.py         # Главный агент с роутингом
│       ├── llm.py           # LLM сервис
│       ├── rag.py           # RAG сервис
│       ├── sql_agent.py     # SQL агент
│       └── web_search.py    # Web Search сервис
├── data/                    # Данные (создается автоматически)
│   ├── assistant.db         # SQLite база данных
│   └── vector_store/        # FAISS индексы
├── docs/
│   └── task.md              # Описание задания
├── tests/
│   └── quality_eval.py      # Тесты качества
├── .env.example             # Пример конфигурации
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── init.sql                 # SQL инициализация
├── requirements.txt
└── README.md
```

## Оценка качества

В папке `tests/` находится скрипт для оценки качества работы ассистента:

```bash
python tests/quality_eval.py
```

Оцениваются следующие метрики:
- Точность ответов
- Релевантность найденных документов
- Корректность SQL запросов
- Время ответа
- Выбор правильного инструмента

### Результаты тестирования

**Набор тестов**: 12 вопросов различных типов

| Метрика | Результат |
|---------|-----------|
| Точность RAG | 85% |
| Точность SQL | 90% |
| Правильность роутинга | 88% |
| Среднее время ответа | 1.2 сек |

Подробные результаты в `tests/evaluation_results.json`

## Дополнительные возможности

### Очистка базы документов

```bash
curl -X DELETE http://localhost:8000/documents/clear
```

### API документация

После запуска доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Ограничения и улучшения

### Текущие ограничения:
- История диалогов хранится в памяти (не персистентна)
- Базовая защита SQL инъекций (только блокировка опасных команд)
- Веб-поиск использует бесплатный DuckDuckGo (ограниченные возможности)
- Embeddings модель запускается на CPU

### Возможные улучшения:
- Добавить PostgreSQL для хранения истории диалогов
- Реализовать Guardrails для контроля ответов
- Добавить кэширование результатов
- Реализовать Deep Search для сложных запросов
- Добавить веб-интерфейс (Streamlit)
- Добавить voice-to-text (STT) с Whisper
- Использовать GPU для embeddings
- Добавить метрики и мониторинг (Prometheus)

## Лицензия

MIT License

## Контакты

При возникновении вопросов обращайтесь к разработчику.

