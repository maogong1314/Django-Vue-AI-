
# ASGI 配置文件，用于启动 qna_platform 项目的异步服务器接口
# 详细文档见：https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/


# 导入 os 模块，用于设置环境变量
import os


# 从 django.core.asgi 导入 get_asgi_application，用于获取 ASGI 应用对象
from django.core.asgi import get_asgi_application


# 设置默认的 Django 配置文件环境变量，指定 settings.py 路径
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qna_platform.settings')


# 获取 ASGI 应用对象，供 ASGI 服务器（如 daphne、uvicorn）调用
application = get_asgi_application()
