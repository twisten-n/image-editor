"""图片编辑操作。

每个函数都接收 OpenCV 图片数组并返回新的数组，不会修改传入的原图。
参数不合法时抛出 ImageError，由命令行入口统一提示。
"""

from __future__ import annotations

import cv2
import numpy as np

from image_io import ImageError


def resize(image: np.ndarray, width: int | None = None, height: int | None = None) -> np.ndarray:
    """缩放图片；只给一个尺寸时按原比例计算另一个。"""
    if width is None and height is None:
        raise ImageError("缩放需要至少指定宽度 --width 或高度 --height")
    if width is not None and width <= 0:
        raise ImageError(f"宽度必须大于 0，收到: {width}")
    if height is not None and height <= 0:
        raise ImageError(f"高度必须大于 0，收到: {height}")

    origin_h, origin_w = image.shape[:2]
    if width is None:
        width = max(1, round(origin_w * height / origin_h))
    elif height is None:
        height = max(1, round(origin_h * width / origin_w))

    # 缩小时用 INTER_AREA 效果更好，放大时用 INTER_LINEAR。
    interpolation = cv2.INTER_AREA if width <= origin_w and height <= origin_h else cv2.INTER_LINEAR
    return cv2.resize(image, (width, height), interpolation=interpolation)


def crop(
    image: np.ndarray,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> np.ndarray:
    """按左、上、右、下坐标裁剪；right 和 bottom 不包含在裁剪区域内。"""
    height, width = image.shape[:2]
    if not (0 <= left < right <= width) or not (0 <= top < bottom <= height):
        raise ImageError(
            "裁剪区域越界，需满足 "
            f"0 <= left < right <= {width} 且 0 <= top < bottom <= {height}，"
            f"收到: left={left}, top={top}, right={right}, bottom={bottom}"
        )
    return image[top:bottom, left:right].copy()


def rotate(image: np.ndarray, angle: int) -> np.ndarray:
    """顺时针旋转 90、180 或 270 度。"""
    if angle not in (90, 180, 270):
        raise ImageError(f"旋转角度只支持 90、180、270 度，收到: {angle}")

    if angle == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)


def flip(image: np.ndarray, direction: str) -> np.ndarray:
    """水平或垂直翻转。"""
    if direction == "horizontal":
        return cv2.flip(image, 1)
    if direction == "vertical":
        return cv2.flip(image, 0)
    raise ImageError(f"翻转方向只支持 horizontal 或 vertical，收到: {direction}")


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """把彩色图转换成灰度图；已经是灰度图时原样返回副本。"""
    if image.ndim == 2:
        return image.copy()
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

