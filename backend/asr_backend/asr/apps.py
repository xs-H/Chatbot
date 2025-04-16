from django.apps import AppConfig
from django.utils.deprecation import MiddlewareMixin


class AsrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asr"


class CorsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # 在响应头中添加CORS相关的字段
        response["Access-Control-Allow-Origin"] = "*"  # 允许所有来源
        response["Access-Control-Allow-Methods"] = (
            "GET, POST, OPTIONS, PUT, DELETE"  # 允许的方法
        )
        response["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"  # 允许的请求头
        )
        return response
