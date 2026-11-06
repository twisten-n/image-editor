"use strict";

const state = {
  original: null,
  currentId: null,
  currentName: "",
  dims: null,
  operation: "resize",
  messageTimer: null,
};

const elements = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("fileInput"),
  previewWrap: document.getElementById("previewWrap"),
  previewImage: document.getElementById("previewImage"),
  previewBadge: document.getElementById("previewBadge"),
  modeBadge: document.getElementById("modeBadge"),
  infoGrid: document.getElementById("infoGrid"),
  opTabs: document.getElementById("opTabs"),
  params: document.getElementById("params"),
  formatSelect: document.getElementById("formatSelect"),
  applyBtn: document.getElementById("applyBtn"),
  restoreBtn: document.getElementById("restoreBtn"),
  downloadBtn: document.getElementById("downloadBtn"),
  resultName: document.getElementById("resultName"),
  message: document.getElementById("message"),
};

/* ---------------- 操作参数模板 ---------------- */

const OPERATIONS = {
  resize: {
    render: () => `
      <div class="param-row">
        <label class="field"><span>宽度（像素）</span>
          <input id="pWidth" type="number" min="1" step="1" placeholder="留空则按比例">
        </label>
        <label class="field"><span>高度（像素）</span>
          <input id="pHeight" type="number" min="1" step="1" placeholder="留空则按比例">
        </label>
      </div>
      <p class="hint">两个都填则精确缩放到指定尺寸；只填一个时，另一个按原图比例自动计算。</p>
    `,
  },
  crop: {
    render: (dims) => `
      <div class="param-row four">
        <label class="field"><span>左边界 left</span>
          <input id="pLeft" type="number" min="0" step="1" value="0">
        </label>
        <label class="field"><span>上边界 top</span>
          <input id="pTop" type="number" min="0" step="1" value="0">
        </label>
        <label class="field"><span>右边界 right</span>
          <input id="pRight" type="number" min="1" step="1" value="${dims ? dims.w : ""}">
        </label>
        <label class="field"><span>下边界 bottom</span>
          <input id="pBottom" type="number" min="1" step="1" value="${dims ? dims.h : ""}">
        </label>
      </div>
      <p class="hint">right 和 bottom 不包含在裁剪区域内；坐标越界时程序会给出提示。</p>
    `,
  },
  rotate: {
    render: () => `
      <label class="field"><span>旋转角度（顺时针）</span>
        <select id="pAngle">
          <option value="90">90°</option>
          <option value="180">180°</option>
          <option value="270">270°</option>
        </select>
      </label>
      <p class="hint">旋转 90° 或 270° 后，图片的宽和高会互换。</p>
    `,
  },
  flip: {
    render: () => `
      <label class="field"><span>翻转方向</span>
        <select id="pDirection">
          <option value="horizontal">水平翻转（左右镜像）</option>
          <option value="vertical">垂直翻转（上下镜像）</option>
        </select>
      </label>
    `,
  },
  gray: {
    render: () => `<p class="hint">把彩色图片转换为灰度图。已经是灰度图时会保持原样。</p>`,
  },
  convert: {
    render: () => `<p class="hint">只转换格式，不改变画面内容。请在下方选择输出格式。</p>`,
  },
};

/* ---------------- 工具函数 ---------------- */

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showMessage(text, type = "") {
  elements.message.textContent = text;
  elements.message.className = `message ${type}`.trim();
  if (state.messageTimer) clearTimeout(state.messageTimer);
  if (type === "ok") {
    state.messageTimer = setTimeout(() => {
      elements.message.textContent = "";
      elements.message.className = "message";
    }, 5000);
  }
}

function renderInfo(info) {
  const order = ["文件名", "图片格式", "宽度和高度", "颜色模式", "文件大小"];
  const html = order
    .filter((key) => info && info[key])
    .map(
      (key) => `
        <div class="info-item">
          <dt>${escapeHtml(key)}</dt>
          <dd>${escapeHtml(info[key])}</dd>
        </div>`,
    )
    .join("");
  elements.infoGrid.innerHTML = html || '<div class="empty-info">暂无信息</div>';
}

function setBusy(busy, text = "应用并预览") {
  elements.applyBtn.disabled = busy || !state.currentId;
  elements.applyBtn.textContent = busy ? "处理中…" : text;
  elements.dropzone.style.pointerEvents = busy ? "none" : "";
  elements.dropzone.style.opacity = busy ? "0.6" : "";
}

function renderParams() {
  const config = OPERATIONS[state.operation];
  elements.params.innerHTML = config.render(state.dims);
}

function enableControls() {
  elements.opTabs.querySelectorAll(".op").forEach((button) => {
    button.disabled = false;
  });
  elements.applyBtn.disabled = false;
  elements.fileInput.disabled = false;
}

