
# Django 配置文件，包含整个 qna_platform 项目的所有设置。
#
# 由 'django-admin startproject' 命令自动生成，Django 版本为 4.2.23。
#
# 更多关于本文件的信息请参考：
# https://docs.djangoproject.com/en/4.2/topics/settings/
#
# 所有配置项及其详细说明请参考：
# https://docs.djangoproject.com/en/4.2/ref/settings/



# 导入 Path 用于处理文件和目录路径
from pathlib import Path
# 导入 os 用于操作系统相关功能（如路径拼接）
import os


# 构建项目的基础路径，BASE_DIR 指向项目的根目录
BASE_DIR = Path(__file__).resolve().parent.parent



# 快速开发环境设置（不适用于生产环境）
# 详细说明见：https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/


# 安全警告：生产环境中请务必保密 SECRET_KEY
SECRET_KEY = 'django-insecure-$xg41+o&&oz&0u%+xbg=po$7r5nzxzyqp-x6@38wm@xs^&yg+3'


# 安全警告：生产环境请关闭 DEBUG
DEBUG = True  # True 表示开启调试模式，开发时使用，生产环境应设为 False


# 允许访问本项目的主机名/IP 列表
ALLOWED_HOSTS = ['10.211.55.4', 'localhost', '127.0.0.1']



# 应用定义（Django 会加载的所有 app）


# 已安装的应用（内置、第三方、本地）
INSTALLED_APPS = [
    'django.contrib.admin',            # Django 后台管理
    'django.contrib.auth',             # 认证系统
    'django.contrib.contenttypes',     # 内容类型框架
    'django.contrib.sessions',         # 会话框架
    'django.contrib.messages',         # 消息框架
    'django.contrib.staticfiles',      # 静态文件管理

    # 第三方应用
    'rest_framework',                  # Django REST framework，用于 API 开发
    'corsheaders',                     # 处理跨域请求

    # 本地应用
    'users',                           # 用户相关 app
    'qa',                              # 问答相关 app
]


# 中间件配置（请求/响应处理链）
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',           # 安全相关中间件
    'corsheaders.middleware.CorsMiddleware',                   # 处理跨域请求的中间件
    'django.contrib.sessions.middleware.SessionMiddleware',    # 会话管理
    'django.middleware.common.CommonMiddleware',               # 通用中间件
    'django.middleware.csrf.CsrfViewMiddleware',               # CSRF 防护
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 认证
    'django.contrib.messages.middleware.MessageMiddleware',    # 消息
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # 防止点击劫持
]


# 根 URL 配置，指向项目的主路由文件
ROOT_URLCONF = 'qna_platform.urls'


# 模板系统配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # 使用 Django 模板引擎
        'DIRS': [],                                                    # 模板文件夹列表（可自定义）
        'APP_DIRS': True,                                              # 是否自动查找各 app 下的 templates 目录
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',            # 调试上下文
                'django.template.context_processors.request',          # 请求对象上下文
                'django.contrib.auth.context_processors.auth',         # 认证上下文
                'django.contrib.messages.context_processors.messages', # 消息上下文
            ],
        },
    },
]


# WSGI 应用入口，用于部署
WSGI_APPLICATION = 'qna_platform.wsgi.application'



# 数据库配置
# 详细说明见：https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',           # SQLite 引擎（默认注释掉）
        # 'NAME': BASE_DIR / 'db.sqlite3',                  # SQLite 数据库文件路径
        'ENGINE': 'django.db.backends.postgresql',          # 使用 PostgreSQL 数据库
        'NAME': 'qna_db',      # 数据库名（请根据实际情况修改）
        'USER': 'qna_user',    # 数据库用户名（请根据实际情况修改）
        'PASSWORD': 'password',# 数据库密码（请根据实际情况修改）
        'HOST': 'localhost',   # 数据库主机地址
        'PORT': '5432',        # 数据库端口
    }
}



# 密码校验器配置
# 详细说明见：https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', # 检查密码与用户属性相似性
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',           # 检查密码最小长度
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',          # 检查常见密码
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',         # 检查密码是否为纯数字
    },
]



# 国际化配置
# 详细说明见：https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'   # 语言代码（如需中文可改为 zh-hans）
TIME_ZONE = 'UTC'         # 时区（如需北京时间可改为 Asia/Shanghai）
USE_I18N = True           # 启用国际化
USE_TZ = True             # 启用时区支持



# 静态文件（CSS、JS、图片等）配置
# 详细说明见：https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/'    # 静态文件 URL 前缀


# 默认主键字段类型
# 详细说明见：https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 媒体文件（用户上传文件）相关配置
MEDIA_URL = '/media/'  # 媒体文件 URL 前缀
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 媒体文件存储路径


# 自定义用户模型（指向 users 应用下的 CustomUser）
AUTH_USER_MODEL = 'users.CustomUser'


# AI 引擎相关配置
DEEPSEEK_API_KEY = 'sk-c9f1b9f0cb6c42e0884a41e374b43d6a'  # DeepSeek API 密钥
DEEPSEEK_API_BASE_URL = 'https://api.deepseek.com/v1'      # DeepSeek API 基础 URL


# 登录/登出后重定向配置
LOGIN_REDIRECT_URL = '/api/'   # 登录后跳转地址
LOGOUT_REDIRECT_URL = '/api/'  # 登出后跳转地址


# 跨域资源共享（CORS）相关配置
CORS_ALLOWED_ORIGINS = [
    "http://10.1.1.190:3000",
    "http://10.211.55.4:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# 允许跨域请求携带凭证（如 cookie）
CORS_ALLOW_CREDENTIALS = True

# 允许跨域请求的请求头列表
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# 受信任的 CSRF 来源（允许这些来源的跨域 CSRF 请求）
CSRF_TRUSTED_ORIGINS = [
    "http://10.1.1.190:3000",
    "http://10.211.55.4:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# Session Cookie 配置
# 开发环境下 SameSite=None 且 Secure=False 会被浏览器拒收，导致登录态丢失。
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
# CSRF Cookie 配置
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False



