import os

import fitz  # pip install PyMuPDF


def pdf_to_images(pdf_path, output_folder, dpi=300):
    """
    将PDF转换为高质量图片
    :param pdf_path: PDF文件路径
    :param output_folder: 输出图片文件夹
    :param dpi: 输出分辨率（默认300）
    """
    try:
        # 创建输出目录
        os.makedirs(output_folder, exist_ok=True)

        # 打开PDF文件
        pdf_doc = fitz.open(pdf_path)

        # 遍历每一页
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)

            # 设置缩放矩阵（根据DPI计算）
            zoom = dpi / 72  # 72是PDF的默认DPI
            mat = fitz.Matrix(zoom, zoom)

            # 获取页面像素图
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # 保存图片
            output_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
            pix.save(output_path)

        print(f"转换完成，共生成 {len(pdf_doc)} 张图片")
        pdf_doc.close()

    except Exception as e:
        print(f"转换失败: {str(e)}")


# 使用示例
pdf_to_images(
    pdf_path="library_classification/《中国图书馆分类法》.pdf",
    output_folder="library_classification/Images",
    dpi=300  # 需要更高清晰度可以设置为600
)
