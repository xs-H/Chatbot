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

```json
201 Created

{
  "task_id": "20250329173320"
}
```

- `task_id`(string): 任务唯一 ID, 用于后续查询识别任务的状态和结果

### `GET /api/v1/asr/task/{task_id}`

根据任务 ID 查询识别任务的状态和结果

#### Request

```http
GET /api/v1/asr/task/{task_id}
```

- `{task_id}`(string, Required): 任务名, 在先前创建任务时获取

#### Response

*如果任务已经完成, 返回识别结果:*

```json
200 OK

{
  "task_id": "a1b2c3d4e5f6g7h8",
  "status": "done",
  "text": "那就是青藏高原"
}
```

*若任务正在处理中, 返回:*

```http
202 Accepted
```

`status`参数情况和说明:

| `status` | Description |
|-|-|
| `done` | 任务已完成, 识别结果可用 |
| `error` | 任务处理失败, 可能是音频文件格式不支持或内部错误 |