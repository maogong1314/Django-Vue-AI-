# 导入 Django 的 render 和 get_object_or_404，用于渲染页面和获取对象
from django.shortcuts import render, get_object_or_404
# 导入 DRF 的视图集和权限控制
from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication
# 导入 settings，用于读取配置
from django.conf import settings
# 导入 OpenAI SDK，用于调用 AI 服务
from openai import OpenAI
# 导入流式响应，用于大文本/AI流式输出
from django.http import StreamingHttpResponse
# 导入 CSRF 相关装饰器
from django.views.decorators.csrf import csrf_exempt
# 导入方法装饰器
from django.utils.decorators import method_decorator
# 导入 DRF 的 APIView 基类
from rest_framework.views import APIView
# 导入 action 装饰器，用于自定义路由
from rest_framework.decorators import action
# 导入 DRF 的 Response 响应对象
from rest_framework.response import Response
# 导入 requests 库，用于 HTTP 请求
import requests
# 导入 HttpResponse，用于返回原始数据
from django.http import HttpResponse
# 导入文件存储类
from django.core.files.storage import FileSystemStorage
# 导入 os、uuid、threading 等常用库
import os
import uuid
import threading
# 导入爬虫相关方法
from .spider import spider_import_novel, get_new_task_id, get_spider_progress, set_spider_progress, cancel_spider_task

# 导入所有模型
from .models import Question, Answer, Comment, NovelCategory, Novel, NovelChapter, NovelChapterComment
# 导入自定义用户模型
from users.models import CustomUser
# 导入所有序列化器
from .serializers import QuestionSerializer, AnswerSerializer, CommentSerializer, NovelCategorySerializer, NovelSerializer, NovelChapterSerializer, NovelChapterCommentSerializer
# 导入爬虫相关方法（重复导入，可优化）
from .spider import spider_import_novel, get_new_task_id, get_spider_progress
from .security import sanitize_user_input, ensure_positive_int

# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    保留 Session 登录态认证，但跳过 DRF 的 CSRF 二次校验。
    """

    def enforce_csrf(self, request):
        return

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限类，只允许对象的所有者编辑它。
    
    继承自 DRF 的 BasePermission，用于控制用户对资源的访问权限。
    安全方法（GET、HEAD、OPTIONS）允许所有用户访问，
    其他方法（POST、PUT、DELETE）只允许对象所有者操作。
    """
    def has_object_permission(self, request, view, obj):
        # 如果是安全方法（GET、HEAD、OPTIONS），允许访问
        if request.method in permissions.SAFE_METHODS:
            return True
        # 否则检查对象作者是否为当前用户
        return obj.author == request.user

# 新增：评论所有者或管理员可编辑
class IsOwnerOrStaff(permissions.BasePermission):
    """
    自定义权限类，允许对象所有者或管理员修改/删除。
    
    继承自 DRF 的 BasePermission，提供更灵活的权限控制。
    安全方法允许所有用户访问，其他方法允许对象所有者或管理员操作。
    主要用于评论管理，确保用户只能删除自己的评论，管理员可以管理所有评论。
    """
    def has_object_permission(self, request, view, obj):
        # 如果是安全方法，允许访问
        if request.method in permissions.SAFE_METHODS:
            return True
        # 检查是否为对象所有者或管理员
        return (hasattr(obj, 'user') and obj.user == request.user) or request.user.is_staff

