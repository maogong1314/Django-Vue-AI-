
# 导入 Django 的 models 模块，用于定义数据模型
from django.db import models
# 导入 settings，用于获取用户模型配置
from django.conf import settings
# 导入自定义用户模型
from users.models import CustomUser


# 问题模型，表示一个提问
class Question(models.Model):
    # 问题标题，最大长度200
    title = models.CharField(max_length=200, verbose_name='标题')
    # 问题内容
    content = models.TextField(verbose_name='内容')
    # 作者，外键关联用户表，删除用户时问题也删除
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions', verbose_name='作者')
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 是否置顶
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')


    class Meta:
        # 后台显示名称
        verbose_name = '问题'
        verbose_name_plural = verbose_name
        # 默认按创建时间倒序排列
        ordering = ['-created_at']


    # 返回问题标题作为对象字符串表示
    def __str__(self):
        return self.title


# 回答模型，表示对问题的回答
class Answer(models.Model):
    # 所属问题，外键关联 Question，删除问题时回答也删除
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='问题')
    # 回答内容
    content = models.TextField(verbose_name='内容')
    # 作者，外键关联用户表
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers', verbose_name='作者')
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')


    class Meta:
        # 后台显示名称
        verbose_name = '回答'
        verbose_name_plural = verbose_name
        # 默认按创建时间倒序排列
        ordering = ['-created_at']


    # 返回对象字符串表示，显示关联问题标题
    def __str__(self):
        return f'对 "{self.question.title}" 的回答'


# 评论模型，表示对回答的评论
class Comment(models.Model):
    # 所属回答，外键关联 Answer，删除回答时评论也删除
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='comments', verbose_name='回答')
    # 评论内容
    content = models.TextField(verbose_name='内容')
    # 作者，外键关联用户表
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', verbose_name='作者')
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')


    class Meta:
        # 后台显示名称
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        # 默认按创建时间正序排列
        ordering = ['created_at']


    # 返回对象字符串表示，显示关联问题标题
    def __str__(self):
        return f'对 "{self.answer.question.title}" 回答的评论'


# 小说分类模型
class NovelCategory(models.Model):
    # 分类名称，唯一
    name = models.CharField(max_length=100, unique=True)


# 小说模型
class Novel(models.Model):
    # 小说标题
    title = models.CharField(max_length=200)
    # 所属分类，外键关联 NovelCategory
    category = models.ForeignKey(NovelCategory, on_delete=models.CASCADE, related_name='novels')
    # 封面图片链接，可为空
    cover_url = models.URLField(blank=True, null=True)
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True)


# 小说章节模型
class NovelChapter(models.Model):
    # 所属小说，外键关联 Novel
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters')
    # 章节标题
    title = models.CharField(max_length=200)
    # 章节内容
    content = models.TextField()
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True)


# 小说章节评论模型
class NovelChapterComment(models.Model):
    # 所属章节，外键关联 NovelChapter
    chapter = models.ForeignKey('NovelChapter', on_delete=models.CASCADE, related_name='comments')
    # 评论用户，外键关联自定义用户表
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # 评论内容
    content = models.TextField()
    # 创建时间，自动添加
    created_at = models.DateTimeField(auto_now_add=True)
