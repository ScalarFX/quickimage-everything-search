# QuickImage - Fast Image Search Tool

[中文](#中文说明) | [English](#english)

---

## English

### Introduction
QuickImage is a lightning-fast image search and copy tool for Windows. It leverages [Everything](https://www.voidtools.com/) search engine to provide instant file search with millisecond-level response time.

### Features
- ⚡ **Instant Search** - Real-time results as you type
- 🎯 **Exact Match** - Search by exact filename (without extension)
- 📋 **One-Click Copy** - Copy all matched files to Desktop with Enter
- 🔍 **Floating Search Box** - Quick access with global hotkey (Ctrl+`)
- 📌 **Always on Top** - Stay visible while working
- 🖥️ **System Tray** - Minimize to tray, auto-start on boot

### Requirements
- Windows 10/11
- [Everything](https://www.voidtools.com/) with **es.exe** command-line tool
- Python 3.8+

### Installation

1. **Install Everything**
   - Download from https://www.voidtools.com/
   - During installation, check **"Install es command-line interface"**

2. **Install Python dependencies**
   ```bash
   pip install keyboard pystray pillow
   ```

3. **Run**
   ```bash
   python main.pyw
   ```

### Usage
1. Set source folder: `File → Set Source Directory`
2. Type filename (space-separated for multiple)
3. Press `Enter` or `Ctrl+C` to copy to `Desktop/每日JIT`

### Hotkeys
| Key | Action |
|-----|--------|
| `Ctrl+`` | Open floating search box |
| `Enter` / `Ctrl+C` | Copy files |
| `Ctrl+A` | Select all |
| `T` | Toggle always on top |
| `Esc` | Close floating box |

### License
MIT License - see [LICENSE](LICENSE)

---

## 中文说明

### 简介
QuickImage 是一款极速图片搜索复制工具，基于 [Everything](https://www.voidtools.com/) 搜索引擎，提供毫秒级实时搜索体验。

### 功能特点
- ⚡ **极速搜索** - 输入即搜，实时显示结果
- 🎯 **精确匹配** - 按文件名精确搜索（不含扩展名）
- 📋 **一键复制** - Enter 键批量复制到桌面
- 🔍 **悬浮搜索框** - 全局快捷键 Ctrl+` 快速呼出
- 📌 **窗口置顶** - 工作时保持可见
- 🖥️ **系统托盘** - 最小化到托盘，支持开机启动

### 环境要求
- Windows 10/11
- [Everything](https://www.voidtools.com/) 并安装 **es.exe** 命令行工具
- Python 3.8+

### 安装步骤

1. **安装 Everything**
   - 下载地址：https://www.voidtools.com/
   - 安装时勾选 **"安装 es 命令行界面"**

2. **安装 Python 依赖**
   ```bash
   pip install keyboard pystray pillow
   ```

3. **运行**
   ```bash
   python main.pyw
   ```

### 使用方法
1. 设置源目录：`文件 → 设置源目录`
2. 输入文件名（多个用空格分隔）
3. 按 `Enter` 或 `Ctrl+C` 复制到 `桌面/每日JIT`

### 快捷键
| 按键 | 功能 |
|------|------|
| `Ctrl+`` | 打开悬浮搜索框 |
| `Enter` / `Ctrl+C` | 复制文件 |
| `Ctrl+A` | 全选 |
| `T` | 切换置顶 |
| `Esc` | 关闭悬浮框 |

### 开机自启动
运行 `添加开机启动.bat` 即可添加开机自启动。

### 许可证
MIT License - 详见 [LICENSE](LICENSE)

---

**© NerionX**