class QuestionViewSet(viewsets.ModelViewSet):
    """
    问题视图集，提供问题的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持用户创建问题，并自动调用 AI 服务生成回答。
    包含自定义的 answers 动作，用于获取问题下的所有回答。
    
    Attributes:
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """
    # 指定序列化器类
    serializer_class = QuestionSerializer
    # 设置权限类：登录用户可写，未登录只读，且只能操作自己的内容
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        获取查询集，只返回当前认证用户的问题。
        
        Returns:
            QuerySet: 当前用户的问题列表，按创建时间倒序排列
        """
        # 获取当前用户
        user = self.request.user
        # 如果用户已认证，返回该用户的问题列表
        if user.is_authenticated:
            return Question.objects.filter(author=user).order_by('-created_at')
        # 如果用户未认证，返回空查询集
        return Question.objects.none()

    @action(detail=True, methods=['get'])
    def answers(self, request, pk=None):
        """
        自定义动作：获取指定问题下的所有回答。
        
        Args:
            request: HTTP 请求对象
            pk: 问题的主键ID
            
        Returns:
            Response: 包含回答列表的响应对象
        """
        # 获取指定问题对象
        question = self.get_object()
        # 获取该问题下的所有回答，按创建时间排序
        answers = question.answers.all().order_by('created_at')
        # 序列化回答数据
        serializer = AnswerSerializer(answers, many=True)
        # 返回序列化后的数据
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        重写创建方法，在保存问题后自动调用 AI 生成回答。
        
        Args:
            serializer: 问题序列化器实例
        """
        # 首先，保存用户创建的问题
        question = serializer.save(author=self.request.user)

        # 然后，调用AI生成回答
        try:
            # 创建OpenAI客户端实例
            client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,  # 从设置中获取API密钥
                base_url=settings.DEEPSEEK_API_BASE_URL,  # 从设置中获取API基础URL
            )
            
            # 构建发送给AI的提示词
            prompt = f"请根据以下问题给出一个专业、详细的回答：\n\n标题：{question.title}\n\n内容：{question.content}"

            # 调用AI服务生成回答
            chat_completion = client.chat.completions.create(
                model="deepseek-chat",  # 指定使用的模型
                messages=[
                    {"role": "system", "content": "你是一个问答社区的AI助手，负责回答用户提出的问题。"},  # 系统角色提示
                    {"role": "user", "content": prompt}  # 用户问题内容
                ],
                max_tokens=1024,  # 最大生成token数
                temperature=0.7,  # 生成随机性参数
            )

            # 提取AI生成的回答内容
            ai_answer_content = chat_completion.choices[0].message.content

            # 获取AI助手用户对象，如果不存在则创建
            ai_user = CustomUser.objects.get(username='AI_Assistant')

            # 创建并保存AI的回答到数据库
            Answer.objects.create(
                question=question,  # 关联的问题
                content=ai_answer_content,  # AI生成的回答内容
                author=ai_user  # 作者为AI助手
            )

        except Exception as e:
            # 如果AI调用失败，打印错误，但问题本身仍然会被创建
            # 在生产环境中，这里应该有更完善的错误处理和日志记录
            print(f"调用AI生成回答时出错: {e}")

class AnswerViewSet(viewsets.ModelViewSet):
    """
    回答视图集，提供回答的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持用户创建回答，自动设置作者为当前用户。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """

    # 查询所有回答对象
    queryset = Answer.objects.all()
    # 指定序列化器
    serializer_class = AnswerSerializer
    # 权限：登录用户可写，未登录只读，且只能操作自己的内容
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


    # 创建回答时自动设置作者为当前用户
    def perform_create(self, serializer):
        """
        重写创建方法，自动设置回答作者为当前用户。
        
        Args:
            serializer: 回答序列化器实例
        """
        serializer.save(author=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    """
    评论视图集，提供评论的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持用户创建评论，自动设置作者为当前用户。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """

    # 查询所有评论对象
    queryset = Comment.objects.all()
    # 指定序列化器
    serializer_class = CommentSerializer
    # 权限：登录用户可写，未登录只读，且只能操作自己的内容
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


    # 创建评论时自动设置作者为当前用户
    def perform_create(self, serializer):
        """
        重写创建方法，自动设置评论作者为当前用户。
        
        Args:
            serializer: 评论序列化器实例
        """
        serializer.save(author=self.request.user)

def stream_ai_response(question_content):
    """
    流式AI响应生成器函数。
    
    该函数是一个生成器，用于流式传输 AI 响应，提供实时的AI回答体验。
    通过调用 DeepSeek API 的流式接口，逐步返回AI生成的内容。
    
    Args:
        question_content (str): 用户的问题内容
        
    Yields:
        str: AI生成的回答内容片段
        
    Raises:
        Exception: 当AI服务调用失败时抛出异常
    """

    try:
        # 创建OpenAI客户端，使用配置中的API密钥和地址
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,  # 从设置中获取API密钥
            base_url=settings.DEEPSEEK_API_BASE_URL  # 从设置中获取API基础URL
        )
        # 向AI发起流式对话请求
        stream = client.chat.completions.create(
            model="deepseek-chat",  # 指定使用的模型
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},  # 系统提示
                {"role": "user", "content": question_content}  # 用户问题
            ],
            stream=True  # 启用流式输出
        )
        # 逐步返回AI生成的内容
        for chunk in stream:
            # 获取每个chunk中的内容
            content = chunk.choices[0].delta.content
            # 如果内容不为空，则yield出去
            if content:
                yield content
    except Exception as e:
        # AI服务异常时返回错误信息
        yield f"AI 服务发生错误: {str(e)}"

