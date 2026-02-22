
# 导入 Django 的模型基类
from django.db import models
# 导入 Django 的内置用户抽象基类，便于自定义用户模型
from django.contrib.auth.models import AbstractUser


# 自定义用户模型，继承自 Django 的 AbstractUser
class CustomUser(AbstractUser):
    # 新增字段：个人简介，允许为空，后台显示名为“个人简介”
    bio = models.TextField(blank=True, verbose_name='个人简介')


    class Meta:
        # 设置后台显示的模型名称为“用户”
        verbose_name = '用户'
        # 设置后台显示的复数名称（与单数一致）
        verbose_name_plural = verbose_name


    # 定义对象的字符串表示，返回用户名
    def __str__(self):
        return self.username
