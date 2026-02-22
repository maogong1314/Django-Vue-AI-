import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTextEdit, QLabel, QPushButton
)
from PyQt5.QtCore import Qt

API_BASE = "http://10.1.1.190:8000/api/novel/"

class NovelReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI小说管理与阅读器")
        self.setGeometry(200, 200, 900, 600)
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        self.category_list = QListWidget()
        self.novel_list = QListWidget()
        self.chapter_list = QListWidget()
        self.category_list.setFixedWidth(150)
        self.novel_list.setFixedWidth(200)
        self.chapter_list.setFixedWidth(200)

        self.category_list.itemClicked.connect(self.on_category_selected)
        self.novel_list.itemClicked.connect(self.on_novel_selected)
        self.chapter_list.itemClicked.connect(self.on_chapter_selected)

        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_categories)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("分类"))
        left_panel.addWidget(self.category_list)
        left_panel.addWidget(QLabel("小说"))
        left_panel.addWidget(self.novel_list)
        left_panel.addWidget(QLabel("章节"))
        left_panel.addWidget(self.chapter_list)
        left_panel.addWidget(self.refresh_btn)

        main_layout.addLayout(left_panel)
        main_layout.addWidget(self.content_view, stretch=1)

        self.setCentralWidget(main_widget)

    def load_categories(self):
        self.category_list.clear()
        self.novel_list.clear()
        self.chapter_list.clear()
        self.content_view.clear()
        try:
            resp = requests.get(API_BASE + "novel-categories/")
            resp.raise_for_status()
            self.categories = resp.json()
            for cat in self.categories:
                self.category_list.addItem(f"{cat['id']} - {cat['name']}")
        except Exception as e:
            self.content_view.setText(f"加载分类失败: {e}")

    def on_category_selected(self, item):
        cat_id = int(item.text().split(" - ")[0])
        self.novel_list.clear()
        self.chapter_list.clear()
        self.content_view.clear()
        try:
            resp = requests.get(API_BASE + f"novels/?category={cat_id}")
            resp.raise_for_status()
            self.novels = resp.json()
            for novel in self.novels:
                self.novel_list.addItem(f"{novel['id']} - {novel['title']}")
        except Exception as e:
            self.content_view.setText(f"加载小说失败: {e}")

    def on_novel_selected(self, item):
        novel_id = int(item.text().split(" - ")[0])
        self.chapter_list.clear()
        self.content_view.clear()
        try:
            resp = requests.get(API_BASE + f"novel-chapters/?novel={novel_id}")
            resp.raise_for_status()
            self.chapters = resp.json()
            for chap in self.chapters:
                self.chapter_list.addItem(f"{chap['id']} - {chap['title']}")
        except Exception as e:
            self.content_view.setText(f"加载章节失败: {e}")

    def on_chapter_selected(self, item):
        chap_id = int(item.text().split(" - ")[0])
        chapter = next((c for c in self.chapters if c['id'] == chap_id), None)
        if chapter:
            self.content_view.setText(chapter['content'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    reader = NovelReader()
    reader.show()
    sys.exit(app.exec_()) 