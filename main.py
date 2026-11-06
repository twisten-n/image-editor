"""图片信息查看与编辑工具的命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from image_info import format_info, format_size, get_image_info
from image_io import ImageError, read_image, save_image
from image_ops import crop, flip, resize, rotate, to_grayscale


def default_output(input_path: Path, operation: str) -> Path:
    """未指定 -o 时，在原图旁边生成 xxx_操作名.扩展名 的新文件。"""
    suffix = input_path.suffix or ".png"
    return input_path.with_name(f"{input_path.stem}_{operation}{suffix}")


def report_saved(path: Path) -> None:
    print(f"已保存到: {path}（{format_size(path.stat().st_size)}）")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-editor",
        description="查看图片基础信息，并完成缩放、裁剪、旋转等简单编辑。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="查看图片基础信息")
    info_parser.add_argument("input", help="图片路径")

    resize_parser = subparsers.add_parser("resize", help="缩放图片")
    resize_parser.add_argument("input", help="图片路径")
    resize_parser.add_argument("-o", "--output", help="输出文件路径（默认在原图旁新建文件）")
    resize_parser.add_argument("--width", type=int, help="目标宽度（像素）")
    resize_parser.add_argument("--height", type=int, help="目标高度（像素）")

    crop_parser = subparsers.add_parser("crop", help="裁剪图片")
    crop_parser.add_argument("input", help="图片路径")
    crop_parser.add_argument("-o", "--output", help="输出文件路径（默认在原图旁新建文件）")
    crop_parser.add_argument("--left", type=int, required=True, help="左边界（包含）")
    crop_parser.add_argument("--top", type=int, required=True, help="上边界（包含）")
    crop_parser.add_argument("--right", type=int, required=True, help="右边界（不包含）")
    crop_parser.add_argument("--bottom", type=int, required=True, help="下边界（不包含）")

    rotate_parser = subparsers.add_parser("rotate", help="旋转图片")
    rotate_parser.add_argument("input", help="图片路径")
    rotate_parser.add_argument("-o", "--output", help="输出文件路径（默认在原图旁新建文件）")
    rotate_parser.add_argument(
        "--angle",
        type=int,
        required=True,
        choices=(90, 180, 270),
        help="顺时针旋转角度：90、180 或 270",
    )

    flip_parser = subparsers.add_parser("flip", help="翻转图片")
    flip_parser.add_argument("input", help="图片路径")
    flip_parser.add_argument("-o", "--output", help="输出文件路径（默认在原图旁新建文件）")
    flip_parser.add_argument(
        "--direction",
        required=True,
        choices=("horizontal", "vertical"),
        help="horizontal 为水平翻转，vertical 为垂直翻转",
    )

    gray_parser = subparsers.add_parser("gray", help="转换为灰度图")
    gray_parser.add_argument("input", help="图片路径")
    gray_parser.add_argument("-o", "--output", help="输出文件路径（默认在原图旁新建文件）")

    convert_parser = subparsers.add_parser("convert", help="转换图片格式")
    convert_parser.add_argument("input", help="图片路径")
    convert_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="输出文件路径，扩展名决定目标格式，例如 out.png、out.jpg",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            print(format_info(get_image_info(args.input)))
            return 0

        input_path = Path(args.input)
        image = read_image(input_path)
        output_path = Path(args.output) if args.output else default_output(input_path, args.command)

        if args.command == "resize":
            result = resize(image, width=args.width, height=args.height)
        elif args.command == "crop":
            result = crop(image, args.left, args.top, args.right, args.bottom)
        elif args.command == "rotate":
            result = rotate(image, args.angle)
        elif args.command == "flip":
            result = flip(image, args.direction)
        elif args.command == "gray":
            result = to_grayscale(image)
        elif args.command == "convert":
            result = image
        else:  # 正常情况下不会走到这里
            raise ImageError(f"未知命令: {args.command}")

        saved_path = save_image(result, output_path, source=input_path)
        report_saved(saved_path)
    except ImageError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
