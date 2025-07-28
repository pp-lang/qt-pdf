from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QPen

class CardContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.cards = []
        self.drag_insert_index = None

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.setLayout(self.grid_layout)
        self.dragged_card = None

    def add_card(self, card):
        self.cards.append(card)
        self.relayout()

    def relayout(self):
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                self.grid_layout.removeWidget(w)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        width = self.width()
        card_width = 200
        spacing = self.grid_layout.spacing()
        columns = max(1, width // (card_width + spacing))

        for index, card in enumerate(self.cards):
            row = index // columns
            col = index % columns
            self.grid_layout.addWidget(card, row, col)

    def resizeEvent(self, event):
        self.relayout()
        super().resizeEvent(event)

    # --- 拖拽事件 ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-card"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-card"):
            pos = event.position().toPoint()
            self.handle_drop(pos)
            event.acceptProposedAction()

    def handle_drop(self, pos):
        if not self.dragged_card:
            return
        insert_index = self.get_insert_index(pos, self.dragged_card)
        if insert_index is None:
            insert_index = len(self.cards)
        self.cards.remove(self.dragged_card)
        self.cards.insert(insert_index, self.dragged_card)
        self.relayout()

    def dropEvent(self, event):
        pos = event.position().toPoint()
        pdf_path = event.mimeData().text()
        dragged_card = next((c for c in self.cards if c.pdf_path == pdf_path), None)
        if not dragged_card:
            return

        insert_index = self.get_insert_index(pos)
        if insert_index is None:
            insert_index = len(self.cards)

        # 动画移动
        self.animate_reorder(dragged_card, insert_index)
        event.acceptProposedAction()

    def get_insert_index(self, pos: QPoint):
        for i, card in enumerate(self.cards):
            rect = card.geometry()
            if pos.y() < rect.center().y():
                return i
        return None

    def animate_reorder(self, card, new_index):
        old_index = self.cards.index(card)
        if old_index == new_index:
            return

        self.cards.remove(card)
        self.cards.insert(new_index, card)

        # 先计算目标位置
        width = self.width()
        card_width = 170
        spacing = self.grid_layout.spacing()
        columns = max(1, width // (card_width + spacing))

        animations = []
        for i, c in enumerate(self.cards):
            target_row = i // columns
            target_col = i % columns
            target_pos = self.grid_layout.cellRect(target_row, target_col).topLeft()

            anim = QPropertyAnimation(c, b"geometry")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(c.geometry())
            anim.setEndValue(QRect(target_pos, c.size()))
            anim.start()
            animations.append(anim)

        # 重排布局（动画结束后）
        self.relayout()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drag_insert_index is not None and self.drag_insert_index <= len(self.cards):
            painter = QPainter(self)
            pen = QPen(Qt.GlobalColor.red, 2)
            painter.setPen(pen)
            if self.drag_insert_index < len(self.cards):
                rect = self.cards[self.drag_insert_index].geometry()
                painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
            else:
                # 最后位置
                if self.cards:
                    rect = self.cards[-1].geometry()
                    painter.drawLine(rect.right() + 10, rect.top(), rect.right() + 10, rect.bottom())

    def clear_cards(self):
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()
        self.relayout()
