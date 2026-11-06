# 图片信息查看与编辑工具

一个用 Python 编写的图片处理工具，提供**网页版**和**命令行版**两种使用方式：可以查看图片的
基础信息，并完成缩放、裁剪、旋转、翻转、灰度化和格式转换等简单编辑。所有编辑结果都会
另存为新文件，不会覆盖原图。

## 1. 项目介绍

### 1.1 程序做什么

- 读取并展示图片的文件名、格式、宽高、颜色模式、文件大小；
- 对图片进行常见的简单编辑，并把结果保存为新文件；
- 对文件不存在、文件不是图片、参数非法等情况给出清晰提示，而不是直接崩溃。

### 1.2 支持的功能

| 功能 | 命令 | 说明 |
| --- | --- | --- |
| 读取图片信息 | `info` | 文件名、格式、宽高、颜色模式、文件大小 |
| 缩放 | `resize` | 指定宽高；只给宽或高时按比例缩放 |
| 裁剪 | `crop` | 指定左、上、右、下坐标，越界会提示 |
| 旋转 | `rotate` | 支持顺时针 90、180、270 度 |
| 翻转 | `flip` | 水平翻转、垂直翻转 |
| 灰度化 | `gray` | 彩色图转灰度图 |
| 格式转换 | `convert` | 例如 PNG 与 JPG 互转，自动处理透明通道 |

> 网页版在页面上以按钮和表单提供同样的功能，具体操作见 3.2 节。

### 1.3 程序形式与技术栈

- 形式：**网页版（主）+ 命令行版**，两种方式共用同一套图片处理函数
- 语言：Python 3.10+
- 网页框架：Flask
- 图片处理：OpenCV（`opencv-python`）+ NumPy
- 图片信息读取：Pillow

## 2. 环境配置

### 2.1 Python 版本

需要 **Python 3.10 或更高版本**。可用下面的命令确认：

```bash
python --version
```

### 2.2 使用 uv 安装依赖（推荐）

项目根目录已经提供 `pyproject.toml` 和 `uv.lock`。

1. 安装 uv（若尚未安装）：

   Linux / macOS：

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Windows PowerShell：

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. 在项目根目录安装依赖（会自动创建 `.venv` 虚拟环境）：

   ```bash
   uv sync
   ```

### 2.3 使用 pip 安装（备选）

如果不想使用 uv，也可以手动创建虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate          # Windows 使用 .venv\Scripts\activate
pip install "numpy>=1.24" "opencv-python>=4.8" "pillow>=10.0" "flask>=3.0"
```

## 3. 运行方式

本项目提供网页版和命令行版，两种方式共用同一套图片处理逻辑，功能一致。

### 3.1 启动网页版（推荐）

在项目根目录执行：

```bash
uv sync
uv run python app.py
```

看到类似下面的提示后，用浏览器打开 <http://127.0.0.1:5000>：

```text
图片编辑网页已启动：http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
```

按 `Ctrl+C` 可以停止服务。

> 网页版上传的图片和处理结果临时保存在系统临时目录，不会写入项目仓库；
> 重启服务后需要重新上传图片。

### 3.2 网页版操作步骤

1. 把图片拖到左侧虚线区域，或点击该区域选择文件（支持 JPG / PNG / BMP / WEBP，最大 20 MB）；
2. 页面会显示图片预览，以及文件名、格式、宽高、颜色模式、文件大小；
3. 在右侧选择操作：
   - **缩放**：填写宽度或高度，留空的一项会按原图比例自动计算；
   - **裁剪**：填写 left / top / right / bottom，默认已填入整张图的坐标；
   - **旋转**：选择 90° / 180° / 270°；
   - **翻转**：选择水平或垂直；
   - **灰度化**：无需参数；
   - **格式转换**：配合“输出格式”使用；
4. 选择输出格式（也可以保持原格式），点击 **应用并预览**；
5. 预览满意后点击 **下载结果**，文件会保存到浏览器默认下载目录；
6. 可以继续对结果做下一次编辑；点击 **恢复原图** 可回到刚上传时的状态。

> 参数不合法（例如宽度为 0、裁剪越界）时，右侧会显示红色错误提示，程序不会崩溃。

### 3.3 命令行版（可选）

所有命令都在**项目根目录**执行，基本格式为：

```bash
uv run python main.py <子命令> <图片路径> [选项]
```

> 如果使用 2.3 的 pip 方式，把 `uv run python main.py` 换成 `python main.py` 即可。

项目自带两张示例图片：

- `samples/demo.jpg`：普通彩色图
- `samples/transparent.png`：带透明通道的 PNG

#### 3.3.1 查看图片信息

```bash
uv run python main.py info samples/demo.jpg
```

预期输出（文件大小会随图片变化）：

```text
文件名     : demo.jpg
图片格式   : JPEG
宽度和高度 : 640 x 427 像素
颜色模式   : RGB
文件大小   : 16.53 KB
```

#### 3.3.2 缩放

指定宽度，高度按比例自动计算：

```bash
uv run python main.py resize samples/demo.jpg -o out_resize.jpg --width 320
```

同时指定宽高：

```bash
uv run python main.py resize samples/demo.jpg -o out_resize2.jpg --width 200 --height 200
```

预期输出：

```text
已保存到: out_resize.jpg（10.29 KB）
```

只给 `--height` 时，宽度同样会按比例计算。

#### 3.3.3 裁剪

`--left`、`--top` 为裁剪区域左上角（包含），`--right`、`--bottom` 为右下角（**不包含**）。

```bash
uv run python main.py crop samples/demo.jpg -o out_crop.jpg \
  --left 50 --top 40 --right 300 --bottom 240
