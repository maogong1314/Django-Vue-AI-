
# 导入 DRF 的 serializers 模块，用于序列化和反序列化数据
from rest_framework import serializers
# 导入相关模型
from .models import Question, Answer, Comment, NovelCategory, Novel, NovelChapter, NovelChapterComment
# 导入自定义的用户序列化器
from users.serializers import UserSerializer
from .security import sanitize_user_input


# 评论序列化器
class CommentSerializer(serializers.ModelSerializer):
    # 嵌套用户信息，只读
    author = UserSerializer(read_only=True)


    class Meta:
        # 指定序列化的模型和字段
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']

    def validate_content(self, value):
        return sanitize_user_input(value, field_name='content')


# 回答序列化器
class AnswerSerializer(serializers.ModelSerializer):
    # 嵌套用户信息，只读
    author = UserSerializer(read_only=True)
    # 嵌套评论信息，只读
    comments = CommentSerializer(many=True, read_only=True)


    class Meta:
        # 指定序列化的模型和字段
        model = Answer
        fields = ['id', 'content', 'author', 'created_at', 'comments']

    def validate_content(self, value):
        return sanitize_user_input(value, field_name='content')


# 问题序列化器
class QuestionSerializer(serializers.ModelSerializer):
    # 嵌套用户信息，只读
    author = UserSerializer(read_only=True)
    # 嵌套回答信息，只读
    answers = AnswerSerializer(many=True, read_only=True)


    class Meta:
        # 指定序列化的模型和字段
        model = Question
        fields = ['id', 'title', 'content', 'author', 'created_at', 'answers', 'is_pinned']

    def validate_title(self, value):
        return sanitize_user_input(value, field_name='title')

    def validate_content(self, value):
        return sanitize_user_input(value, field_name='content')


# 小说分类序列化器
class NovelCategorySerializer(serializers.ModelSerializer):
    class Meta:
        # 序列化所有字段
        model = NovelCategory
        fields = '__all__'

    def validate_name(self, value):
        return sanitize_user_input(value, field_name='name')


# 小说章节序列化器
class NovelChapterSerializer(serializers.ModelSerializer):
    class Meta:
        # 序列化所有字段
        model = NovelChapter
        fields = '__all__'

    def validate_title(self, value):
        return sanitize_user_input(value, field_name='title')


# 小说序列化器
class NovelSerializer(serializers.ModelSerializer):
    # 嵌套章节信息，只读
    chapters = NovelChapterSerializer(many=True, read_only=True)
    # 嵌套分类信息，只读
    category = NovelCategorySerializer(read_only=True)
    # 分类主键字段，仅写入
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=NovelCategory.objects.all(), source='category', write_only=True
    )


    class Meta:
        # 指定序列化的模型和字段
        model = Novel
        fields = ['id', 'title', 'cover_url', 'category', 'category_id', 'created_at', 'chapters']

    def validate_title(self, value):
        return sanitize_user_input(value, field_name='title')


# 小说章节评论序列化器
class NovelChapterCommentSerializer(serializers.ModelSerializer):
    # 用户名字段，只读，取自 user.username
    user_name = serializers.CharField(source='user.username', read_only=True)
    # 用户主键字段，只读
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        # 指定序列化的模型和字段
        model = NovelChapterComment
        fields = ['id', 'chapter', 'user', 'user_name', 'content', 'created_at']

    def validate_content(self, value):
        return sanitize_user_input(value, field_name='content')