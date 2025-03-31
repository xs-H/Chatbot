#!/bin/bash

MODEL_PATH="${WHISPER_MODEL:-/data/whisper/small.pt}"
CACHE_PATH="$HOME/.cache/whisper/small.pt"
MODEL_URL="https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt"

mkdir -p "$(dirname "$MODEL_PATH")"

if [ -f "$MODEL_PATH" ]; then
    echo "✅ Whisper model exists: $MODEL_PATH"
elif [ -f "$CACHE_PATH" ]; then
    echo "📂 Copying whisper model from cache: $CACHE_PATH → $MODEL_PATH"
    cp "$CACHE_PATH" "$MODEL_PATH"
else
    echo "⬇️ Downloading whisper model..."
    curl -L "$MODEL_URL" -o "$MODEL_PATH"
fi

if [[ "$1" == "--prod" ]]; then
    echo "🚀 Start PRODUCT mode(Gunicorn)..."
    exec gunicorn server.wsgi:application \
        --bind 0.0.0.0:8001 \
        --workers 3 \
        --access-logfile - \
        --error-logfile -
else
    echo "🚀 Start DEV mode(Django runserver)..."
    export DEBUG=1
    export ALLOWED_HOSTS=*
    python manage.py runserver 0.0.0.0:8001
fi
