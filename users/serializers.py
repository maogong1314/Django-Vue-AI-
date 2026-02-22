
# 导入 DRF 的序列化器基类
from rest_framework import serializers
# 导入自定义用户模型
from .models import CustomUser

# 定义用户序列化器，用于将用户模型与 JSON 互转
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        # 指定序列化的模型为 CustomUser
        model = CustomUser
        # 指定需要序列化的字段列表
        fields = ['id', 'username', 'email', 'bio', 'date_joined', 'is_staff', 'is_superuser']