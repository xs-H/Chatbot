# ChatBot - ASR Backend

语音识别(ASR)功能后端, 提供`RESTFUL API`接口.

## 🎧 接口文档: ASR 语音识别任务

下面是可用的 API 接口列表：

### `POST /api/v1/asr/task`

创建一个语音识别任务，提交二进制语音文件（如 `.mp3`, `.wav`），服务器将异步处理并返回任务 ID。

**Request**

```http
POST /api/v1/asr/task
Content-Type: multipart/form-data

{
    "file": {binary sound file}
}
```

- `file`(File, Required): 需要识别的音频文件，支持常见语音文件格式如 `.mp3`, `.wav`.

**Response**

```json
{
  "task_id": "20250329173320",
  "status": "created",
  "text": null
}
```

- `task_id`(string): 任务唯一 ID, 用于后续查询识别任务的状态和结果
- `status`(string): 当前任务状态
- `text`(string): 识别结果文本, 初始为 `null`, 任务完成后返回

### `GET /api/v1/asr/task/{task_id}`

根据任务 ID 查询识别任务的状态和结果。

**Request**

```http
GET /api/v1/asr/task/{task_id}
```

- `{task_id}`(string, Required): 任务名, 可在先前创建任务时获取

**Response**

```json
{
  "task_id": "a1b2c3d4e5f6g7h8",
  "status": "done",
  "text": "那就是青藏高原"
}
```

`status`参数情况和说明:

| `status` | Description |
|-|-|
| `created` | 任务已创建, 等待处理(POST 创建任务时返回) |
| `processing` | 任务正在处理中 |
| `done` | 任务已完成, 识别结果可用 |
| `error` | 任务处理失败, 可能是音频文件格式不支持或内部错误 |
