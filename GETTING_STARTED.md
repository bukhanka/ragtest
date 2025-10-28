# Пошаговое руководство по запуску

## Шаг 1: Предварительные требования

Убедитесь, что у вас установлено:

- ✅ **Docker** (версия 20.10+)
- ✅ **Docker Compose** (версия 2.0+)
- ✅ **Git**

Проверка:
```bash
docker --version
docker-compose --version
git --version
```

## Шаг 2: Получение кода

```bash
git clone <repository-url>
cd test_ser
```

## Шаг 3: Конфигурация

### Вариант A: Использование OpenAI API (рекомендуется для начала)

1. Получите API ключ на https://platform.openai.com/api-keys

2. Создайте `.env` файл:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` и добавьте ваш ключ:
```bash
nano .env  # или любой другой редактор
```

Замените:
```
OPENAI_API_KEY=your_openai_api_key_here
```

На:
```
OPENAI_API_KEY=sk-ваш-реальный-ключ
```

### Вариант B: Использование локальной LLM (Ollama)

1. Установите Ollama:
```bash
# Linux
curl https://ollama.ai/install.sh | sh

# Mac
brew install ollama

# Windows - скачайте с https://ollama.ai/
```

2. Запустите Ollama:
```bash
ollama serve
```

3. Скачайте модель (в новом терминале):
```bash
ollama pull llama2
# или для русского языка:
ollama pull saiga
```

4. Используйте специальную конфигурацию:
```bash
cp .env.local_llm .env
```

## Шаг 4: Запуск

### Автоматический запуск (Linux/Mac)

```bash
./start.sh
```

Скрипт автоматически:
- Проверит наличие .env
- Создаст необходимые директории
- Соберет Docker образы
- Запустит сервисы
- Проверит доступность API

### Ручной запуск

```bash
# Создать директории
mkdir -p data data/vector_store

# Собрать образы
docker-compose build

# Запустить
docker-compose up -d

# Проверить статус
docker-compose ps
```

## Шаг 5: Проверка работы

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_available": true,
  "vector_store_available": true,
  "database_available": true
}
```

### 2. Проверка логов

```bash
docker-compose logs -f app
```

Должны увидеть:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. Открыть документацию

Откройте в браузере: http://localhost:8000/docs

Должен открыться Swagger UI с интерактивной документацией API.

## Шаг 6: Первый запрос

### Способ 1: Через curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет! Кто ты?"}'
```

### Способ 2: Через Swagger UI

1. Откройте http://localhost:8000/docs
2. Найдите endpoint `POST /chat`
3. Нажмите "Try it out"
4. Введите сообщение:
```json
{
  "message": "Привет! Расскажи о своих возможностях"
}
```
5. Нажмите "Execute"

### Способ 3: Через Python

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "Привет! Что ты умеешь?"}
)

result = response.json()
print("Ответ:", result["response"])
print("Инструменты:", [t["name"] for t in result["tools_used"]])
```

## Шаг 7: Загрузка документации

### Загрузить тестовые документы

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@tests/test_sample_docs.txt"
```

Ответ:
```json
{
  "message": "Documents uploaded successfully",
  "documents_processed": 1,
  "chunks_created": 15
}
```

### Загрузить свои документы

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@path/to/your/document.txt"
```

## Шаг 8: Тестирование возможностей

### RAG - Вопросы по документации

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое RAG и как он работает?"}'
```

### SQL - Запросы к базе данных

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Сколько человек работает в команде Machine Learning?"}'
```

### Web Search - Поиск в интернете

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Найди в интернете информацию о последних обновлениях ChatGPT"}'
```

## Шаг 9: Запуск тестов качества

```bash
# Подождите 5-10 секунд после запуска для инициализации
sleep 10