```

上面的命令会得到一张 250 x 200 像素的图片。

坐标越界时会给出提示，例如：

```text
错误: 裁剪区域越界，需满足 0 <= left < right <= 640 且 0 <= top < bottom <= 427，...
```

#### 3.3.4 旋转

只支持顺时针 90、180、270 度：

```bash
uv run python main.py rotate samples/demo.jpg -o out_rot90.jpg --angle 90
```

#### 3.3.5 翻转

```bash
# 水平翻转（左右镜像）
uv run python main.py flip samples/demo.jpg -o out_flip_h.jpg --direction horizontal

# 垂直翻转（上下镜像）
uv run python main.py flip samples/demo.jpg -o out_flip_v.jpg --direction vertical
```

#### 3.3.6 灰度化

```bash
uv run python main.py gray samples/demo.jpg -o out_gray.png
```

输出图片的颜色模式会变成灰度（`L`）。

#### 3.3.7 格式转换

`convert` 必须用 `-o` 指定输出文件，**扩展名决定目标格式**：

```bash
# PNG 转 JPG
uv run python main.py convert samples/transparent.png -o out_transparent.jpg

# JPG 转 PNG
uv run python main.py convert samples/demo.jpg -o out_demo.png
```

带透明通道的 PNG 转 JPG 时，程序会自动把 RGBA 转成 RGB，不会因为透明通道报错。

#### 3.3.8 关于输出文件

- 除 `convert` 外，其余编辑命令的 `-o/--output` 都可以省略；
- 省略时会在原图旁边自动生成 `原文件名_操作名.扩展名`，例如
  `samples/demo.jpg` 缩放后会得到 `samples/demo_resize.jpg`；
- 程序**不允许**把结果写回原图路径，避免覆盖原图；
- 保存成功后会打印完整保存路径和文件大小。

#### 3.3.9 错误提示示例

```bash
uv run python main.py info not_exist.jpg
# 错误: 文件不存在: not_exist.jpg

uv run python main.py info fake.jpg
# 错误: 不是有效的图片文件: fake.jpg

uv run python main.py resize samples/demo.jpg --width 0
# 错误: 宽度必须大于 0，收到: 0
```

出现以上提示时程序以非 0 状态退出，但不会打印大段 traceback。

## 4. 项目结构

```text
.
├── app.py             # 网页版入口：Flask 路由与接口
├── main.py            # 命令行入口：解析参数、调用各功能
├── image_info.py      # 读取并格式化图片基础信息
├── image_io.py        # 图片读写、格式校验、透明通道处理
├── image_ops.py       # 缩放、裁剪、旋转、翻转、灰度化
├── templates/
│   └── index.html     # 单页工作台页面
├── static/
│   ├── style.css      # 页面样式
│   └── app.js         # 上传、调用接口、预览和下载
├── samples/           # 示例图片（体积很小）
├── pyproject.toml     # 项目依赖配置
├── uv.lock            # uv 锁定的依赖版本
├── .gitignore
└── README.md
```

## 5. 说明

- 颜色模式由 Pillow 读取，结果为 `RGB`、`RGBA`、`灰度 (L)`、`调色板 (P)` 等；
- 图片读写使用 `imdecode` / `imencode`，兼容包含中文的路径；
- 支持保存为 `jpg`、`jpeg`、`png`、`bmp`、`webp`；
- 旋转只接受 90/180/270，其他角度会由参数校验直接拒绝；
- 网页版和命令行版调用的是同一套 `image_ops` / `image_io` / `image_info` 函数；
- 网页版为本地开发服务器，默认只监听 `127.0.0.1:5000`，不会把图片上传到互联网。
