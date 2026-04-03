# QuickImage

Fast image search and copy tool for Windows, powered by Everything.

<p align="center">
  <a href="#english">English</a> | <a href="#zh-cn">简体中文</a>
</p>

Chinese full documentation: [README.zh.md](README.zh.md)

---

<a id="english"></a>

## English

## What It Does

QuickImage focuses on one workflow:

**Type image names -> get instant matches -> copy to your target folder.**

Ideal for JIT asset pickup, sample organization, and batch refill work.

---

## Key Features

- Real-time search while typing
- Exact filename matching (without extension)
- Multiple keywords in one query (space-separated)
- Custom output directory
- Auto-create output directory if missing
- Automatic engine fallback: SDK first, then `es.exe`
- Built-in language switch: `File -> Language -> English/Chinese`

---

## Requirements

| Item | Requirement |
|---|---|
| OS | Windows 10 / 11 |
| Search Engine | [Everything](https://www.voidtools.com/) must be installed |
| Python | 3.8+ (for source run) |
| SDK (Optional) | `Everything64.dll` for better search performance |

> The app still works without SDK and will automatically use `es.exe`.

---

## Quick Start (Source)

1. Install Everything (recommended with `es.exe` command line component)
2. Run in project directory:

```bash
python main.pyw
```

3. On first launch:
   - `File -> Set Source Directory`
   - `File -> Set Output Directory` (optional)

---

## SDK Acceleration (Optional)

If you want faster searches, place the SDK DLL.

- SDK page: `https://www.voidtools.com/support/everything/sdk/`
- SDK zip: `https://www.voidtools.com/Everything-SDK.zip`

Recommended file:

- `Everything64.dll` (for 64-bit systems)

Recommended locations (either one):

- `Everything-SDK/dll/Everything64.dll`
- App folder as `Everything64.dll`

The app auto-detects and prefers SDK when available.

---

## Usage

1. Type image names in the search box (space-separated for multiple)
2. Results appear in real time
3. Press `Enter` or `Ctrl+C` to copy results to output directory

---

## Shortcuts

| Key | Action |
|---|---|
| `Enter` / `Ctrl+C` | Copy current results |
| `Ctrl+A` | Select all results |
| `T` | Toggle always-on-top |

---

## Check Current Engine

Look at the bottom status bar:

- `Engine: SDK` -> SDK is currently in use
- `Engine: es.exe` -> command-line fallback is in use

---

## Config File

Configuration is saved at:

- `C:\Users\<your_user>\.image_search_config.json`

Saved items include:

- Source directory
- Output directory
- Window geometry
- UI language

---

## License

MIT License - see `LICENSE`

---

<a id="zh-cn"></a>

## 简体中文

QuickImage 是一个基于 Everything 的 Windows 极速图片搜索复制工具。

- 输入即搜，支持多关键词（空格分隔）
- 精确文件名匹配（不含扩展名）
- 支持自定义保存目录
- 搜索引擎自动切换：优先 SDK，失败回退 `es.exe`
- 软件内支持中英文切换：`文件 -> 语言 -> 中文/English`

快速开始：

1. 安装 Everything（建议包含 `es.exe`）
2. 运行 `python main.pyw`
3. 在应用中设置源目录与保存目录

完整中文文档请查看：`README.zh.md`

---

**© NerionX**
