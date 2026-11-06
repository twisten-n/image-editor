"""读取并格式化图片的基础信息。"""

from __future__ import annotations

import unicodedata
from pathlib import Path

from PIL import Image

from image_io import read_image

# Pillow 的模式名称 -> 更友好的颜色模式说明
MODE_NAMES = {
    "1": "1 位黑白",
    "L": "灰度 (L)",
    "LA": "灰度 + 透明 (LA)",
    "P": "调色板 (P)",
    "RGB": "RGB",
    "RGBA": "RGBA",
    "CMYK": "CMYK",
    "YCbCr": "YCbCr",
}


def format_size(num_bytes: int) -> str:
    """把字节数格式化成 KB 或 MB，保留 2 位小数。"""
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.2f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def get_image_info(path: str | Path) -> dict:
    """收集图片信息；文件无效时抛出 ImageError。"""
    path = Path(path)

    # 先用统一的读取函数校验文件，保证错误提示和编辑功能一致。
    read_image(path)

    with Image.open(path) as pil_image:
        width, height = pil_image.size
        mode = pil_image.mode
        image_format = pil_image.format or path.suffix.lstrip(".").upper()

    return {
        "文件名": path.name,
        "图片格式": image_format.upper(),
        "宽度和高度": f"{width} x {height} 像素",
        "颜色模式": MODE_NAMES.get(mode, mode),
        "文件大小": format_size(path.stat().st_size),
    }


def display_width(text: str) -> int:
    """估算字符串在终端里的显示宽度，中文按 2 个字符宽度计算。"""
    return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def format_info(info: dict) -> str:
    """把信息字典排版成便于阅读的多行文本。"""
    label_width = max(display_width(label) for label in info)
    lines = [
        f"{label}{' ' * (label_width - display_width(label))} : {value}"
        for label, value in info.items()
    ]
    return "\n".join(lines)
