# 服务器状态检查

## 🛜 应用状态接口

### `POST /api/v1/asr/`

获取应用的当前状态和健康检查

#### Request

```http
GET /api/v1/asr/
```

#### Response

```json
200 OK

{
  "status": "ok",
  "service": "asr-backend",
  "version": "1.0"
}
```