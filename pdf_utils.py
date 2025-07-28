import os
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger, PdfReader
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

def generate_thumbnail(pdf_path, width=140, height=180):
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # 加载第一页
        mat = fitz.Matrix(2, 2)  # 放大2倍，清晰一点
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 转成 QImage
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

        # 缩放到指定大小
        scaled = image.scaled(width, height, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qt.TransformationMode.SmoothTransformation)

        doc.close()

        return QPixmap.fromImage(scaled)

    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return None

def get_pdf_page_count(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except:
        return 0

def merge_pdfs(pdf_list, output_path):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()

def split_pdf(input_pdf, output_dir):
    reader = PdfReader(input_pdf)
    for i, page in enumerate(reader.pages):
        writer = PdfMerger()
        writer.append(input_pdf, pages=(i, i + 1))
        out_file = os.path.join(output_dir, f"page_{i + 1}.pdf")
        with open(out_file, "wb") as f:
            writer.write(f)
