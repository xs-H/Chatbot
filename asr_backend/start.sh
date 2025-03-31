#!/bin/bash

# 设置模型路径（默认环境变量，否则使用默认路径）
MODEL_PATH="${WHISPER_MODEL:-/data/whisper/small.pt}"
CACHE_PATH="$HOME/.cache/whisper/small.pt"
MODEL_URL="https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt"

# 准备模型目录
mkdir -p "$(dirname "$MODEL_PATH")"

# 检查模型是否存在
if [ -f "$MODEL_PATH" ]; then
    echo "✅ 模型已存在: $MODEL_PATH"
elif [ -f "$CACHE_PATH" ]; then
    echo "📂 从缓存复制模型: $CACHE_PATH → $MODEL_PATH"
    cp "$CACHE_PATH" "$MODEL_PATH"
else
    echo "⬇️  正在下载 Whisper 模型..."
    curl -L "$MODEL_URL" -o "$MODEL_PATH"
fi

# 启动模式
if [[ "$1" == "--prod" ]]; then
    echo "🚀 启动生产模式(Gunicorn)..."
    exec gunicorn server.wsgi:application \
        --bind 0.0.0.0:8001 \
        --workers 3 \
        --access-logfile - \
        --error-logfile -
else
    echo "🚀 启动开发模式(Django runserver)..."
    python manage.py runserver 0.0.0.0:8001
fi
