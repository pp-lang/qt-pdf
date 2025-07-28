import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag
from pdf_utils import generate_thumbnail, get_pdf_page_count

class FileCard(QFrame):
    def __init__(self, pdf_path, remove_callback):
        super().__init__()
        self.pdf_path = pdf_path
        self.remove_callback = remove_callback
        self.setFixedSize(150, 220)
        self.setStyleSheet("background:white; border:none; border-radius:10px;")

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        thumbnail = generate_thumbnail(pdf_path)
        thumb_label = QLabel()
        thumb_label.setStyleSheet("border:1px solid #ddd; border-radius:5px; background:#fafafa;")
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if thumbnail:
            thumb_label.setPixmap(thumbnail.scaled(120, 150, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(thumb_label)

        name_label = QLabel(os.path.basename(pdf_path))
        name_label.setStyleSheet("font-size:12px; color:#333;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        pages = get_pdf_page_count(pdf_path)
        page_label = QLabel(f"共 {pages} 页")
        page_label.setStyleSheet("color:gray; font-size:10px;")
        layout.addWidget(page_label)

        remove_btn = QPushButton("删除")
        remove_btn.setStyleSheet("background:#ff4d4f; color:white; border:none; padding:5px; border-radius:5px;")
        remove_btn.clicked.connect(lambda: self.remove_callback(self))
        layout.addWidget(remove_btn)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.pdf_path)
            mime_data.setData("application/x-card", self.pdf_path.encode())
            drag.setMimeData(mime_data)

            # 设置拖拽时的预览图
            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            drag.exec(Qt.DropAction.MoveAction)
        else:
            super().mousePressEvent(event)
