# Архитектура LLM-Ассистента

## Обзор

Система представляет собой многофункционального ассистента, который объединяет несколько источников информации:
- Документация (через RAG)
- База данных (через SQL Agent)
- Интернет (через Web Search)

## Компоненты системы

### 1. API Layer (FastAPI)

**Файл**: `app/main.py`

Предоставляет REST API endpoints:
- `POST /chat` - основной endpoint для диалога
- `POST /documents/upload` - загрузка документов
- `DELETE /documents/clear` - очистка базы знаний
- `GET /health` - проверка состояния системы

**Технологии**:
- FastAPI для асинхронного API
- Pydantic для валидации данных
- CORS middleware для кросс-доменных запросов

### 2. Assistant Agent (Router)

**Файл**: `app/services/agent.py`

Главный компонент, который:
1. Принимает запрос пользователя
2. Анализирует его с помощью LLM
3. Определяет, какие инструменты использовать
4. Координирует выполнение запросов к инструментам
5. Синтезирует финальный ответ

**Логика роутинга**:
```python
query → LLM analysis → {use_rag, use_sql, use_web_search}
                            ↓           ↓           ↓
                         RAG      SQL Agent   Web Search
                            ↓           ↓           ↓
                            └───────────┴───────────┘
                                      ↓
                            Final Response Generation
```

**Алгоритм**:
1. LLM анализирует запрос и возвращает JSON с решением
2. Параллельно выполняются запросы к выбранным инструментам
3. Результаты объединяются и передаются LLM для финального ответа

### 3. RAG Service

**Файл**: `app/services/rag.py`

Реализует Retrieval-Augmented Generation:

**Индексация**:
```
Document → Text Splitter → Chunks → Embeddings → FAISS Index
```

**Поиск**:
```
Query → Embedding → Vector Search → Top-K Documents → Context
```

**Технологии**:
- FAISS для векторного поиска
- HuggingFace Embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- LangChain для работы с документами
- RecursiveCharacterTextSplitter для разбиения текста

**Параметры**:
- Размер чанка: 1000 символов
- Перекрытие: 200 символов
- Top-K: 3-4 документа
- Score threshold: 0.5

### 4. SQL Agent

**Файл**: `app/services/sql_agent.py`

Преобразует естественный язык в SQL:

**Процесс**:
```
NL Query → LLM + Schema → SQL Query → Validation → Execution → Results
```

**Защита**:
- Блокировка опасных операций (DROP, DELETE, UPDATE, etc.)
- Только SELECT запросы
- Валидация перед выполнением

**База данных**:
- SQLite для простоты развертывания
- Таблицы: team_members, projects
- Асинхронный доступ через aiosqlite

### 5. Web Search Service

**Файл**: `app/services/web_search.py`

Поиск информации в интернете:

**Технологии**:
- DuckDuckGo Search API
- Асинхронное выполнение
- Форматирование результатов

**Ограничения**:
- Бесплатный API с ограничениями
- До 5 результатов по умолчанию

### 6. LLM Service

**Файл**: `app/services/llm.py`

Унифицированный интерфейс для LLM:

**Поддерживаемые провайдеры**:
- OpenAI API (gpt-3.5-turbo, gpt-4, etc.)
- Локальные модели через Ollama
- Любой OpenAI-совместимый API (vLLM, LocalAI, etc.)

**Функции**:
- `chat_completion()` - обычная генерация
- `generate_with_tools()` - с функциональными вызовами

## Поток данных

### Простой запрос (один инструмент):

```
User: "Сколько людей в команде ML?"
  ↓
Agent: analyzes → decides to use SQL
  ↓
SQL Agent: "SELECT COUNT(*) FROM team_members WHERE department='Machine Learning'"
  ↓
Database: returns 4
  ↓
LLM: generates natural response
  ↓
Response: "В команде Machine Learning работает 4 человека: Александр, Мария, Дмитрий и Елена."
```

### Сложный запрос (несколько инструментов):

```
User: "Кто работает с PyTorch и над какими проектами?"
  ↓
Agent: analyzes → decides to use SQL + RAG
  ↓
SQL Agent: finds team members with PyTorch skill
  ↓
RAG: searches for project documentation
  ↓
LLM: synthesizes answer from both sources
  ↓
Response: detailed answer with team info and project details
```

## Хранение данных

### 1. Векторная база (FAISS)
```
data/vector_store/
  └── index/
      ├── index.faiss  (векторный индекс)
      └── index.pkl    (метаданные документов)
```

### 2. Реляционная база (SQLite)
```
data/assistant.db
  ├── team_members (сотрудники)
  └── projects     (проекты)
```

### 3. История диалогов
- Хранится в памяти (in-memory)
- Последние 10 сообщений на conversation
- Требует доработки для production

## Масштабируемость

### Текущая реализация:
- Однопоточная обработка
- In-memory история
- Локальное хранилище

### Для production:
1. **Горизонтальное масштабирование**:
   - Kubernetes для оркестрации
   - Redis для кэширования
   - PostgreSQL вместо SQLite

2. **Очереди задач**:
   - Celery для асинхронной обработки
   - RabbitMQ/Redis как брокер

3. **Мониторинг**:
   - Prometheus для метрик
   - Grafana для визуализации
   - ELK stack для логов

## Безопасность

### Текущие меры:
1. SQL Injection защита - блокировка опасных команд
2. Валидация входных данных через Pydantic
3. Изоляция в Docker контейнерах

### Рекомендации для production:
1. Аутентификация и авторизация (JWT)
2. Rate limiting
3. Input sanitization
4. Guardrails для LLM ответов
5. Audit logging

## Производительность

### Типичное время ответа:

| Инструмент | Время |
|-----------|-------|
| RAG | 0.5-1.0s |
| SQL | 0.3-0.5s |
| Web Search | 1.5-3.0s |
| Комбинация | 2.0-4.0s |

### Оптимизации:
1. Параллельное выполнение инструментов
2. Кэширование embeddings
3. Пулы соединений к БД
4. Батчинг запросов к LLM

## Выбор технологий

### Почему FastAPI?
- Асинхронность из коробки
- Автоматическая документация API
- Pydantic валидация
- Высокая производительность

### Почему FAISS?
- Быстрый векторный поиск
- Не требует отдельного сервера
- Хорошо работает на CPU
- Поддержка от Facebook AI

### Почему SQLite?
- Не требует отдельного сервера
- Простое развертывание
- Достаточно для MVP
- Легко мигрировать на PostgreSQL

### Почему LangChain?
- Готовые абстракции для RAG
- Интеграция с многими векторными БД
- Text splitters и document loaders
- Активное сообщество

## Возможные улучшения

1. **Guardrails**: контроль качества ответов
2. **Deep Search**: многошаговый поиск
3. **Streaming**: потоковая генерация ответов
4. **Caching**: кэширование частых запросов
5. **Analytics**: метрики использования
6. **Multi-tenancy**: поддержка нескольких организаций
7. **Fine-tuning**: дообучение на специфичных данных