function valueOrNull(id) {
  const input = document.getElementById(id);
  if (!input) return null;
  const value = input.value.trim();
  return value === "" ? null : Number(value);
}

function collectParams() {
  switch (state.operation) {
    case "resize":
      return { width: valueOrNull("pWidth"), height: valueOrNull("pHeight") };
    case "crop":
      return {
        left: valueOrNull("pLeft"),
        top: valueOrNull("pTop"),
        right: valueOrNull("pRight"),
        bottom: valueOrNull("pBottom"),
      };
    case "rotate":
      return { angle: Number(document.getElementById("pAngle").value) };
    case "flip":
      return { direction: document.getElementById("pDirection").value };
    default:
      return {};
  }
}

/* ---------------- 接口请求 ---------------- */

async function requestJSON(url, options) {
  const response = await fetch(url, options);
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    throw new Error(data.error || `请求失败（HTTP ${response.status}）`);
  }
  return data;
}

function applyResult(data, { reset = false } = {}) {
  if (reset) state.original = data;

  state.currentId = data.id;
  state.currentName = data.filename;
  state.dims = { w: data.width, h: data.height };

  elements.dropzone.classList.add("hidden");
  elements.previewWrap.classList.remove("hidden");
  elements.previewImage.src = data.preview_url;
  elements.previewImage.alt = data.filename;

  const isOriginal = state.original && data.id === state.original.id;
  elements.previewBadge.textContent = isOriginal ? "原图" : "处理结果";
  elements.modeBadge.textContent = isOriginal ? "可编辑" : "已修改，可继续编辑";
  elements.modeBadge.classList.toggle("subtle", isOriginal);

  elements.resultName.textContent = `当前文件：${data.filename}`;
  elements.downloadBtn.href = data.download_url;
  elements.downloadBtn.classList.remove("disabled");
  elements.downloadBtn.setAttribute("aria-disabled", "false");
  elements.restoreBtn.disabled = isOriginal;

  renderInfo(data.info);
  enableControls();
}

/* ---------------- 上传 ---------------- */

function validateFile(file) {
  if (!file) return "请选择图片文件";
  if (!/\.(jpe?g|png|bmp|webp)$/i.test(file.name)) {
    return "不支持的格式，请选择 JPG、PNG、BMP 或 WEBP 图片";
  }
  if (file.size > 20 * 1024 * 1024) {
    return "图片超过 20 MB 限制，请先压缩后再上传";
  }
  return "";
}

async function uploadFile(file) {
  const problem = validateFile(file);
  if (problem) {
    showMessage(problem, "error");
    return;
  }

  const formData = new FormData();
  formData.append("image", file);

  setBusy(true, "正在上传…");
  showMessage("");
  try {
    const data = await requestJSON("/api/upload", { method: "POST", body: formData });
    state.operation = "resize";
    elements.opTabs.querySelectorAll(".op").forEach((button) => {
      button.classList.toggle("active", button.dataset.op === "resize");
    });
    elements.formatSelect.value = "keep";
    applyResult(data, { reset: true });
    renderParams();
    showMessage(`已上传 ${data.filename}，请选择操作后点击“应用并预览”。`, "ok");
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    setBusy(false);
  }
}

/* ---------------- 应用操作 ---------------- */

async function applyOperation() {
  if (!state.currentId) return;

  setBusy(true, "处理中…");
  showMessage("");
  try {
    const data = await requestJSON("/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: state.currentId,
        operation: state.operation,
        params: collectParams(),
        format: elements.formatSelect.value,
      }),
    });
    applyResult(data, { reset: false });
    showMessage("处理完成，可以继续编辑，或直接下载结果。", "ok");
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    setBusy(false);
  }
}

/* ---------------- 事件绑定 ---------------- */

elements.dropzone.addEventListener("click", () => elements.fileInput.click());
elements.dropzone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    elements.fileInput.click();
  }
});

elements.fileInput.addEventListener("change", () => {
  uploadFile(elements.fileInput.files[0]);
  elements.fileInput.value = "";
});

["dragenter", "dragover"].forEach((name) => {
  elements.dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    elements.dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((name) => {
  elements.dropzone.addEventListener(name, (event) => {
    event.preventDefault();
    elements.dropzone.classList.remove("dragover");
  });
});

elements.dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file) uploadFile(file);
});

elements.opTabs.addEventListener("click", (event) => {
  const button = event.target.closest(".op");
  if (!button || button.disabled) return;

  state.operation = button.dataset.op;
  elements.opTabs.querySelectorAll(".op").forEach((item) => {
    item.classList.toggle("active", item === button);
  });
  renderParams();
  showMessage("");
});

elements.applyBtn.addEventListener("click", applyOperation);

elements.restoreBtn.addEventListener("click", () => {
  if (!state.original) return;
  applyResult(state.original, { reset: false });
  renderParams();
  showMessage("已恢复为原图。", "ok");
});
