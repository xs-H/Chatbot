#!/bin/bash

CACHE_PATH="$HOME/.cache/whisper/small.pt"
MODEL_URL="https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt"

if [ -n "$WHISPER_MODEL" ]; then
    MODEL_PATH="$WHISPER_MODEL"
else
    MODEL_PATH="$CACHE_PATH"
fi

mkdir -p "$(dirname "$MODEL_PATH")"

if [ -n "$WHISPER_MODEL" ]; then
    # 在指定 WHISPER_MODEL 的情况下, 若存在则直接使用, 否则下载默认模型
    if [ -f "$WHISPER_MODEL" ]; then
        echo "✅ Whisper model exists: $WHISPER_MODEL"
    else
        echo "⬇️ Downloading whisper model to $WHISPER_MODEL..."
        curl -L "$MODEL_URL" -o "$WHISPER_MODEL"
    fi
else
    # 若没有指定 WHISPER_MODEL, 则检查缓存目录下是否存在模型
    # 如果存在则使用缓存的模型, 否则下载默认模型
    if [ -f "$CACHE_PATH" ]; then
        echo "📂 Cache found. Setting WHISPER_MODEL to $CACHE_PATH"
        export WHISPER_MODEL="$CACHE_PATH"
    else
        echo "⬇️ Downloading whisper model to $CACHE_PATH..."
        curl -L "$MODEL_URL" -o "$CACHE_PATH"
        export WHISPER_MODEL="$CACHE_PATH"
    fi
fi

if [[ "$1" == "--prod" ]]; then
    echo "🚀 Start PRODUCT mode(Gunicorn)..."
    exec gunicorn server.wsgi:application \
        --bind 0.0.0.0:8001 \
        --workers 1 \
        --access-logfile - \
        --error-logfile -
else
    echo "🚀 Start DEV mode(Django runserver)..."
    export DEBUG=1
    export ALLOWED_HOSTS=*
    python manage.py runserver 0.0.0.0:8001
fi
