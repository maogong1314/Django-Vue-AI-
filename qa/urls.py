
# 导入 Django 的 path 和 include，用于路由配置
from django.urls import path, include
# 导入 DRF 的 DefaultRouter，用于自动生成 RESTful 路由
from rest_framework.routers import DefaultRouter
# 导入视图类和视图集
from .views import (
    NovelCategoryViewSet,  # 小说分类视图集
    NovelViewSet,          # 小说视图集
    NovelChapterViewSet,   # 小说章节视图集
    GenerateNovelChapterView,         # AI 生成章节视图
    GenerateNovelChapterStreamView,   # AI 生成章节流式视图
    NovelSpiderAPIView,               # 小说爬虫 API 视图
    NovelChapterCommentViewSet,       # 小说章节评论视图集
    CoverProxyView                    # 封面代理视图
)


# 创建一个默认的路由器对象
router = DefaultRouter()
# 注册小说分类的路由，自动生成增删改查接口
router.register(r'novel-categories', NovelCategoryViewSet)
# 注册小说的路由，自动生成增删改查接口
router.register(r'novels', NovelViewSet)
# 注册小说章节的路由，自动生成增删改查接口
router.register(r'novel-chapters', NovelChapterViewSet)
# 注册小说章节评论的路由，自动生成增删改查接口
router.register(r'novel-chapter-comments', NovelChapterCommentViewSet)


# 定义所有接口的 URL 路由表
urlpatterns = [
    # 包含上面注册的所有 RESTful 路由（如 /novels/、/novel-categories/ 等）
    path('', include(router.urls)),
    # AI 生成章节接口（普通模式）
    path('generate-chapter/', GenerateNovelChapterView.as_view()),
    # AI 生成章节接口（流式返回模式）
    path('generate-chapter-stream/', GenerateNovelChapterStreamView.as_view()),
    # 小说爬虫接口，触发爬取小说
    path('novel-spider/', NovelSpiderAPIView.as_view()),
    # 封面图片代理接口，解决跨域问题
    path('cover-proxy/', CoverProxyView.as_view()),
]