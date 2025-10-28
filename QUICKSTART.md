# Быстрый старт

## За 5 минут

### 1. Клонируйте репозиторий

```bash
git clone <repository-url>
cd test_ser
```

### 2. Настройте .env

```bash
cp .env.example .env
nano .env  # или используйте любой редактор
```

Добавьте ваш OpenAI API ключ:
```
OPENAI_API_KEY=sk-ваш-ключ-здесь
```

### 3. Запустите

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows/вручную:**
```bash
docker-compose up -d
```

### 4. Проверьте

```bash
curl http://localhost:8000/health
```

### 5. Загрузите тестовые данные

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@tests/test_sample_docs.txt"
```

### 6. Задайте первый вопрос

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое RAG?"}'
```

## Готово! 🎉

Теперь вы можете:

- Открыть документацию: http://localhost:8000/docs
- Использовать API: http://localhost:8000/chat
- Просмотреть логи: `docker-compose logs -f`
- Запустить тесты: `python tests/quality_eval.py`
- Попробовать примеры: `python examples/example_client.py`

## Что дальше?

1. **Загрузите свою документацию**:
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@your_documentation.txt"
```

2. **Попробуйте разные типы запросов**:
```bash
# RAG - вопросы по документации
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Объясни концепцию embeddings"}'

# SQL - вопросы к базе данных
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Сколько человек в команде ML?"}'

# Web Search - поиск в интернете
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Найди информацию о GPT-4"}'
```

3. **Используйте Python клиент**:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "Привет!"}
)
print(response.json()["response"])
```

## Использование локальных моделей (опционально)

Если хотите использовать локальные LLM вместо OpenAI:

1. **Установите Ollama**:
```bash
curl https://ollama.ai/install.sh | sh
```

2. **Скачайте модель**:
```bash
ollama pull llama2
```

3. **Обновите .env**:
```
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama2
OPENAI_API_KEY=dummy-key
```

4. **Перезапустите**:
```bash
docker-compose restart
```

## Остановка

```bash
docker-compose down
```

## Troubleshooting

**Проблема**: API не отвечает

**Решение**: Проверьте логи
```bash
docker-compose logs app
```

**Проблема**: Ошибка подключения к OpenAI

**Решение**: Проверьте API ключ в .env
```bash
cat .env | grep OPENAI_API_KEY
```

**Проблема**: Нет места на диске

**Решение**: Очистите Docker
```bash
docker system prune -a
```

## Дополнительные ресурсы

- [README.md](README.md) - Полная документация
- [API_EXAMPLES.md](docs/API_EXAMPLES.md) - Примеры API
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архитектура системы
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Развертывание
- [/docs](http://localhost:8000/docs) - Swagger UI (после запуска)

