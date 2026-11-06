"""网页版入口：把图片查看与编辑功能包装成 Flask 接口。

命令行版本仍然由 main.py 提供，本文件只负责浏览器交互。
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_file, url_for

from image_info import get_image_info
from image_io import ImageError, read_image, save_image
from image_ops import crop, flip, resize, rotate, to_grayscale

# 上传文件与处理结果都放在系统临时目录，避免污染项目仓库。
WORK_DIR = Path(tempfile.gettempdir()) / "image_editor_web"
WORK_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
INPUT_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
# 前端传来的格式名 -> 保存扩展名
OUTPUT_SUFFIXES = {
    "jpg": ".jpg",
    "jpeg": ".jpg",
    "png": ".png",
    "bmp": ".bmp",
    "webp": ".webp",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# 图片 id -> {"path": Path, "name": 展示文件名, "stem": 原始文件名主干, "suffix": 扩展名}
IMAGES: dict[str, dict] = {}


def _clean_filename(filename: str) -> str:
    """去掉浏览器可能带上的路径和控制字符，只保留文件名本身。"""
    name = filename.replace("\\", "/").split("/")[-1].strip()
    name = "".join(char for char in name if char.isprintable())
    return name[:120] or "image"


def _register(path: Path, name: str, stem: str, suffix: str) -> str:
    image_id = uuid.uuid4().hex
    IMAGES[image_id] = {"path": path, "name": name, "stem": stem, "suffix": suffix}
    return image_id


def _error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def _payload(image_id: str, width: int, height: int, info: dict, name: str) -> dict:
    return {
        "id": image_id,
        "filename": name,
        "width": width,
        "height": height,
        "info": info,
        "preview_url": url_for("api_file", image_id=image_id),
        "download_url": url_for("api_download", image_id=image_id),
    }


def _parse_int(value, label: str, required: bool = True) -> int | None:
    if value is None or value == "":
        if required:
            raise ImageError(f"请填写{label}")
        return None
    if isinstance(value, bool):
        raise ImageError(f"{label}必须是整数")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ImageError(f"{label}必须是整数") from None


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/upload")
def api_upload():
    uploaded = request.files.get("image")
    if uploaded is None or not uploaded.filename:
        return _error("请选择要上传的图片")

    original_name = _clean_filename(uploaded.filename)
    suffix = Path(original_name).suffix.lower()
    if suffix not in INPUT_SUFFIXES:
        supported = "、".join(sorted(INPUT_SUFFIXES))
        return _error(f"不支持的图片格式，可用格式：{supported}")

    data = uploaded.read()
    if not data:
        return _error("上传的文件是空的")
    if len(data) > MAX_UPLOAD_BYTES:
        return _error("图片超过 20 MB 限制，请先压缩后再上传")

    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        return _error("文件不是有效的图片，请检查后重新上传")

    image_id = uuid.uuid4().hex
    path = WORK_DIR / f"{image_id}{suffix}"
    path.write_bytes(data)

    height, width = image.shape[:2]
    info = get_image_info(path)
    info["文件名"] = original_name  # 展示用户上传时的文件名，而不是临时文件名

    stem = Path(original_name).stem
    image_id = _register(path, original_name, stem, suffix)
    return jsonify(_payload(image_id, width, height, info, original_name))


@app.post("/api/process")
def api_process():
    payload = request.get_json(silent=True) or {}
    image_id = payload.get("id")
    record = IMAGES.get(image_id)
    if record is None:
        return _error("图片已失效，请重新上传", 404)

    operation = payload.get("operation")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        return _error("参数格式不正确")

    try:
        image = read_image(record["path"])

        if operation == "resize":
            width = _parse_int(params.get("width"), "宽度", required=False)
            height = _parse_int(params.get("height"), "高度", required=False)
            result = resize(image, width=width, height=height)
            label = "resize"
        elif operation == "crop":
            result = crop(
                image,
                _parse_int(params.get("left"), "左边界"),
                _parse_int(params.get("top"), "上边界"),
                _parse_int(params.get("right"), "右边界"),
                _parse_int(params.get("bottom"), "下边界"),
            )
            label = "crop"
        elif operation == "rotate":
            result = rotate(image, _parse_int(params.get("angle"), "旋转角度"))
            label = "rotate"
        elif operation == "flip":
            result = flip(image, str(params.get("direction", "")))
            label = "flip"
        elif operation == "gray":
            result = to_grayscale(image)
            label = "gray"
        elif operation == "convert":
            result = image.copy()
            label = "converted"
        else:
            return _error("未知的操作")

        output_format = str(payload.get("format") or "keep").lower()
        if output_format == "keep":
            suffix = record["suffix"]
        elif output_format in OUTPUT_SUFFIXES:
            suffix = OUTPUT_SUFFIXES[output_format]
        else:
            return _error("不支持的输出格式")

        output_name = f"{record['stem']}_{label}{suffix}"
        output_path = WORK_DIR / f"{uuid.uuid4().hex}{suffix}"
        save_image(result, output_path, source=record["path"])
    except ImageError as exc:
        return _error(str(exc))

    height, width = result.shape[:2]
    info = get_image_info(output_path)
    info["文件名"] = output_name

    new_id = _register(output_path, output_name, record["stem"], suffix)
    return jsonify(_payload(new_id, width, height, info, output_name))


@app.get("/api/file/<image_id>")
def api_file(image_id: str):
    record = IMAGES.get(image_id)
    if record is None:
        return _error("图片不存在或已失效", 404)
    return send_file(record["path"], conditional=True)


@app.get("/api/download/<image_id>")
def api_download(image_id: str):
    record = IMAGES.get(image_id)
    if record is None:
        return _error("图片不存在或已失效", 404)
    return send_file(record["path"], as_attachment=True, download_name=record["name"])


@app.errorhandler(413)
def too_large(_error_info):
    return _error("图片超过 20 MB 限制，请先压缩后再上传", 413)


if __name__ == "__main__":
    print("图片编辑网页已启动：http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
