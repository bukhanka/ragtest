# Руководство по развертыванию

## Быстрый старт с Docker

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd test_ser

# 2. Создать .env файл
cp .env.example .env

# 3. Добавить API ключ в .env
echo "OPENAI_API_KEY=your-key-here" >> .env

# 4. Запустить
docker-compose up -d

# 5. Проверить статус
curl http://localhost:8000/health

# 6. Загрузить тестовую документацию
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@tests/test_sample_docs.txt"

# 7. Задать вопрос
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое RAG?"}'
```

## Локальное развертывание

### Требования
- Python 3.11+
- pip или poetry
- 4GB RAM минимум
- 10GB свободного места

### Шаги

1. **Создать виртуальное окружение**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Установить зависимости**:
```bash
pip install -r requirements.txt
```

3. **Настроить .env**:
```bash
cp .env.example .env
# Отредактировать .env и добавить OPENAI_API_KEY
```

4. **Запустить**:
```bash
python -m uvicorn app.main:app --reload
```

5. **Проверить**:
```bash
curl http://localhost:8000/health
```

## Использование локальных LLM (Ollama)

### Установка Ollama

**Linux**:
```bash
curl https://ollama.ai/install.sh | sh
```

**Mac**:
```bash
brew install ollama
```

**Windows**: Скачать с https://ollama.ai/

### Настройка

1. **Загрузить модель**:
```bash
# Llama 2 (7B)
ollama pull llama2

# Mistral (7B)
ollama pull mistral

# Llama 3 (8B)
ollama pull llama3

# Для русского языка лучше использовать:
ollama pull saiga
```

2. **Запустить Ollama**:
```bash
ollama serve
```

3. **Обновить .env**:
```env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama2
OPENAI_API_KEY=dummy-key
```

4. **Перезапустить приложение**:
```bash
docker-compose restart
```

### Сравнение моделей

| Модель | Размер | RAM | Скорость | Качество (RU) |
|--------|--------|-----|----------|---------------|
| llama2 | 7B | 8GB | Средняя | Среднее |
| mistral | 7B | 8GB | Быстрая | Хорошее |
| llama3 | 8B | 10GB | Средняя | Отличное |
| saiga | 7B | 8GB | Средняя | Отличное |

## Использование vLLM

vLLM - высокопроизводительный сервер для запуска LLM.

### Установка

```bash
pip install vllm
```

### Запуск

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-chat-hf \
  --port 8080
```

### Настройка

```env
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_MODEL=meta-llama/Llama-2-7b-chat-hf
OPENAI_API_KEY=dummy-key
```

## Production развертывание

### Docker Compose для production

Создать `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    image: llm-assistant:latest
    container_name: llm_assistant_prod
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
    volumes:
      - app_data:/app/data
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: assistant_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: always

volumes:
  app_data:
  postgres_data:
  redis_data:
```

### Kubernetes

Пример Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-assistant
  template:
    metadata:
      labels:
        app: llm-assistant
    spec:
      containers:
      - name: assistant
        image: llm-assistant:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Nginx конфигурация

```nginx
upstream llm_assistant {
    least_conn;
    server app:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://llm_assistant;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## Мониторинг

### Prometheus

Добавить в `requirements.txt`:
```
prometheus-client==0.19.0
```

Добавить метрики в код:
```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests')
response_time = Histogram('response_time_seconds', 'Response time')
```

### Grafana Dashboard

Импортировать dashboard для FastAPI или создать свой:
- Request rate
- Response time
- Error rate
- Active conversations

### Health checks

```bash
# Kubernetes
kubectl get pods
kubectl logs llm-assistant-xxx

# Docker
docker ps
docker logs llm_assistant

# Manual check
curl http://localhost:8000/health
```

## Бэкапы

### База данных

```bash
# SQLite
cp data/assistant.db data/backup_$(date +%Y%m%d).db

# PostgreSQL
docker exec postgres pg_dump -U assistant assistant_db > backup.sql
```

### Векторная база

```bash
tar -czf vector_store_backup.tar.gz data/vector_store/
```

### Автоматизация

Добавить в crontab:
```bash
# Ежедневный бэкап в 3 утра
0 3 * * * /path/to/backup_script.sh
```

## Обновление

```bash
# 1. Остановить сервис
docker-compose down

# 2. Получить изменения
git pull

# 3. Пересобрать образ
docker-compose build

# 4. Запустить
docker-compose up -d

# 5. Проверить
docker-compose logs -f
```

## Troubleshooting

### Проблема: Application не стартует

```bash
# Проверить логи
docker-compose logs app

# Проверить .env
cat .env

# Проверить порты
netstat -tulpn | grep 8000
```

### Проблема: Out of Memory

```bash
# Увеличить лимиты в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G
```

### Проблема: Медленные ответы

1. Проверить использование CPU/RAM
2. Использовать локальную LLM
3. Добавить кэширование
4. Уменьшить размер контекста

### Проблема: Ошибки векторной базы

```bash
# Пересоздать индекс
curl -X DELETE http://localhost:8000/documents/clear

# Загрузить документы заново
curl -X POST http://localhost:8000/documents/upload \
  -F "files=@docs/documentation.txt"
```

## Безопасность

1. **Использовать HTTPS** в production
2. **Настроить firewall**:
```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```
3. **Ограничить доступ к API**:
   - JWT токены
   - Rate limiting
   - API keys
4. **Регулярно обновлять зависимости**:
```bash
pip list --outdated
pip install -U package-name
```

