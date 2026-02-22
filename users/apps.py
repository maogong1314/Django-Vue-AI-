
# 导入 Django 的 AppConfig，用于应用配置
from django.apps import AppConfig


# 定义 users 应用的配置类，继承自 AppConfig
class UsersConfig(AppConfig):
    # 指定默认主键类型为 BigAutoField（大整型自增主键）
    default_auto_field = 'django.db.models.BigAutoField'
    # 指定该 app 的名称为 'users'，与文件夹名一致
    name = 'users'