# Запустите тесты
python tests/quality_eval.py
```

Тесты проверят:
- ✅ Работу RAG системы
- ✅ Работу SQL агента
- ✅ Работу Web Search
- ✅ Правильность роутинга запросов
- ✅ Время ответа

Результаты будут сохранены в `tests/evaluation_results.json`

## Шаг 10: Использование Python клиента

Запустите пример:

```bash
python examples/example_client.py
```

Этот скрипт демонстрирует:
- Проверку здоровья системы
- Загрузку документов
- Различные типы запросов
- Работу с контекстом диалога

## Остановка системы

```bash
# Быстрый способ
./stop.sh

# Или вручную
docker-compose down

# Остановка и удаление данных
docker-compose down -v
```

## Просмотр логов

```bash
# Все логи
docker-compose logs

# Только приложение
docker-compose logs app

# В реальном времени
docker-compose logs -f app

# Последние 100 строк
docker-compose logs --tail=100 app
```

## Распространенные проблемы и решения

### Проблема 1: Port 8000 уже используется

```bash
# Найти процесс
sudo lsof -i :8000

# Остановить процесс или изменить порт в docker-compose.yml
ports:
  - "8001:8000"  # изменить на другой порт
```

### Проблема 2: Ошибка подключения к OpenAI

```bash
# Проверьте API ключ
cat .env | grep OPENAI_API_KEY

# Проверьте логи
docker-compose logs app | grep -i "error\|openai"

# Используйте локальную LLM вместо OpenAI
cp .env.local_llm .env
docker-compose restart
```

### Проблема 3: Out of memory

```bash
# Проверьте доступную память
free -h

# Увеличьте лимиты Docker или используйте меньшую модель
# Для Ollama используйте llama2:7b вместо llama2:13b
ollama pull llama2:7b
```

### Проблема 4: Медленная работа

```bash
# 1. Используйте локальную LLM
cp .env.local_llm .env

# 2. Уменьшите количество результатов RAG
# В app/services/rag.py измените k=3 на k=2

# 3. Проверьте нагрузку на CPU
top

# 4. Проверьте логи на наличие ошибок
docker-compose logs app | grep -i error
```

### Проблема 5: Векторная база не работает

```bash
# Очистите и пересоздайте индекс
curl -X DELETE http://localhost:8000/documents/clear

# Загрузите документы заново
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@tests/test_sample_docs.txt"
```

## Следующие шаги

1. ✅ **Изучите документацию**:
   - [README.md](README.md) - Основная документация
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архитектура
   - [API_EXAMPLES.md](docs/API_EXAMPLES.md) - Примеры API

2. ✅ **Загрузите свою документацию**:
   ```bash
   curl -X POST http://localhost:8000/documents/upload \
     -F "files=@your_docs.txt"
   ```

3. ✅ **Интегрируйте в свое приложение**:
   - Используйте Python/JavaScript примеры
   - Изучите API через Swagger UI

4. ✅ **Настройте под свои нужды**:
   - Измените модель LLM в `.env`
   - Добавьте свои данные в SQL базу
   - Настройте параметры RAG

5. ✅ **Для production**:
   - Изучите [DEPLOYMENT.md](docs/DEPLOYMENT.md)
   - Настройте PostgreSQL
   - Добавьте аутентификацию
   - Настройте мониторинг

## Полезные команды

```bash
# Перезапуск после изменений
docker-compose restart

# Пересборка после изменений в коде
docker-compose up -d --build

# Просмотр использования ресурсов
docker stats

# Полная очистка (удалит все данные!)
docker-compose down -v
docker system prune -a

# Бэкап базы данных
cp data/assistant.db data/backup_$(date +%Y%m%d).db

# Экспорт переменных окружения
set -a; source .env; set +a
```

## Получение помощи

- 📖 **Документация**: См. папку `docs/`
- 🐛 **Баги**: Создайте issue
- 💡 **Вопросы**: Создайте issue с тегом `question`
- 💬 **Обсуждения**: GitHub Discussions

## Готово! 🎉

Теперь у вас работает полнофункциональный LLM-ассистент с RAG, SQL и Web Search!

Экспериментируйте с различными запросами и изучайте возможности системы.

