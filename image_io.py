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


def save_image(image: np.ndarray, path: str | Path, source: str | Path) -> Path:
    """把图片保存为新文件，并返回保存路径。

    参数 source 是原图路径，用于阻止覆盖原图。
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ImageError(f"不支持保存为 {suffix or '无扩展名'} 格式，可用格式: {supported}")

    if path.resolve() == Path(source).resolve():
        raise ImageError("输出路径不能与原图相同，请换一个文件名以保护原图")

    path.parent.mkdir(parents=True, exist_ok=True)

    # JPG / BMP 不支持透明通道，带 alpha 的图必须先转成 BGR，否则保存会失败。
    if path.suffix.lower() in {".jpg", ".jpeg", ".bmp"} and image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    # 与 imread 对称，使用 imencode + tofile 兼容中文路径。
    success, buffer = cv2.imencode(suffix, image)
    if not success:
        raise ImageError(f"保存失败，无法编码为 {suffix} 格式: {path}")
    buffer.tofile(str(path))
    return path
