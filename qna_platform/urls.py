# Django 主路由配置文件，负责将 URL 映射到对应的视图。
#
# `urlpatterns` 列表定义了所有可访问的 URL 及其对应的处理视图。
# 详细说明见：https://docs.djangoproject.com/en/4.2/topics/http/urls/
#
# 常见用法示例：
# 1. 函数视图：path('', views.home, name='home')
# 2. 类视图：path('', Home.as_view(), name='home')
# 3. 包含其它路由：path('blog/', include('blog.urls'))


from django.contrib import admin  # Django 后台管理模块
from django.urls import path, include  # 定义 URL 路由
from django.http import HttpResponse  # 简单响应
# 导入 DRF 路由器（可自动生成 RESTful 路由）
from rest_framework import routers
from rest_framework.routers import DefaultRouter
# 导入本地 app 的视图
from qa import views as qa_views
from users import views as user_views
# 导入 settings 用于判断 DEBUG 及媒体文件配置
from django.conf import settings
from django.conf.urls.static import static


# 创建一个 DRF 默认路由器实例
router = DefaultRouter()
# 注册用户相关接口（自动生成 /users/ 路由）
router.register(r'users', user_views.UserViewSet)
# 注册问题相关接口（自动生成 /questions/ 路由，指定 basename）
router.register(r'questions', qa_views.QuestionViewSet, basename='question')
# 注册答案相关接口（自动生成 /answers/ 路由）
router.register(r'answers', qa_views.AnswerViewSet)
# 注册评论相关接口（自动生成 /comments/ 路由）
router.register(r'comments', qa_views.CommentViewSet)


# URL 路由表，依次定义所有可访问的接口
urlpatterns = [
    path("", lambda req: HttpResponse("OK")),  # 根路径返回 200
    path('admin/', admin.site.urls),  # Django 后台管理界面
    path('api/upload/', qa_views.FileUploadView.as_view(), name='file-upload'),  # 文件上传接口
    path('api/chat/stream/', qa_views.ChatStreamView.as_view(), name='chat_stream'),  # 聊天流式接口
    path('api/admin/users/', user_views.AdminUserListView.as_view()),  # 管理员获取用户列表
    path('api/admin/delete_user/<int:pk>/', user_views.AdminUserDeleteView.as_view(), name='admin-delete-user'),  # 管理员删除用户
    path('api/admin/register/', user_views.AdminRegisterView.as_view()),  # 管理员注册用户
    path('api/', include(router.urls)),  # 自动生成的 RESTful 路由（用户、问题、答案、评论）
    path('api/novel/', include('qa.urls')),  # 小说相关接口，转发到 qa/urls.py
    path('api/auth/register/', user_views.RegisterView.as_view(), name='register'),  # 用户注册
    path('api/auth/login/', user_views.LoginView.as_view(), name='login'),  # 用户登录
    path('api/auth/logout/', user_views.LogoutView.as_view(), name='logout'),  # 用户登出
    path('api/auth/check/', user_views.CheckAuthView.as_view(), name='check_auth'),  # 检查用户认证状态
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),  # DRF 自带的登录登出页面
]


# 如果处于开发模式（DEBUG=True），则添加媒体文件的静态路由，方便本地访问上传文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
