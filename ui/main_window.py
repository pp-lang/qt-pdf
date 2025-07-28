import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QHBoxLayout, QScrollArea, QLineEdit, QFrame, QMessageBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings
from ui.widgets.file_card import FileCard
from ui.widgets.card_container import CardContainer

from pdf_utils import merge_pdfs, split_pdf

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF工具")
        self.setAcceptDrops(True)
        self.resize(1000, 700)
        self.setStyleSheet("background-color: white;")
        self.settings = QSettings("MyCompany", "PDFTool")
        self.save_dir = self.settings.value("save_dir", os.path.join(os.getcwd(), "files"))

        self.mode = "merge"
        self.files = []

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 左侧区域
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #F5F5FA;")  # 浅灰色背景
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)
        left_widget.setLayout(left_layout)

        self.tab_widget = QTabWidget()
        tab1 = QWidget()
        tab1.setFixedHeight(50)  # 根据实际需要调整高度
        tab2 = QWidget()
        tab2.setFixedHeight(50)
        self.tab_widget.addTab(tab1, "合并 PDF")
        self.tab_widget.addTab(tab2, "拆分 PDF")
        self.tab_widget.setStyleSheet("""
             QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                min-width: 100px;
                min-height: 40px;
                font-size: 16px;
                border-radius: 5px 5px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #e53935;
                color: white;
            }
            QTabBar::tab:!selected {
                background: #f0f0f0;
                color: #333;
            }
        """)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        left_layout.addWidget(self.tab_widget)

        # 上传区域容器
        upload_container = QWidget()
        upload_layout = QHBoxLayout()
        upload_layout.setContentsMargins(0, 0, 0, 0)
        upload_layout.setSpacing(0)

        # 大红按钮
        self.upload_btn = QPushButton("选择 PDF 文件\n或拖拽到此处")
        self.upload_btn.setFixedHeight(150)
        self.upload_btn.setMinimumWidth(400)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background:#e53935; 
                color:white; 
                font-size:20px; 
                font-weight:bold;
                padding:40px; border-radius:15px;
                text-align: center; 
            }
            QPushButton:hover {
                background:#d32f2f;
            }
        """)
        self.upload_btn.setContentsMargins(0, 0, 0, 0)
        self.upload_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.upload_btn.clicked.connect(self.select_files)

        # 小红按钮（默认隐藏）
        self.add_file_btn = QPushButton("添加文件")
        self.add_file_btn.setFixedSize(100, 40)
        self.add_file_btn.setStyleSheet("""
            QPushButton {
                background:#e53935; color:white; font-size:16px; font-weight:bold;
                border:none; border-radius:8px;
            }
            QPushButton:hover {
                background:#d32f2f;
            }
        """)
        self.add_file_btn.clicked.connect(self.select_files)
        self.add_file_btn.hide()  # 默认隐藏

        upload_layout.addWidget(self.upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(self.add_file_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        upload_container.setLayout(upload_layout)
        left_layout.addWidget(upload_container)

        self.card_container = CardContainer()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.card_container)

        left_layout.addWidget(scroll_area, stretch=1)

        main_layout.addWidget(left_widget)

        # 右侧区域
        right_widget = QWidget()
        right_widget.setFixedWidth(400)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)
        right_widget.setLayout(right_layout)

        path_layout = QVBoxLayout()
        label_container = QWidget()
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(8)  # 文字和按钮之间的间距
        label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        label = QLabel("文件保存位置")
        label.setStyleSheet("font-size:14px; color:#333;")

        open_folder_btn = QPushButton("打开")
        open_folder_btn.setStyleSheet("""
            QPushButton {
                color: #1a73e8;
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        open_folder_btn.clicked.connect(self.open_file_location)

        label_layout.addWidget(label,0)
        label_layout.addWidget(open_folder_btn,0)
        label_container.setLayout(label_layout)
        path_layout.addWidget(label_container)

        path_box = QHBoxLayout()
        self.path_input = QLineEdit(self.save_dir)
        self.path_input.setReadOnly(True)
        self.path_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #333;
                background: #fff;
            }
        """)

        choose_path_btn = QPushButton("更改")
        choose_path_btn.setStyleSheet("""
            QPushButton {
                color: #1a73e8;
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 0 8px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        choose_path_btn.clicked.connect(self.choose_save_dir)

        path_box.addWidget(self.path_input, 1)
        path_box.addWidget(choose_path_btn)
        path_layout.addLayout(path_box)

        right_layout.addLayout(path_layout)

        # 文件名输入
        filename_layout = QVBoxLayout()
        filename_label = QLabel("输出文件名")
        filename_label.setStyleSheet("font-size:14px; color:#333; margin-top:10px;")
        filename_layout.addWidget(filename_label)

        self.filename_input = QLineEdit("merged.pdf")
        self.filename_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #333;
                background: #fff;
            }
        """)
        filename_layout.addWidget(self.filename_input)

        right_layout.addLayout(filename_layout)

        right_layout.addStretch()
        self.action_btn = QPushButton("合并 PDF")
        self.action_btn.setStyleSheet("background:#e53935; color:white; font-size:18px; margin-top:20px;padding:15px; border-radius:10px;")
        self.action_btn.clicked.connect(self.process)
        right_layout.addWidget(self.action_btn)

        main_layout.addWidget(right_widget)

    def open_file_location(self):
        output_dir = self.path_input.text()
        if not os.path.exists(output_dir):
            QMessageBox.warning(self, "提示", "文件保存目录不存在")
            return

        import subprocess, platform
        if platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", output_dir])
        else:  # Linux
            subprocess.run(["xdg-open", output_dir])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
        if files:
            if self.mode == "split":
                files = [files[0]]
            self.add_files(files)

    def on_tab_changed(self, index):
        self.mode = "merge" if index == 0 else "split"
        self.action_btn.setText("合并 PDF" if self.mode == "merge" else "拆分 PDF")
        self.clear_files()
        if self.mode == "merge":
            self.add_file_btn.show()
        else:
            self.add_file_btn.hide()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择 PDF 文件", "", "PDF Files (*.pdf)")
        if files:
            if self.mode == "split":
                files = [files[0]]
            self.add_files(files)

    def add_files(self, file_list):
        if self.mode == "split":
            self.clear_files()
        for f in file_list:
            if f not in self.files:
                self.files.append(f)
                card = FileCard(f, self.remove_file)
                self.card_container.add_card(card)
        self.upload_btn.setVisible(len(self.files) == 0)
        if self.mode == "merge":
            self.add_file_btn.setVisible(len(self.files) > 0)

    def remove_file(self, card):
        # 从容器列表中移除
        if card in self.card_container.cards:
            self.card_container.cards.remove(card)

        # 从文件列表中移除
        if card.pdf_path in self.files:
            self.files.remove(card.pdf_path)

        # 从布局中移除
        layout = self.card_container.grid_layout
        layout.removeWidget(card)

        # 彻底删除控件
        card.setParent(None)  # 这一步非常重要
        card.deleteLater()

        # 重新布局
        self.upload_btn.setVisible(len(self.files) == 0)
        if self.mode == "merge":
            self.add_file_btn.setVisible(len(self.files) > 0)
        self.card_container.relayout()
        self.card_container.update()  # 强制重绘

    def clear_files(self):
        # 清空 CardContainer 的卡片列表和布局
        self.card_container.clear_cards()
        # 清空 MainWindow 的文件记录
        self.files.clear()
        self.upload_btn.setVisible(len(self.files) == 0)
        self.add_file_btn.hide()
        self.card_container.relayout()
        self.card_container.update()  # 强制重绘

    def choose_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.path_input.setText(dir_path)
            self.settings.setValue("save_dir", dir_path)

    def process(self):
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加 PDF 文件")
            return

        output_dir = self.path_input.text()
        os.makedirs(output_dir, exist_ok=True)

        if self.mode == "merge":
            filename = self.filename_input.text().strip() or "merged.pdf"
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            out_file = os.path.join(output_dir, filename)

            merge_pdfs(self.files, out_file)
            QMessageBox.information(self, "完成", f"文件已合并为{filename}")
        else:
            split_pdf(self.files[0], output_dir)
            QMessageBox.information(self, "完成", f"文件已拆分至：\n{output_dir}")




