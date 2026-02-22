
# 导入 requests 库，用于发送 HTTP 请求
import requests
# 导入 BeautifulSoup，用于解析 HTML
from bs4 import BeautifulSoup
# 导入小说相关模型
from .models import NovelCategory, Novel, NovelChapter
# 导入事务管理装饰器
from django.db import transaction
# 导入正则表达式模块
import re
# 导入 urljoin，用于拼接 URL
from urllib.parse import urljoin
# 导入线程模块
import threading
# 导入 uuid，用于生成唯一任务ID
import uuid
# 导入 base64，用于解码部分站点通过 JS 注入的正文（如 biquke.vip 的 qsbs.bb）
import base64


# =========================
# 通用 & 可配置的站点规则
# =========================

# 默认的通用规则，适配大部分中文小说网站
DEFAULT_SITE_CONFIG = {
    # 小说标题相关
    "title_meta_property": "og:title",
    "title_selectors": ["h1", ".book-title", ".novel-title", "title"],

    # 分类
    "default_category": "网络小说",

    # 封面相关（笔趣阁等站点封面在 #fmimg 内：<img src="/img/21574.jpg" ...>）
    "cover_meta_property": "og:image",
    "cover_selectors": [
        "#fmimg img",
        "#sidebar img",
        "img.cover",
        ".book-cover img",
        ".novel-cover img",
        "img.book-cover",
    ],

    # 章节链接提取规则
    # - href 里包含这些关键词之一，或
    # - 文本看起来像 “第xx章/回/节”
    "chapter_href_keywords": ["chapter", "chap", "book", "novel", "read", "article"],
    # 需要排除的链接关键词（目录、首页等）
    "chapter_href_exclude_keywords": ["index", "all-chapters", "catalog", "list", "contents"],
    # href 需要匹配的正则（任一满足即可）
    "chapter_href_patterns": [
        r"/\d+/\d+\.html",
        r"/chapter/\d+",
        r"/read/\d+",
        r"\d+\.html$",
    ],

    # 正文内容选择器优先级（从上到下依次尝试）
    "content_selectors": [
        "#acontent",
        "div#content",
        "div.content-body",
        "div.read-content",
        "div.chapter-content",
        "div.content",
        "div.novel-content",
        "div.article-content",
    ],
    # 在正文容器内部，哪些标签视为段落
    "content_paragraph_tags": ["p", "div"],

    # 下一页（分页）链接识别
    "next_page_text_keywords": ["下一页", "下一章", "下页", "Next", "NEXT", "next"],
    # rel 属性为 next 的 a 标签
    "next_page_rel_values": ["next"],
}


# 全局进度存储（内存，线程安全）
_spider_progress = {}  # 存储爬虫任务进度
_spider_progress_lock = threading.Lock()  # 线程锁，保证多线程安全

# 全局取消任务标记（内存，线程安全）
_spider_cancelled = set()  # 被请求停止的任务ID集合
_spider_cancel_lock = threading.Lock()


# 生成新的唯一任务ID
def get_new_task_id():
    return uuid.uuid4().hex


# 设置指定任务的进度信息
def set_spider_progress(task_id, progress):
    with _spider_progress_lock:
        _spider_progress[task_id] = progress.copy()


# 获取指定任务的进度信息
def get_spider_progress(task_id):
    with _spider_progress_lock:
        return _spider_progress.get(task_id, None)


def cancel_spider_task(task_id):
    """
    标记指定task_id的爬虫任务为“已取消”。
    只是在内存中打标记，真正的停止动作由 spider_import_novel 在循环中检查并提前退出。
    """
    with _spider_cancel_lock:
        _spider_cancelled.add(task_id)


def is_spider_cancelled(task_id):
    """
    查询某个任务是否被请求取消。
    """
    with _spider_cancel_lock:
        return task_id in _spider_cancelled