class ConversationStreamer:
    """
    连续对话流式响应处理器。
    
    该类负责处理连续对话的流式响应，包括：
    - 创建或加载对话(Question)
    - 保存用户的消息和AI的回复(Answer)
    - 将对话历史传递给AI
    - 流式返回AI的实时响应
    
    实现了迭代器接口，可以直接用于StreamingHttpResponse。
    
    Attributes:
        user: 当前用户对象
        user_message: 用户当前消息
        conversation_id: 对话ID（可选）
        full_response: 完整的AI响应列表
        saved: 是否已保存标志
        question: 对话对象
        ai_messages: 发送给AI的消息列表
        generator: 流式生成器
    """
    def __init__(self, user, user_message, conversation_id=None, display_title=None):
        """
        初始化对话流式处理器。
        
        Args:
            user: 当前用户对象
            user_message: 用户消息内容（可含模式前缀，用于发给 AI）
            conversation_id: 现有对话ID，如果为None则创建新对话
            display_title: 对话列表展示用标题（仅用户输入，不含模式 prompt），可选
        """
        # 初始化用户对象
        self.user = user
        # 初始化用户消息
        self.user_message = user_message
        # 初始化对话ID（可选）
        self.conversation_id = conversation_id
        # 对话列表展示标题（仅用户输入）
        self.display_title = (display_title or "").strip() if display_title else None
        # 初始化完整响应列表
        self.full_response = []
        # 初始化保存标志
        self.saved = False
        # 准备对话
        self._prepare_conversation()
        # 准备AI消息
        self._prepare_ai_messages()
        # 初始化流式生成器
        self.generator = self._stream_generator()

    def _prepare_conversation(self):
        """
        准备对话对象，加载现有对话或创建新对话。
        
        如果提供了conversation_id，则加载现有对话；
        否则创建新的对话，标题取用户消息的前50个字符。
        同时保存用户的当前消息到数据库。
        """
        # 如果提供了对话ID，则加载现有对话
        if self.conversation_id:
            self.question = get_object_or_404(Question, id=self.conversation_id, author=self.user)
        else:
            # 否则创建新对话：优先用前端传来的展示标题（不含模式 prompt），否则取用户消息前50字
            title = self.display_title[:50] if self.display_title else self.user_message.strip()[:50]
            self.question = Question.objects.create(title=title, content=self.user_message, author=self.user)
        
        # 保存用户的消息到数据库
        Answer.objects.create(question=self.question, content=self.user_message, author=self.user)
    
    def _prepare_ai_messages(self):
        """
        准备发送给AI的上下文历史消息。
        
        构建包含系统角色和完整对话历史的消息列表，
        用于AI理解对话上下文并生成连贯的回答。
        """
        # 获取对话中的所有回答，按时间排序
        history_answers = self.question.answers.all().order_by('created_at')
        # 初始化AI消息列表，包含系统角色
        self.ai_messages = [{"role": "system", "content": "You are a helpful assistant."}]
        # 遍历历史回答，构建对话上下文
        for ans in history_answers:
            # 判断角色：如果是AI助手的回答则为assistant，否则为user
            role = "assistant" if ans.author.username == 'AI_Assistant' else "user"
            # 将历史消息添加到AI消息列表
            self.ai_messages.append({"role": role, "content": ans.content})

    def _stream_generator(self):
        """
        与AI服务通信并流式返回结果的生成器。
        
        调用DeepSeek API的流式接口，逐步返回AI生成的内容。
        同时将内容保存到full_response列表中，用于后续保存到数据库。
        
        Yields:
            str: AI生成的回答内容片段
            
        Raises:
            Exception: 当AI服务调用失败时抛出异常
        """
        try:
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,  # 从设置中获取API密钥
                base_url=settings.DEEPSEEK_API_BASE_URL  # 从设置中获取API基础URL
            )
            # 发起流式AI请求
            stream = client.chat.completions.create(
                model="deepseek-chat",  # 指定使用的模型
                messages=self.ai_messages,  # 发送包含上下文的完整消息列表
                stream=True  # 启用流式输出
            )
            # 遍历流式响应
            for chunk in stream:
                # 获取每个chunk中的内容
                content = chunk.choices[0].delta.content
                # 如果内容不为空
                if content:
                    # 将内容添加到完整响应列表
                    self.full_response.append(content)
                    # yield内容给前端
                    yield content
        except Exception as e:
            # 发生异常时返回错误信息
            yield f"AI 服务发生错误: {str(e)}"

    def _save_ai_response(self):
        """
        保存AI的完整回答到数据库。
        
        将流式接收到的AI回答内容保存为Answer对象，
        关联到当前对话。包含错误检查，避免保存包含错误的响应。
        """
        # 如果已经保存过，直接返回
        if self.saved:
            return
        # 设置保存标志为True
        self.saved = True
        # 如果没有完整响应，直接返回
        if not self.full_response:
            return
        # 将完整响应列表连接成字符串
        ai_answer = "".join(self.full_response)
        # 如果响应包含错误信息，跳过保存
        if "AI 服务发生错误" in ai_answer:
            print("AI response contained an error, skipping save.")
            return
        # 获取或创建AI助手用户
        ai_user, _ = CustomUser.objects.get_or_create(username='AI_Assistant')
        # 创建并保存AI回答到数据库
        Answer.objects.create(
            question=self.question,  # 关联的问题
            content=ai_answer,  # AI生成的回答内容
            author=ai_user  # 作者为AI助手
        )

    def __iter__(self):
        """
        迭代器接口实现。
        
        首先发送对话ID，然后逐步返回AI的流式响应。
        
        Yields:
            str: 对话ID和AI响应内容
        """
        # 第一次迭代时，先发送conversation_id
        yield f"CONVERSATION_ID:{self.question.id}\n"
        # 然后yield生成器的内容
        yield from self.generator
    
    def close(self):
        """
        在流结束后被调用，用于保存AI回答。
        
        当StreamingHttpResponse结束时，Django会调用此方法，
        确保AI的回答被保存到数据库中。
        """
        self._save_ai_response()

