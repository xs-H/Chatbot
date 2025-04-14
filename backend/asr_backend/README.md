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

Use `docker compose` to build and run the container:

```bash
❯ cd docker
❯ docker compose up -d
```

To view logs, use the following command:

```bash
❯ docker compose logs -f
```