FROM dockerproxy.net/library/python:3.11-slim
# FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y curl ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["./start.sh", "--prod"]