@method_decorator(csrf_exempt, name='dispatch')  
class ChatStreamView(APIView):
    """
    聊天流式视图，提供实时AI对话功能。
    
    继承自 DRF 的 APIView，支持流式响应。
    接收用户消息，创建或继续现有对话，并流式返回AI回答。
    豁免CSRF检查以支持前端流式请求。
    
    Attributes:
        permission_classes: 权限控制类列表
    """
    # 设置权限：只有认证用户才能访问
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        处理POST请求，开始流式AI对话。
        
        Args:
            request: HTTP请求对象，包含用户消息和对话ID
            
        Returns:
            StreamingHttpResponse: 流式响应对象，包含AI的实时回答
        """
        # 从请求数据中获取用户消息
        user_message = sanitize_user_input(request.data.get('question', ''), field_name='question')
        # 从请求数据中获取对话ID
        conversation_id = request.data.get('conversation_id')
        # 对话列表展示标题（仅用户输入，不含模式 prompt），可选
        display_title = request.data.get('title')

        # 如果用户消息为空，返回错误流
        if not user_message:
            def error_stream():
                yield "错误：问题内容不能为空。"
            return StreamingHttpResponse(error_stream(), status=400, content_type='text/plain; charset=utf-8')

        # 创建对话流式处理器
        streamer = ConversationStreamer(request.user, user_message, conversation_id, display_title=display_title)
        # 创建流式HTTP响应
        response = StreamingHttpResponse(streamer, content_type='text/plain; charset=utf-8')
        # 确保close方法能被调用
        response.streaming_content = streamer
        # 返回响应
        return response

class NovelCategoryViewSet(viewsets.ModelViewSet):
    """
    小说分类视图集，提供小说分类的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持管理员创建和管理小说分类。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """
    # 查询所有小说分类对象
    queryset = NovelCategory.objects.all()
    # 指定序列化器
    serializer_class = NovelCategorySerializer
    # 设置权限：登录用户可写，未登录只读
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class NovelViewSet(viewsets.ModelViewSet):
    """
    小说视图集，提供小说的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持按分类过滤小说，按创建时间排序。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """
    # 查询所有小说对象，按创建时间倒序排列
    queryset = Novel.objects.all().order_by('-created_at')
    # 指定序列化器
    serializer_class = NovelSerializer
    # 设置权限：登录用户可写，未登录只读
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        获取查询集，支持按分类过滤。
        
        如果URL参数中包含category，则只返回该分类的小说。
        否则返回所有小说。
        
        Returns:
            QuerySet: 过滤后的小说查询集
        """
        # 从查询参数中获取分类ID
        category_id = self.request.query_params.get('category')
        # 如果指定了分类ID，则过滤该分类的小说
        if category_id:
            return Novel.objects.filter(category_id=category_id).order_by('-created_at')
        # 否则返回所有小说
        return Novel.objects.all().order_by('-created_at')