# 获取网页内容，带重试机制
def fetch_page_content(url, retries=3, delay=5):
    # 尝试多次请求网页，防止偶发网络错误
    for i in range(retries):
        try:
            # 部分站点（如 biquke.vip）PC 端正文通过 JS 加密，手机站是纯 HTML。
            # 这里自动把 www.biquke.vip 切到 m.biquke.vip，提升抓取成功率。
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                # 仅对 biquke 的「章节页」做 PC -> H5 的转换；目录页保留 PC 以正确解析封面 #fmimg
                if parsed.netloc == "www.biquke.vip" and re.search(r"^/book/\d+/\d+.*\.html", parsed.path):
                    mobile_url = parsed._replace(scheme="http", netloc="m.biquke.vip").geturl()
                    print("切换到手机版 URL：", mobile_url)
                    url = mobile_url
            except Exception:
                # 解析失败则忽略，继续用原始 URL
                pass
            # 构造请求头，模拟浏览器访问，防止被反爬
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                # Referer 使用当前站点根域名，更像正常访问
                'Referer': f'{url.split("/book/")[0]}/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
            }
            # 发送 GET 请求获取网页内容
            response = requests.get(url, headers=headers, timeout=15)
            print("正在访问：", url, "状态码：", response.status_code)
            # 检查响应状态码，非 2xx 会抛出异常
            response.raise_for_status()
            # 设置正确的编码，防止中文乱码
            response.encoding = response.apparent_encoding or 'utf-8'
            # 返回网页源码
            return response.text
        except Exception as e:
            # 最后一次重试仍失败则抛出异常
            if i == retries - 1:
                raise
    # 所有重试都失败，返回 None
    return None

def _looks_like_chapter_text(text: str) -> bool:
    """
    判断一个文本是否像“章节标题”，对大部分中文小说网站比较通用。
    """
    if not text:
        return False
    # 常见章节命名：第xx章 / 第xx回 / 第xx节 等
    if re.search(r"第.{0,10}[章回节卷]", text):
        return True
    # 英文/数字章节，如 Chapter 1, Ch.01 等
    if re.search(r"(chapter|chap\.?|ch\.)\s*\d+", text, re.IGNORECASE):
        return True
    # 兜底：长度适中且不是导航类文案
    if 2 <= len(text) <= 40 and not any(k in text for k in ["首页", "目录", "上一页", "下一页", "尾页", "返回"]):
        return True
    return False


def _match_href_patterns(href: str, patterns):
    for p in patterns:
        if re.search(p, href):
            return True
    return False


