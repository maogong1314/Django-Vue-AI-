
# 导入 Django 的 AppConfig，用于应用配置
from django.apps import AppConfig



# 定义 QaConfig 类，继承自 AppConfig，用于配置 qa 应用
class QaConfig(AppConfig):
    # 设置模型的默认主键类型为 BigAutoField（大整型自增主键）
    default_auto_field = 'django.db.models.BigAutoField'
    # 指定当前 app 的名称为 'qa'
    name = 'qa'
