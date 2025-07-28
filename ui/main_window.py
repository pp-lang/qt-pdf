import os
import platform
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QHBoxLayout, QScrollArea, QLineEdit, QFrame, QMessageBox, QTabWidget,
    QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QSettings
from ui.widgets.file_card import FileCard
from ui.widgets.card_container import CardContainer
from pdf_utils import merge_pdfs
import fitz  # PyMuPDF


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
        self.tab_widget.addTab(QWidget(), "合并 PDF")
        self.tab_widget.addTab(QWidget(), "拆分 PDF")
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
        self.upload_btn.setMinimumWidth(500)
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
        self.upload_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.upload_btn.clicked.connect(self.select_files)

        # 小红按钮（默认隐藏）
        self.add_file_btn = QPushButton("添加文件")
        self.add_file_btn.setFixedSize(120, 40)
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

        # 文件保存位置
        path_layout = QVBoxLayout()
        label_container = QWidget()
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(8)
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

        label_layout.addWidget(label)
        label_layout.addWidget(open_folder_btn)
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

        # 文件名输入（仅合并模式可见）
        self.filename_label = QLabel("输出文件名")
        self.filename_label.setStyleSheet("font-size:14px; color:#333; margin-top:10px;")
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
        right_layout.addWidget(self.filename_label)
        right_layout.addWidget(self.filename_input)

        # 拆分模式（默认隐藏）
        self.split_mode_label = QLabel("拆分模式")
        self.split_mode_label.setStyleSheet("font-size:14px; color:#333;")
        self.split_mode_combo = QComboBox()
        self.split_mode_combo.addItems(["每页拆分", "按步长拆分", "自定义范围"])
        self.split_mode_combo.currentIndexChanged.connect(self.on_split_mode_changed)
        self.step_input = QLineEdit()
        self.step_input.setPlaceholderText("步长，如 2")
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("范围，如 1-2,4-6")
        self.split_mode_label.hide()
        self.split_mode_combo.hide()
        self.step_input.hide()
        self.range_input.hide()
        right_layout.addWidget(self.split_mode_label)
        right_layout.addWidget(self.split_mode_combo)
        right_layout.addWidget(self.step_input)
        right_layout.addWidget(self.range_input)

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
        if platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Darwin":
            subprocess.run(["open", output_dir])
        else:
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
            self.filename_label.show()
            self.filename_input.show()
            self.split_mode_label.hide()
            self.split_mode_combo.hide()
            self.step_input.hide()
            self.range_input.hide()
        else:
            self.add_file_btn.hide()
            self.filename_label.hide()
            self.filename_input.hide()
            self.split_mode_label.show()
            self.split_mode_combo.show()

    def on_split_mode_changed(self, index):
        self.step_input.setVisible(index == 1)
        self.range_input.setVisible(index == 2)

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
                self.card_container.add_card(FileCard(f, self.remove_file))
        self.upload_btn.setVisible(len(self.files) == 0)
        if self.mode == "merge":
            self.add_file_btn.setVisible(len(self.files) > 0)

    def remove_file(self, card):
        if card in self.card_container.cards:
            self.card_container.cards.remove(card)
        if card.pdf_path in self.files:
            self.files.remove(card.pdf_path)
        self.card_container.grid_layout.removeWidget(card)
        card.setParent(None)
        card.deleteLater()
        self.upload_btn.setVisible(len(self.files) == 0)
        if self.mode == "merge":
            self.add_file_btn.setVisible(len(self.files) > 0)
        self.card_container.relayout()
        self.card_container.update()

    def clear_files(self):
        self.card_container.clear_cards()
        self.files.clear()
        self.upload_btn.setVisible(True)
        self.add_file_btn.hide()
        self.card_container.relayout()
        self.card_container.update()

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
            QMessageBox.information(self, "完成", f"文件已合并为 {filename}")
        else:
            pdf_path = self.files[0]
            mode = self.split_mode_combo.currentIndex()
            if mode == 0:
                self.split_by_page(pdf_path, output_dir)
            elif mode == 1:
                step = int(self.step_input.text().strip() or 1)
                self.split_by_step(pdf_path, output_dir, step)
            elif mode == 2:
                ranges = self.range_input.text().strip()
                self.split_by_custom_ranges(pdf_path, output_dir, ranges)
            QMessageBox.information(self, "完成", f"文件已拆分至：{output_dir}")

    def split_by_page(self, pdf_path, output_dir):
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            new_doc.save(os.path.join(output_dir, f"page_{i + 1}.pdf"))
            new_doc.close()
        doc.close()

    def split_by_step(self, pdf_path, output_dir, step):
        doc = fitz.open(pdf_path)
        total = len(doc)
        for start in range(0, total, step):
            end = min(start + step - 1, total - 1)
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)
            new_doc.save(os.path.join(output_dir, f"pages_{start + 1}-{end + 1}.pdf"))
            new_doc.close()
        doc.close()

    def split_by_custom_ranges(self, pdf_path, output_dir, ranges):
        doc = fitz.open(pdf_path)
        for r in ranges.split(","):
            if "-" in r:
                start, end = map(int, r.split("-"))
            else:
                start = end = int(r)
            start -= 1
            end -= 1
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)
            new_doc.save(os.path.join(output_dir, f"pages_{start + 1}-{end + 1}.pdf"))
            new_doc.close()
        doc.close()
