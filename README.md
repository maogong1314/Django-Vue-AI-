# AI 问答社区（含小说管理）项目

本项目是一个前后端分离的 AI 问答社区系统，包含问答、评论、用户管理、小说管理与 AI 生成章节等功能。

## 技术栈

- 后端：Django + Django REST Framework
- 前端：Vue 3 + Vite + Pinia
- 数据库：PostgreSQL

## 项目结构

- `qna_platform/`：Django 主项目配置
- `users/`：用户模块
- `qa/`：问答与小说模块
- `frontend/`：前端项目（Vite）
- `media/`：上传文件目录（开发环境）

## 环境要求

- Python 3.10+（建议）
- Node.js 18+（建议）
- PostgreSQL 12+（建议）

## 快速开始（本地开发）

### 1. 后端启动

进入项目目录：

```bash
cd /home/parallels/object_ai/ai_qa_community
```

创建并激活虚拟环境（任选其一）：

```bash
python -m venv venv
source venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

配置数据库（在 `qna_platform/settings.py` 中修改 `DATABASES`）：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'qna_db',
        'USER': 'qna_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

创建数据库并迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

启动后端服务（可自定义监听 IP）：

```bash
# 仅本机访问
python manage.py runserver 127.0.0.1:8000

# 局域网访问（例如 10.211.55.4）
python manage.py runserver 0.0.0.0:8000
```

访问地址示例：

- 本机：`http://127.0.0.1:8000`
- 局域网：`http://10.211.55.4:8000`

如需使用自定义 IP，请在 `qna_platform/settings.py` 中同步修改：

- `ALLOWED_HOSTS` 添加你的 IP
- `CORS_ALLOWED_ORIGINS`、`CSRF_TRUSTED_ORIGINS` 添加对应的前端地址（如 `http://10.211.55.4:3000`）

### 2. 前端启动

进入前端目录：

```bash
cd /home/parallels/object_ai/ai_qa_community/frontend
```

安装依赖：

```bash
npm install
```

启动开发服务器（默认端口 3000）：

```bash
npm run dev
```

前端地址示例：

- 本机：`http://127.0.0.1:3000`
- 局域网：`http://10.211.55.4:3000`

前端已在 `vite.config.js` 中配置代理（前端请求 `/api` 会转发到后端）：

```
/api  ->  http://127.0.0.1:8000
```

如果后端地址改为 `10.211.55.4:8000`，请同步修改 `frontend/vite.config.js` 的 `server.proxy` 目标地址。

## AI 功能配置

项目使用 DeepSeek/OpenAI 等接口（在 `qna_platform/settings.py` 中配置）：

```python
DEEPSEEK_API_KEY = '你的Key'
DEEPSEEK_API_BASE_URL = 'https://api.deepseek.com/v1'
```

## 部署建议（生产环境）

- 后端建议使用 `gunicorn + nginx`
- 前端建议执行 `npm run build` 生成静态资源后部署
- 将 `DEBUG=False`，并设置安全的 `SECRET_KEY`
- 配置真实域名与 `ALLOWED_HOSTS`
- 数据库使用独立 PostgreSQL 实例

## 常见问题

- **前端跨域问题**：确认前端端口为 `3000`，并在后端 `CORS_ALLOWED_ORIGINS` 中已允许该地址
- **上传文件位置**：默认保存到 `media/` 目录
- **依赖过大**：`frontend/node_modules` 不要提交到 Git（已在 `.gitignore` 中忽略）


