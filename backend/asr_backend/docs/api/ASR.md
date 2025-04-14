# 服务接口

## 🎧 ASR 语音识别任务

下面是可用的 API 接口列表：

### `POST /api/v1/asr/task`

创建一个语音识别任务，提交二进制语音文件（如 `.mp3`, `.wav`），服务器将异步处理并返回任务 ID

#### Request

```http
POST /api/v1/asr/task
Content-Type: multipart/form-data

{
    "file": {binary sound file}
}
```

- `file`(File, Required): 需要识别的音频文件，支持常见语音文件格式如 `.mp3`, `.wav`

#### Response

*如果任务创建成功, 返回任务 ID:*

```json5
// 201 Created

{
  "task_id": "20250331222301719319"
}
```

- `task_id`(string): 任务唯一 ID, 用于后续查询识别任务的状态和结果

*没有提供音频文件:*


```json5
// 400 Bad Request

{
  "error": "Missing 'file'"
}

```

### `GET /api/v1/asr/task/{task_id}`

根据任务 ID 查询识别任务的状态和结果

#### Request

```http
GET /api/v1/asr/task/{task_id}
```

- `{task_id}`(string, Required): 任务名, 在先前创建任务时获取

#### Response

*如果任务已经完成, 返回识别结果:*

```json5
// 200 OK

{
  "task_id": "20250331222354939437",
  "status": "done",
  // 下面是 Whisper 的识别结果
  "result": {
    "text": "都说印度是外资粉地但为什么谷歌还是偏偏不信邪的往里面砸钱呢",
    "segments": [
      {
        "id": 0,
        "seek": 0,
        "start": 0.0,
        "end": 1.48,
        "text": "都说印度是外资粉地",
        "tokens": [
          50364, // etc, token IDs
        ],
        "temperature": 0.0,
        "avg_logprob": -0.20072998871674408,
        "compression_ratio": 0.90625,
        "no_speech_prob": 0.01584177277982235
      },
      {
        "id": 1,
        "seek": 0,
        "start": 1.48,
        "end": 4.48,
        "text": "但为什么谷歌还是偏偏不信邪的往里面砸钱呢",
        "tokens": [
          50438, // etc, Token IDs
        ],
        "temperature": 0.0,
        "avg_logprob": -0.20072998871674408,
        "compression_ratio": 0.90625,
        "no_speech_prob": 0.01584177277982235
      }
    ],
    "language": "zh"
  }
}
```

*其他情况:*

- 任务正在处理中

```json5
// 202 Accepted

{
  "task_id": "20250331222354939437",
  "status": "processing",
  "result": ""
}
```

- 指定的任务 ID 不存在

```json5
// 404 Not Found

{
  "task_id": "20250331222354939437",
  "status": "Task not found",
  "result": ""
}
```

- 任务出现错误

```json5
// 500 Internal Server Error

{
  "task_id": "20250331222354939437",
  "status": "error",
  "result": "Traceback info..."
}
```


`status`参数情况和说明:

| `status` | Description |
|-|-|
| `done` | 任务已完成, 识别结果可用 |
| `error` | 任务处理失败, 可能是音频文件格式不支持或内部错误 |
| `processing` | 任务正在处理中, 识别结果尚不可用 |
| `not_found` | 任务 ID 不存在, ID 错误或任务已被删除 |