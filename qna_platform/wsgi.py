
"""
WSGI 配置文件，供 qna_platform 项目部署使用。

本文件将 WSGI 应用暴露为模块级变量 `application`，供 WSGI 服务器（如 gunicorn、uWSGI）调用。

更多关于 WSGI 及部署的说明请参考：
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""


# 导入 os 模块，用于设置环境变量
import os


# 从 django.core.wsgi 导入 get_wsgi_application，用于获取 WSGI 应用对象
from django.core.wsgi import get_wsgi_application


# 设置默认的 Django 配置文件环境变量，指定 settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qna_platform.settings')


# 获取 WSGI 应用对象，供 WSGI 服务器调用
application = get_wsgi_application()