class NovelChapterViewSet(viewsets.ModelViewSet):
    """
    小说章节视图集，提供小说章节的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持按小说过滤章节，按创建时间排序。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """
    # 查询所有小说章节对象，按创建时间正序排列
    queryset = NovelChapter.objects.all().order_by('created_at')
    # 指定序列化器
    serializer_class = NovelChapterSerializer
    # 设置权限：登录用户可写，未登录只读
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        获取查询集，支持按小说过滤。
        
        如果URL参数中包含novel，则只返回该小说的章节。
        否则返回所有章节。
        
        Returns:
            QuerySet: 过滤后的章节查询集
        """
        # 从查询参数中获取小说ID
        novel_id = self.request.query_params.get('novel')
        # 如果指定了小说ID，则过滤该小说的章节
        if novel_id:
            return NovelChapter.objects.filter(novel_id=novel_id).order_by('created_at')
        # 否则返回所有章节
        return NovelChapter.objects.all().order_by('created_at')

class GenerateNovelChapterView(APIView):
    """
    小说章节生成视图，使用AI生成小说章节内容。
    
    继承自 DRF 的 APIView，接收用户提示词，调用AI服务生成章节内容，
    并将生成的章节保存到数据库中。
    
    Attributes:
        无
    """
    def post(self, request):
        """
        处理POST请求，生成小说章节。
        
        Args:
            request: HTTP请求对象，包含提示词、小说ID和章节标题
            
        Returns:
            Response: 包含生成章节数据的响应对象
        """
        # 从请求数据中获取提示词
        prompt = sanitize_user_input(request.data.get('prompt'), field_name='prompt')
        # 从请求数据中获取小说ID
        novel_id = ensure_positive_int(request.data.get('novel_id'), field_name='novel_id')
        # 从请求数据中获取章节标题
        chapter_title = sanitize_user_input(request.data.get('chapter_title'), field_name='chapter_title')
        # 检查参数是否完整
        if not (prompt and novel_id and chapter_title):
            return Response({'error': '参数不完整'}, status=400)
        # 构建API请求URL
        api_url = settings.DEEPSEEK_API_BASE_URL + '/chat/completions'
        # 获取API密钥
        api_key = settings.DEEPSEEK_API_KEY
        # 设置请求头
        headers = {
            'Authorization': f'Bearer {api_key}',  # 设置认证头
            'Content-Type': 'application/json'  # 设置内容类型
        }
        # 构建请求数据
        data = {
            "model": "deepseek-chat",  # 指定使用的模型
            "messages": [
                {"role": "system", "content": "你是一个专业的小说写作AI，请根据用户的提示写一章小说。"},  # 系统角色提示
                {"role": "user", "content": prompt}  # 用户提示内容
            ],
            "max_tokens": 2048,  # 最大生成token数
            "temperature": 1.0  # 生成随机性参数
        }
        # 发送POST请求到AI服务
        resp = requests.post(api_url, headers=headers, json=data, timeout=60)
        # 检查响应状态码
        if resp.status_code != 200:
            return Response({'error': 'AI生成失败'}, status=500)
        # 从响应中提取生成的内容
        content = resp.json()['choices'][0]['message']['content']
        # 创建新的章节对象
        chapter = NovelChapter.objects.create(
            novel_id=novel_id,  # 关联的小说ID
            title=chapter_title,  # 章节标题
            content=content  # 章节内容
        )
        # 返回序列化后的章节数据
        return Response(NovelChapterSerializer(chapter).data)

class GenerateNovelChapterStreamView(APIView):
    """
    小说章节流式生成视图，使用AI流式生成小说章节内容。
    
    继承自 DRF 的 APIView，支持流式响应，实时返回AI生成的内容。
    生成完成后自动保存章节到数据库。
    
    Attributes:
        无
    """
    def post(self, request):
        """
        处理POST请求，流式生成小说章节。
        
        Args:
            request: HTTP请求对象，包含提示词、小说ID和章节标题
            
        Returns:
            StreamingHttpResponse: 流式响应对象，包含AI生成的实时内容
        """
        # 从请求数据中获取提示词
        prompt = sanitize_user_input(request.data.get('prompt'), field_name='prompt')
        # 从请求数据中获取小说ID
        novel_id = ensure_positive_int(request.data.get('novel_id'), field_name='novel_id')
        # 从请求数据中获取章节标题
        chapter_title = sanitize_user_input(request.data.get('chapter_title'), field_name='chapter_title')
        # 检查参数是否完整
        if not (prompt and novel_id and chapter_title):
            return Response({'error': '参数不完整'}, status=400)

        def ai_stream():
            """
            内部AI流式生成函数。
            
            调用DeepSeek API的流式接口，逐步返回AI生成的内容。
            生成完成后保存章节到数据库。
            
            Yields:
                str: AI生成的章节内容片段
            """
            try:
                # 创建OpenAI客户端
                client = OpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,  # 从设置中获取API密钥
                    base_url=settings.DEEPSEEK_API_BASE_URL  # 从设置中获取API基础URL
                )
                # 发起流式AI请求
                system_prompt = (
                    "你是一个专业的小说写作AI，请根据用户的提示写一章小说。"
                    "你必须只输出连贯的小说正文叙述，不要使用条目、编号列表、要点罗列或快速问答式写法，不要输出「1. 2. 3.」或「核心要点」等格式，只写自然段式的故事内容。"
                )
                stream = client.chat.completions.create(
                    model="deepseek-chat",  # 指定使用的模型
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}  # 用户提示内容
                    ],
                    max_tokens=2048,  # 最大生成token数
                    temperature=1.0,  # 生成随机性参数
                    stream=True  # 启用流式输出
                )
                # 初始化内容变量
                content = ""
                # 遍历流式响应
                for chunk in stream:
                    # 获取每个chunk中的增量内容
                    delta = chunk.choices[0].delta.content
                    # 如果增量内容不为空
                    if delta:
                        # 将增量内容添加到总内容中
                        content += delta
                        # yield增量内容给前端
                        yield delta
                # 生成完毕后保存章节到数据库
                chapter = NovelChapter.objects.create(
                    novel_id=novel_id,  # 关联的小说ID
                    title=chapter_title,  # 章节标题
                    content=content  # 完整的章节内容
                )
            except Exception as e:
                # 发生异常时返回错误信息
                yield f"\n[AI生成失败: {str(e)}]"

        # 返回流式HTTP响应
        return StreamingHttpResponse(ai_stream(), content_type='text/plain; charset=utf-8')

@method_decorator(csrf_exempt, name='dispatch')  # 豁免CSRF检查
class NovelSpiderAPIView(APIView):
    """
    小说爬虫API视图，提供小说爬取功能。
    
    继承自 DRF 的 APIView，支持POST请求启动爬虫任务，
    GET请求查询爬虫进度。豁免CSRF检查以支持外部爬虫调用。
    使用后台线程执行爬虫任务，避免阻塞主线程。
    
    Attributes:
        authentication_classes: 认证类列表（为空，禁用认证）
        permission_classes: 权限控制类列表
    """
    # 禁用SessionAuthentication以避免CSRF检查
    authentication_classes = []
    # 设置权限：允许任何人访问
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        """
        处理POST请求：
        - action=start：启动新的小说爬虫任务
        - action=stop：停止已有的爬虫任务（保留已入库章节）
        """
        action = request.data.get('action', 'start')

        # --- 停止任务 ---
        if action == 'stop':
            task_id = request.data.get('task_id')
            if not task_id:
                return Response({'error': '缺少task_id'}, status=400)
            # 标记任务为取消，具体停止由爬虫循环内部检查实现
            cancel_spider_task(task_id)
            # 不修改数据库中已有章节，只更新进度状态由爬虫线程负责
            return Response({'success': True, 'message': '任务已请求停止'})

        # --- 启动新任务（默认行为） ---
        # 从请求数据中获取小说目录页URL
        catalog_url = request.data.get('catalog_url')
        # 检查URL是否提供
        if not catalog_url:
            return Response({'error': '缺少小说目录页URL'}, status=400)
        # 获取新的任务ID
        task_id = get_new_task_id()
        # 先写入初始进度，避免前端查不到
        set_spider_progress(task_id, {
            'novel_title': '',  # 小说标题（初始为空）
            'total': 0,  # 总章节数（初始为0）
            'current': 0,  # 当前进度（初始为0）
            'current_title': '',  # 当前章节标题（初始为空）
            'done': False,  # 是否完成（初始为False）
            'error': None,  # 错误信息（初始为None）
        })

        def run_spider():
            """
            内部爬虫执行函数。
            
            在新线程中执行爬虫任务，避免阻塞主线程。
            包含异常处理，确保错误信息被正确记录。
            """
            try:
                # 调用爬虫导入小说函数
                spider_import_novel(catalog_url, task_id=task_id)
            except Exception as e:
                # 如果发生异常，设置错误状态
                set_spider_progress(task_id, {
                    'novel_title': '',  # 小说标题
                    'total': 0,  # 总章节数
                    'current': 0,  # 当前进度
                    'current_title': '',  # 当前章节标题
                    'done': True,  # 标记为完成
                    'error': str(e),  # 错误信息
                })
        # 在新线程中运行爬虫，避免阻塞主线程
        threading.Thread(target=run_spider, daemon=True).start()
        # 返回成功响应和任务ID
        return Response({'success': True, 'task_id': task_id})

    def get(self, request):
        """
        处理GET请求，查询爬虫任务进度。
        
        Args:
            request: HTTP请求对象，包含任务ID查询参数
            
        Returns:
            Response: 包含爬虫进度信息的响应对象
        """
        # 从查询参数中获取任务ID
        task_id = request.query_params.get('task_id')
        # 检查任务ID是否提供
        if not task_id:
            return Response({'error': '缺少task_id'}, status=400)
        # 获取爬虫进度
        progress = get_spider_progress(task_id)
        # 检查进度是否存在
        if not progress:
            return Response({'error': '未找到该任务'}, status=404)
        # 返回进度信息
        return Response({'progress': progress})

class NovelChapterCommentViewSet(viewsets.ModelViewSet):
    """
    小说章节评论视图集，提供评论的 CRUD 操作。
    
    继承自 DRF 的 ModelViewSet，自动提供标准的增删改查接口。
    支持用户创建评论，自动设置用户为当前用户。
    使用自定义权限类，确保用户只能删除自己的评论，管理员可以管理所有评论。
    列表接口支持按 chapter 查询参数过滤，只返回该章节下的评论。
    
    Attributes:
        queryset: 查询集对象
        serializer_class: 使用的序列化器类
        permission_classes: 权限控制类列表
    """
    # 默认查询集（get_queryset 会按 chapter 过滤）
    queryset = NovelChapterComment.objects.all().order_by('-created_at')
    # 指定序列化器
    serializer_class = NovelChapterCommentSerializer

    def get_queryset(self):
        """
        获取查询集，支持按章节过滤。
        若 URL 参数包含 chapter，则只返回该章节下的评论；否则返回全部。
        """
        qs = NovelChapterComment.objects.all().order_by('-created_at')
        chapter_id = self.request.query_params.get('chapter')
        if chapter_id:
            qs = qs.filter(chapter_id=chapter_id)
        return qs
    # 设置权限：登录用户可写，未登录只读，且只能操作自己的内容或管理员可操作所有
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaff]

    def perform_create(self, serializer):
        """
        重写创建方法，自动设置评论用户为当前用户。
        
        Args:
            serializer: 评论序列化器实例
        """
        # 创建评论时自动设置用户为当前用户
        serializer.save(user=self.request.user)

# --- Cover Image Proxy ---
class CoverProxyView(APIView):
    """
    封面图片代理视图，用于绕过图片防盗链。
    
    继承自 DRF 的 APIView，接收图片URL参数，模拟浏览器请求获取图片，
    然后返回图片内容。主要用于解决小说封面图片的防盗链问题。
    
    Attributes:
        permission_classes: 权限控制类列表（为空，允许任何人访问）
    """
    # 设置权限：任何人可访问
    permission_classes = []

    def get(self, request):
        """
        处理GET请求，代理获取图片内容。
        
        Args:
            request: HTTP请求对象，包含图片URL查询参数
            
        Returns:
            HttpResponse: 包含图片内容的响应对象，或错误信息
        """
        # 从查询参数中获取图片URL
        img_url = request.query_params.get('url')
        # 检查URL是否提供
        if not img_url:
            return Response({'error': 'missing url'}, status=400)
        try:
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',  # 用户代理
                'Referer': 'https://m.wenkuchina.com/'  # 引用页
            }
            # 发送GET请求获取图片
            resp = requests.get(img_url, headers=headers, timeout=15, stream=True)
            # 检查响应状态
            resp.raise_for_status()
            # 获取内容类型
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            # 若返回的并非图片而是 html，则说明目标站点仍做了防盗链，直接 404
            if 'text/html' in content_type:
                return Response({'error': 'blocked by source'}, status=502)
            # 返回图片内容
            return HttpResponse(resp.raw.read(), content_type=content_type)
        except Exception as e:
            # 发生异常时返回错误信息
            return Response({'error': str(e)}, status=502)


class FileUploadView(APIView):
    """
    文件上传视图，提供文件上传功能。
    
    继承自 DRF 的 APIView，支持文件上传，自动生成唯一文件名。
    豁免CSRF检查以支持文件上传请求。
    
    Attributes:
        permission_classes: 权限控制类列表
    """
    # 设置权限：允许任何人访问
    permission_classes = [permissions.AllowAny]

    @method_decorator(csrf_exempt)  # 豁免CSRF检查
    def dispatch(self, *args, **kwargs):
        """
        重写dispatch方法，豁免CSRF检查。
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            父类dispatch方法的返回值
        """
        # 调用父类的dispatch方法
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        处理POST请求，上传文件。
        
        Args:
            request: HTTP请求对象，包含上传的文件
            
        Returns:
            Response: 包含文件URL的成功响应，或错误信息
        """
        # 从请求中获取上传的文件
        file_obj = request.FILES.get('file')
        # 检查文件是否提供
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)

        # 生成唯一的文件名
        ext = file_obj.name.split('.')[-1]  # 获取文件扩展名
        filename = f"{uuid.uuid4()}.{ext}"  # 使用UUID生成唯一文件名
        
        # 创建文件存储对象
        fs = FileSystemStorage()
        # 保存文件并获取文件路径
        filepath = fs.save(filename, file_obj)
        # 获取文件的URL
        file_url = fs.url(filepath)
        
        # 返回文件URL
        return Response({"url": file_url}, status=201)
