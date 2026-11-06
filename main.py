"""图片信息查看与编辑工具的命令行入口。"""

from __future__ import annotations

import argparse
import sys

from image_info import format_info, get_image_info
from image_io import ImageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image-editor",
        description="查看图片基础信息，并完成缩放、裁剪、旋转等简单编辑。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="查看图片基础信息")
    info_parser.add_argument("input", help="图片路径")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "info":
            print(format_info(get_image_info(args.input)))
    except ImageError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