def parse_catalog_page(html_content, catalog_url, site_config=None):
    """
    解析目录页：
    - 尽量使用通用规则
    - 若传入 site_config，可覆盖默认规则，以适配特定网站
    """
    cfg = {**DEFAULT_SITE_CONFIG, **(site_config or {})}
    # 保存目录页源码以便调试
    with open('/tmp/catalog_debug.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    soup = BeautifulSoup(html_content, 'html.parser')

    # 优先从 meta 标签获取标题
    meta_selector = f'meta[property="{cfg["title_meta_property"]}"]'
    og_title = soup.select_one(meta_selector)
    novel_title = None
    if og_title and og_title.get('content'):
        novel_title = og_title['content'].strip()
    # 备用方案：按配置的选择器顺序尝试
    if not novel_title:
        for sel in cfg["title_selectors"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    novel_title = text.split('_')[0].split('-')[0]
                    break
    if not novel_title:
        novel_title = '未知小说'

    # 分类：目前通用场景很难稳定获取，先使用默认分类或配置分类
    category = cfg.get("default_category", "网络小说")

    # 优先从 meta 标签获取封面
    cover_url = ""
    cover_meta_selector = f'meta[property="{cfg["cover_meta_property"]}"]'
    og_image = soup.select_one(cover_meta_selector)
    if og_image and og_image.get('content'):
        cover_url = og_image['content']
    else:
        # 备用方案：按配置的封面选择器顺序尝试
        for sel in cfg["cover_selectors"]:
            cover = soup.select_one(sel)
            if cover and cover.get('src'):
                cover_url = cover.get('src')
                break

    # 站点自带的“无封面”图不当作有效封面
    if cover_url and "nocover" in cover_url.lower():
        cover_url = ""

    # 确保 cover_url 是完整的绝对路径
    if cover_url and not cover_url.startswith('http'):
        cover_url = urljoin(catalog_url, cover_url)

    # 笔趣阁等：若上面未取到，直接从页面找 /img/数字.jpg 的封面图（PC 目录页 #fmimg 内）
    if not cover_url and "biquke.vip" in catalog_url:
        for img in soup.find_all("img", src=True):
            src = (img.get("src") or "").strip()
            if re.search(r"/img/\d+\.jpg", src) and "nocover" not in src.lower():
                cover_url = urljoin(catalog_url, src)
                break

    # 若依旧无法获得封面，随机生成占位图
    if not cover_url:
        import random, uuid
        seed = uuid.uuid4().hex[:8]
        cover_url = f"https://picsum.photos/seed/{seed}/400/560"

    print("爬取结果 ->", f"标题: {novel_title}", f"封面URL: {cover_url}")

    # 更通用的章节链接提取
    links = soup.find_all('a', href=True)
    chapters = []
    seen = set()
    from urllib.parse import urlparse
    parsed_catalog = urlparse(catalog_url)
    base_site = f"{parsed_catalog.scheme}://{parsed_catalog.netloc}"

    # 针对 biquke 等站点，从目录 URL 中提取本书前缀 /book/<id>/，用于过滤其它无关链接
    book_prefix = None
    if "biquke.vip" in catalog_url:
        m = re.search(r"(/book/\d+/)", catalog_url)
        if m:
            book_prefix = m.group(1)

    bad_title_keywords = ["首页", "目录", "上一页", "下一页", "尾页", "返回", "书架", "书库", "列表", "手机阅读"]

    def _link_text_looks_like_url(t: str) -> bool:
        """排除链接文字本身就是网址的情况，避免把目录页 URL 当成章节名（PC 端不需要）"""
        if not t or len(t) > 400:
            return False
        t = t.strip()
        if re.match(r"^\s*https?://\S+", t):
            return True
        if re.search(r"\.(vip|com|cn|net)/", t) and re.search(r"[\w.-]+\.(vip|com|cn|net)", t):
            return True
        return False

    for idx, link in enumerate(links):
        href = link.get('href', '').strip()
        text = link.get_text(strip=True)
        if not href or not text:
            continue

        # 链接文字是网址的不要当章节（PC 端不展示手机阅读/网址信息）
        if _link_text_looks_like_url(text):
            continue

        # 文本中包含明显的导航/翻页关键字，直接排除
        if any(bad in text for bad in bad_title_keywords):
            continue

        # 如果当前目录 URL 带有 /book/<id>/，则只保留同一本书下的章节链接
        if book_prefix and book_prefix not in href:
            continue

        # 排除明显不是章节的链接（路径关键词）
        if any(bad in href for bad in cfg["chapter_href_exclude_keywords"]):
            continue

        looks_like_chapter = _looks_like_chapter_text(text)
        href_keyword_hit = any(k in href for k in cfg["chapter_href_keywords"])
        href_pattern_hit = _match_href_patterns(href, cfg["chapter_href_patterns"])

        # 三者中任意两者命中，认为是章节链接；或 href_pattern 本身命中即可
        score = sum([looks_like_chapter, href_keyword_hit, href_pattern_hit])
        if not (href_pattern_hit or score >= 2):
            continue

        if href in seen:
            continue
        seen.add(href)

        # 规范化为绝对 URL
        if not href.startswith("http"):
            if href.startswith("/"):
                href = urljoin(base_site, href)
            else:
                href = urljoin(catalog_url, href)

        chapters.append({"title": text, "url": href})

    # 对部分站点（如 biquke.vip），根据 URL 中的章节ID进行排序，确保从第1章开始
    def _chapter_order(chap):
        m2 = re.search(r"/book/(\d+)/(\d+)", chap["url"])
        if m2:
            # 返回 (书ID, 章节ID)，以支持不同书籍时也有稳定顺序
            return int(m2.group(1)), int(m2.group(2))
        return (0, 0)

    if "biquke.vip" in catalog_url and chapters:
        chapters.sort(key=_chapter_order)

    return novel_title, category, cover_url, chapters

def _clean_chapter_text(text: str, page_url: str | None = None) -> str:
    """
    对章节正文做一些站点相关的清洗，去掉版权声明、站点导航等噪声。
    目前仅对部分已知站点（如 biquke.vip）做定制清洗。
    """
    if not text:
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # 通用：去掉整行是网址的行（PC 端不展示网址信息）
    lines = [ln for ln in lines if not re.match(r"^\s*https?://\S+\s*$", ln)]

    # 针对 biquke.vip 去掉站点说明、手机阅读、网址、推荐、侵权等（只保留正文，PC 端用）
    if page_url and "biquke.vip" in page_url:
        blacklist = [
            "字体默认", "请勿开启浏览器阅读模式", "一页目录下一页", "一页目录下一页一秒记住域名",
            "书架阅读记录网址地图", "笔趣阁", "Copyright", "本站所有小说为转载作品",
            "手机阅读", "电脑阅读", "手机版", "电脑版", "推荐到QQ", "推荐到微博", "推荐阅读",
            "侵权", "联系邮箱", "48小时", "网址地图", "一秒记住",
        ]
        cleaned = [ln for ln in lines if not any(b in ln for b in blacklist)]
        if cleaned:
            lines = cleaned

    return "\n".join(lines)


def parse_chapter_content(html_content, site_config=None, page_url=None):
    cfg = {**DEFAULT_SITE_CONFIG, **(site_config or {})}

    # 特殊处理：部分站点（如 biquke.vip）正文通过 JS + base64 注入：
    # <script>document.writeln(qsbs.bb('BASE64...'));</script>
    # 这里直接把这些 BASE64 片段解码成 HTML 再解析，比执行 JS 简单也更稳定。
    if "qsbs.bb('" in html_content:
        try:
            encoded_list = re.findall(r"qsbs\.bb\('([^']+)'\)", html_content)
            decoded_html_parts = []
            for enc in encoded_list:
                try:
                    decoded = base64.b64decode(enc).decode('utf-8', errors='ignore')
                    decoded_html_parts.append(decoded)
                except Exception:
                    continue
            if decoded_html_parts:
                merged_html = "".join(decoded_html_parts)
                soup = BeautifulSoup(merged_html, 'html.parser')
                paragraphs = soup.find_all('p')
                text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                cleaned = _clean_chapter_text(text, page_url=page_url)
                print("（JS解码）正文内容前100字：", cleaned[:100])
                return cleaned.strip()
        except Exception:
            # 解码失败则退回到常规解析逻辑
            pass

    soup = BeautifulSoup(html_content, 'html.parser')
    # 1. 优先提取 #acontent（部分站点专门用于正文）
    acontent = soup.select_one('#acontent')
    if acontent:
        # 先尝试按段落标签提取
        parts = [p.get_text(strip=True) for p in acontent.find_all(['p', 'div']) if p.get_text(strip=True)]
        if not parts:
            # 如果内部主要是 <br> + 文本，则直接取整个容器的纯文本
            text = acontent.get_text(separator='\n', strip=True)
        else:
            text = '\n'.join(parts)
        cleaned = _clean_chapter_text(text, page_url=page_url)
        print("正文内容前100字：", cleaned[:100])
        return cleaned.strip()

    # 2. 其他常见内容 div
    content_div = soup.select_one('div.content-body, div.read-content, div.chapter-content, div.content, div.novel-content, div#content, div.article-content')
    if content_div:
        # 先尝试按段落标签提取
        parts = [p.get_text(strip=True) for p in content_div.find_all(['p', 'div']) if p.get_text(strip=True)]
        if not parts:
            # 很多小说站正文是“纯文本 + <br> 换行”，没有 <p> 标签，这里直接抓取整个容器文本
            text = content_div.get_text(separator='\n', strip=True)
        else:
            text = '\n'.join(parts)
        cleaned = _clean_chapter_text(text, page_url=page_url)
        print("正文内容前100字：", cleaned[:100])
        return cleaned.strip()
    # 3. 所有段落
    paragraphs = soup.find_all('p')
    if paragraphs:
        text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        cleaned = _clean_chapter_text(text, page_url=page_url)
        print("正文内容前100字：", cleaned[:100])
        return cleaned.strip()
    # 4. 兜底
    body = soup.body
    if body:
        text = body.get_text(separator='\n', strip=True)
        cleaned = _clean_chapter_text(text, page_url=page_url)
        print("正文内容前100字：", cleaned[:100])
        return cleaned.strip()
    text = soup.get_text(separator='\n', strip=True)
    cleaned = _clean_chapter_text(text, page_url=page_url)
    print("正文内容前100字：", cleaned[:100])
    return cleaned.strip()

def get_next_page_url(soup, current_url, site_config=None):
    """
    更通用的下一页/下一章检测：
    - 文本含配置关键词（默认：下一章/下一页/Next）
    - rel=next
    - class 名包含 next
    """
    cfg = {**DEFAULT_SITE_CONFIG, **(site_config or {})}
    keywords = cfg.get("next_page_text_keywords", [])
    rel_values = set(cfg.get("next_page_rel_values", []))

    # 针对 biquke 等站点，抽取当前书本的 /book/<book_id>/ 前缀，用于过滤“书架”等其它链接
    book_prefix = None
    m = re.search(r"(/book/\d+/)", current_url)
    if m:
        book_prefix = m.group(1)

    def _is_next_link(a_tag):
        href = a_tag.get("href", "")
        text = a_tag.get_text(strip=True)
        cls = " ".join(a_tag.get("class", []))
        rel = set(a_tag.get("rel", []))

        # biquke 等小说站：防止把“返回书架”等链接当成下一页
        # 若当前页属于某本书（/book/<id>/），则只接受同一本书下的链接
        if "biquke.vip" in current_url and book_prefix:
            if book_prefix not in href:
                return False

        if any(k in text for k in keywords):
            return True
        if rel_values & rel:
            return True
        if "next" in cls.lower():
            return True
        # 有些站分页用 _数字.html 追加，比如 13211050_1.html
        if re.search(r"_\d+\.html?$", href):
            return True
        return False

    for a in soup.find_all("a", href=True):
        if not _is_next_link(a):
            continue
        href = a["href"].strip()
        if not href:
            continue
        if not href.startswith("http"):
            href = urljoin(current_url, href)
        if href != current_url:
            return href
    return None



# 递归/迭代抓取章节的所有分页内容，并合并返回
def fetch_full_chapter_content(first_page_url, max_pages=30, site_config=None):
    """
    传入章节第一页的URL，自动抓取后续所有分页内容，拼接成完整章节文本。
    :param first_page_url: 章节第一页的URL
    :param max_pages: 最多抓取多少页，防止死循环
    :return: 合并后的完整章节内容字符串
    """
    combined = []  # 用于存放每一页的正文内容
    visited = set()  # 记录已访问过的URL，防止重复和死循环
    current_url = first_page_url  # 当前要抓取的页面URL

    # 对部分站点（如 biquke.vip），需要区分「同一章节的分页」与「下一章节」：
    # /book/26467/13211050.html       -> 第1章 第1页
    # /book/26467/13211050_1.html     -> 第1章 第2页
    # /book/26467/13211051.html       -> 第2章 第1页
    # 我们只想在本函数中合并同一章节的分页，不应把 13211051.html 拼到上一章里。
    from urllib.parse import urlparse

    parsed_first = urlparse(first_page_url)
    first_book_id = None
    first_chapter_id = None
    if "biquke.vip" in parsed_first.netloc:
        m = re.match(r"^/book/(\d+)/(\d+)(?:_\d+)?\.html", parsed_first.path)
        if m:
            first_book_id = int(m.group(1))
            first_chapter_id = int(m.group(2))

    def _is_same_chapter(next_url: str) -> bool:
        """仅在 biquke 等站上使用：判断 next_url 是否仍属于 first_page_url 的同一章节分页。"""
        nonlocal first_book_id, first_chapter_id
        if not (first_book_id and first_chapter_id):
            # 未识别出章节结构时，不做限制，一律视为同一章节，由调用方控制。
            return True
        p = urlparse(next_url)
        if "biquke.vip" not in p.netloc:
            return False
        m2 = re.match(r"^/book/(\d+)/(\d+)(?:_\d+)?\.html", p.path)
        if not m2:
            return False
        book_id = int(m2.group(1))
        chap_id = int(m2.group(2))
        # 必须是同一本书 & 同一个章节ID，才能视为同一章节的分页
        return book_id == first_book_id and chap_id == first_chapter_id
    for _ in range(max_pages):  # 最多抓取max_pages页，防止异常死循环
        if current_url in visited:
            break  # 如果当前URL已访问过，说明出现循环，直接跳出
        visited.add(current_url)  # 标记当前URL已访问
        html = fetch_page_content(current_url)  # 获取当前页面HTML源码
        if not html:
            break  # 如果页面获取失败，跳出循环
        combined.append(parse_chapter_content(html, site_config=site_config, page_url=current_url))  # 解析正文并加入结果列表
        soup = BeautifulSoup(html, 'html.parser')  # 解析HTML，准备查找“下一页”链接
        next_url = get_next_page_url(soup, current_url, site_config=site_config)  # 获取下一页的URL
        if not next_url:
            break  # 没有下一页，说明已到结尾，跳出

        # 若下一页不再属于同一章节（例如从 13211050_1.html 跳到 13211051.html），
        # 则在此处停止，不把下一章节内容拼接进来。
        if not _is_same_chapter(next_url):
            break

        current_url = next_url  # 进入下一页，继续循环
    # 合并所有页的正文内容，用换行符拼接
    return '\n'.join([c for c in combined if c])

@transaction.atomic  # 保证数据库操作要么全部成功要么全部失败
def spider_import_novel(catalog_url, task_id=None, site_config=None):
    # 1. 规范化目录URL：
    #    - 若传入的是具体章节页（如 /book/26467/13211050.html），自动转换为该书目录页 /book/26467/
    from urllib.parse import urlparse

    parsed = urlparse(catalog_url)
    if "biquke.vip" in parsed.netloc:
        m = re.match(r"(/book/\d+)/\d+.*\.html", parsed.path)
        if m:
            # 将 /book/26467/13211050.html -> /book/26467/
            new_path = m.group(1) + "/"
            catalog_url = parsed._replace(path=new_path, query="", fragment="").geturl()

    # 获取小说目录页的 HTML 内容
    html = fetch_page_content(catalog_url)
    # 2. 解析目录页，获取小说标题、分类、封面、章节列表
    novel_title, category_name, cover_url, chapters = parse_catalog_page(html, catalog_url, site_config=site_config)
    # 3. 获取或创建小说分类对象（如“网络小说”）
    category, _ = NovelCategory.objects.get_or_create(name=category_name)
    # 4. 获取或创建小说对象（根据标题），并更新分类和封面
    novel, created = Novel.objects.update_or_create(
        title=novel_title,
        defaults={'category': category, 'cover_url': cover_url}
    )

    # 4.1 删除已存在的「手机阅读」等非正文章节（PC 端不展示）
    NovelChapter.objects.filter(novel=novel, title="手机阅读").delete()

    # 5. 统计章节总数
    total = len(chapters)
    # 6. 如果没有传入任务ID，则生成一个新的任务ID
    if not task_id:
        task_id = get_new_task_id()
    # 7. 初始化爬虫进度（刚开始，current=0）
    set_spider_progress(task_id, {
        'novel_title': novel_title,  # 小说标题
        'total': total,              # 总章节数
        'current': 0,                # 当前已完成章节数
        'current_title': '',         # 当前正在处理的章节标题
        'done': False,               # 是否已完成
        'error': None,               # 错误信息
    })

    # 8. 遍历每个章节，依次爬取内容并保存到数据库
    for idx, chap in enumerate(chapters, 1):
        # 若该任务已被标记为取消，则优雅地中断循环，保留已保存的章节
        if is_spider_cancelled(task_id):
            set_spider_progress(task_id, {
                'novel_title': novel_title,
                'total': total,
                'current': idx - 1 if idx > 1 else 0,
                'current_title': chap['title'],
                'done': True,
                'error': '任务已被用户停止',
            })
            break
        try:
            # 8.1 爬取当前章节的全部内容（支持多页合并）
            content = fetch_full_chapter_content(chap['url'], site_config=site_config)
            # 8.2 保存或更新章节到数据库
            chapter, created = NovelChapter.objects.update_or_create(
                novel=novel,                # 所属小说
                title=chap['title'],        # 章节标题
                defaults={'content': content}  # 章节内容
            )
            # 8.3 判断是新建还是更新
            action = "创建" if created else "更新"
            # 8.4 打印日志，显示章节标题和内容长度
            print(f"  -> {action}章节： {chap['title']}，内容长度： {len(content)}")
            # 8.5 更新当前进度
            set_spider_progress(task_id, {
                'novel_title': novel_title,
                'total': total,
                'current': idx,              # 当前已完成章节数
                'current_title': chap['title'], # 当前章节标题
                'done': False,
                'error': None,
            })
        except Exception as e:
            # 8.6 如果爬取或保存出错，记录错误信息并抛出异常
            set_spider_progress(task_id, {
                'novel_title': novel_title,
                'total': total,
                'current': idx,
                'current_title': chap['title'],
                'done': False,
                'error': str(e),
            })
            raise
    # 9. 全部章节处理完毕，标记任务完成
    set_spider_progress(task_id, {
        'novel_title': novel_title,
        'total': total,
        'current': total,
        'current_title': '',
        'done': True,   # 标记已完成
        'error': None,
    })
    # 10. 返回小说标题、章节总数、任务ID
    return novel_title, total, task_id