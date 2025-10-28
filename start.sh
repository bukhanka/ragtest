#!/bin/bash

# Скрипт для быстрого запуска LLM-ассистента

set -e

echo "=================================="
echo "LLM Assistant - Quick Start"
echo "=================================="
echo ""

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю из .env.example..."
    cp .env.example .env
    echo "✓ Файл .env создан"
    echo ""
    echo "⚠️  ВАЖНО: Отредактируйте .env и добавьте ваш OPENAI_API_KEY"
    echo "Пример: OPENAI_API_KEY=sk-your-key-here"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

echo "✓ Docker установлен"
echo ""

# Создание директорий для данных
echo "Создаю директории для данных..."
mkdir -p data
mkdir -p data/vector_store
echo "✓ Директории созданы"
echo ""

# Сборка и запуск
echo "Собираю Docker образы..."
docker-compose build

echo ""
echo "Запускаю сервисы..."
docker-compose up -d

echo ""
echo "Ожидаю запуска сервисов (30 секунд)..."
sleep 30

echo ""
echo "Проверяю статус..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ API запущен успешно!"
    echo ""
    echo "=================================="
    echo "Сервис доступен по адресу:"
    echo "  API: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
    echo "=================================="
    echo ""
    echo "Примеры использования:"
    echo ""
    echo "# Проверить статус"
    echo "curl http://localhost:8000/health"
    echo ""
    echo "# Задать вопрос"
    echo 'curl -X POST http://localhost:8000/chat \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{"message": "Что такое RAG?"}'"'"
    echo ""
    echo "# Загрузить документ"
    echo "curl -X POST http://localhost:8000/documents/upload \\"
    echo '  -F "files=@tests/test_sample_docs.txt"'
    echo ""
    echo "# Посмотреть логи"
    echo "docker-compose logs -f app"
    echo ""
    echo "# Остановить сервисы"
    echo "docker-compose down"
    echo ""
else
    echo "✗ Не удалось подключиться к API"
    echo "Проверьте логи: docker-compose logs app"
    exit 1
fi

