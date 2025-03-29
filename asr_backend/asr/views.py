from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from datetime import datetime
import pytz

def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "asr-backend",
        "version": "1.0",
        "timestamp": datetime.utcnow().replace(tzinfo=pytz.utc).isoformat()
    })
