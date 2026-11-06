"""图片读取与保存相关的工具函数。"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

# 程序支持的输出格式（按扩展名判断）。
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class ImageError(Exception):
    """程序可预期的错误。

    这类错误只向用户展示一句清晰的提示，不打印 traceback，避免程序直接崩溃。
    """


def read_image(path: str | Path) -> np.ndarray:
    """读取图片，返回 OpenCV 的 BGR / BGRA / 灰度数组。

    使用 imdecode 而不是 imread，是为了兼容 Windows 下的中文路径。
    """
    path = Path(path)

    if not path.exists():
        raise ImageError(f"文件不存在: {path}")
    if not path.is_file():
        raise ImageError(f"不是文件: {path}")

    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        raise ImageError(f"文件内容为空，无法读取: {path}")

    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ImageError(f"不是有效的图片文件: {path}")
    return image
