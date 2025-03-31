# ChatBot - ASR Backend

语音识别(ASR)功能后端, 提供`RESTFUL API`接口

## 目录

```
❯ tree
.
├── README.md
├── asr
│   ├── __init__.py
│   ├── apps.py
│   ├── models
│   │   └── TranscribeTask.py
│   ├── services
│   │   └── transcribe
│   │       ├── WhisperTranscriber.py
│   │       └── __init__.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docker
│   ├── build.sh
│   ├── dev.Dockerfile
│   └── docker-compose.yml
├── docs                    // 文档
│   └── api                 // API 相关
│       ├── ASR.md          // ASR 功能接口
│       └── status.md       // 服务器健康监测接口
├── manage.py
├── pyproject.toml
├── requirements.txt        // 开发环境 Python 依赖
├── server
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── start.sh
```
## Build&Run

### Build Docker Image

Change directory to `docker` and build the image:

```bash
❯ cd docker
❯ ./build.sh
```

Then run the container:

```bash
❯ docker run -d \
   --name asr_backend \
    -p 8001:8001 \
    -v ./playground:/app/data \
    asr_backend:latest
```

### Docker Compose Run

Or, use `docker-compose` to build and run the container:

```bash
❯ cd docker
❯ docker compose up -d
```
