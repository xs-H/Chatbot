# 服务器状态检查

## 🛜 应用状态接口

### `POST /api/v1/asr/status`

获取应用的当前状态和健康检查

#### Request

```http
GET /api/v1/asr/status
```

#### Response

```json
200 OK

{
  "status": "ok",
  "service": "asr-backend",
  "version": "1.0.0",
  "timestamp": "2025-03-29T12:34:56Z"
}
```