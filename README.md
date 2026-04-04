# QuickImage

Fast image search and copy tool for Windows, powered by Everything.

<p align="center">
  <strong>English</strong> | <a href="README.zh.md">简体中文</a>
</p>

Chinese full documentation: [README.zh.md](README.zh.md)

![QuickImage demo](assets/quickimage-demo.gif)

---

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
| Search Engine | [Everything](https://www.voidtools.com/) can be downloaded and installed automatically on first launch |
| Python | 3.8+ (for source run) |
| SDK | Downloaded automatically by QuickImage when needed |

> You do not need to install the SDK manually. QuickImage prepares it automatically on first launch and falls back to `es.exe` if needed.

---

## Quick Start (Source)

1. Install Everything (recommended with `es.exe` command line component)
2. Run in project directory:

```bash
python main.pyw
```

3. On first launch:
   - If Everything is missing, QuickImage shows a bilingual prompt and can install it automatically
   - `File -> Set Source Directory`
   - `File -> Set Output Directory` (optional)

> The language menu is now bilingual: `Language / 语言`, so English and Chinese users can both find it quickly.

---

## SDK Acceleration

Regular users do not need to handle the SDK manually.

On first launch, QuickImage can:

- detect whether the SDK is available
- download it from voidtools automatically when missing
- place the correct DLL automatically
- fall back to `es.exe` if the SDK step fails

Manual DLL placement is only needed for developer debugging.

If you want to re-check dependencies later, use:

- `File -> Check Search Components / 检查搜索组件`

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

**© NerionX**
