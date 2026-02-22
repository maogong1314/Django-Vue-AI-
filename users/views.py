
# 导入 Django 的渲染函数（本文件未直接用到）
from django.shortcuts import render
# 导入 DRF 的视图集、权限、状态码
from rest_framework import viewsets, permissions, status
# 导入 Django 的认证、登录、登出方法
from django.contrib.auth import authenticate, login, logout
# 导入 DRF 的 APIView 基类
from rest_framework.views import APIView
# 导入 DRF 的响应对象
from rest_framework.response import Response
# 导入自定义用户模型
from .models import CustomUser
# 导入用户序列化器
from .serializers import UserSerializer
# 导入 DRF 的管理员权限
from rest_framework.permissions import IsAdminUser
# 导入 CSRF 豁免装饰器
from django.views.decorators.csrf import csrf_exempt
# 导入方法装饰器工具
from django.utils.decorators import method_decorator
# 导入日志模块
import logging

# 用户相关视图定义区


# 用户只读视图集，允许已认证用户查看用户列表和详情
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    一个只读的API端点，允许查看用户列表和详情。
    """
    # 查询所有用户，按注册时间倒序排列
    queryset = CustomUser.objects.all().order_by('-date_joined')
    # 指定序列化器
    serializer_class = UserSerializer
    # 仅允许已认证用户访问
    permission_classes = [permissions.IsAuthenticated]


# 登录视图，禁用 CSRF 检查，允许任意用户访问
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    # 禁用 DRF 的 SessionAuthentication，跳过 CSRF 检查
    authentication_classes = []
    # 允许所有用户访问
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        # 获取用户名和密码
        username = request.data.get('username')
        password = request.data.get('password')
        # 验证用户身份
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 登录用户
            login(request, user)
            # 返回用户信息
            return Response(UserSerializer(user).data)
        else:
            # 认证失败，返回错误信息
            return Response({'error': '错误的凭证'}, status=status.HTTP_400_BAD_REQUEST)


# 登出视图
@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    authentication_classes = []
    def post(self, request, *args, **kwargs):
        # 注销当前用户
        logout(request)
        # 返回 204 无内容响应
        return Response(status=status.HTTP_204_NO_CONTENT)


# 检查用户认证状态视图
class CheckAuthView(APIView):
    def get(self, request, *args, **kwargs):
        # 如果已认证，返回用户信息
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data)
        else:
            # 未认证，返回错误信息
            return Response({'error': '未认证'}, status=status.HTTP_401_UNAUTHORIZED)


# 用户注册视图，允许所有用户访问
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        # 获取用户名、密码、邮箱（邮箱可选）
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        # 校验用户名和密码不能为空
        if not username or not password:
            return Response({'error': '用户名和密码不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        # 检查用户名是否已存在
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': '该用户名已存在。'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建新用户（不自动登录）
        user = CustomUser.objects.create_user(username=username, password=password, email=email)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


# 管理员获取用户列表视图，允许所有用户访问（实际生产应限制权限）
@method_decorator(csrf_exempt, name='dispatch')
class AdminUserListView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        # 查询所有用户
        users = CustomUser.objects.all()
        # 返回用户列表
        return Response(UserSerializer(users, many=True).data)


# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)


# 管理员删除用户视图，允许所有用户访问（实际生产应限制权限）
@method_decorator(csrf_exempt, name='dispatch')
class AdminUserDeleteView(APIView):
    permission_classes = [permissions.AllowAny]
    def delete(self, request, pk):
        # 记录删除操作日志
        logger.error(f"DELETE called for user {pk}")
        # 查找用户
        user = CustomUser.objects.filter(pk=pk).first()
        if user:
            # 删除用户
            user.delete()
            return Response({'success': True})
        # 用户不存在，返回错误
        return Response({'error': '用户不存在'}, status=404)


# 管理员注册用户视图，允许所有用户访问（实际生产应限制权限）
@method_decorator(csrf_exempt, name='dispatch')
class AdminRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        # 获取用户名、密码、邮箱
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        # 校验用户名和密码不能为空
        if not username or not password:
            return Response({'error': '用户名和密码不能为空。'}, status=400)
        # 检查用户名是否已存在
        if CustomUser.objects.filter(username=username).exists():
            return Response({'error': '该用户名已存在。'}, status=400)
        # 创建管理员用户（is_staff=True）
        user = CustomUser.objects.create_user(username=username, password=password, email=email, is_staff=True)
        return Response(UserSerializer(user).data, status=201)
