"""
QuickImage - 极简图片搜索 (Everything 风格)
使用 .pyw 扩展名隐藏控制台窗口
"""
import os
import queue
import re
import shutil
import threading
import subprocess
import tempfile
import tkinter as tk
import tkinter.font as tkfont
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from tkinter import ttk, filedialog, messagebox
import ctypes

# 4K DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

from config import load_config, save_config
from search_engine import (
    search_images,
    parse_keywords,
    get_backend_label,
    find_everything_dll,
    find_es_exe,
    find_everything_executable,
)

# 系统托盘支持
try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "每日JIT")
WINDOW_EDGE_MARGIN = 40
VOIDTOOLS_DOWNLOADS_URL = "https://www.voidtools.com/downloads/"
DOWNLOAD_TIMEOUT_SECONDS = 30
DOWNLOAD_BLOCK_SIZE = 262144

I18N = {
    "zh": {
        "not_set": "未设置",
        "ready": "就绪",
        "searching": "搜索中...",
        "menu_file": "文件(F)",
        "menu_edit": "编辑(E)",
        "menu_help": "帮助(H)",
        "set_source": "设置源目录(O)...",
        "set_output": "设置保存目录(S)...",
        "check_deps": "检查搜索组件 / Check Search Components",
        "language": "语言 / Language (L)",
        "lang_zh": "中文 / Chinese",
        "lang_en": "English / 英文",
        "exit": "退出(X)",
        "copy_output": "复制到保存目录(C)",
        "select_all": "全选(A)",
        "topmost": "窗口置顶(T)",
        "help": "帮助(H)",
        "about": "关于 QuickImage(A)...",
        "col_name": "名称",
        "col_path": "路径",
        "col_size": "大小",
        "source_prefix": "源",
        "output_prefix": "保存",
        "engine_prefix": "引擎",
        "backend_not_ready": "未就绪",
        "source_updated": "源目录已更新",
        "output_updated": "保存目录已更新",
        "source_required": "请先设置源目录 (文件 -> 设置源目录)",
        "display_results": "显示 {display:,} / {total:,} 个结果",
        "results_count": "{count:,} 个结果",
        "not_found": "未找到匹配图片",
        "copied": "已复制 {count} 个文件到保存目录",
        "help_title": "帮助",
        "help_text": (
            "使用方法:\n\n"
            "1. 文件 -> 设置源目录\n"
            "2. 文件 -> 设置保存目录 (可选)\n"
            "3. 输入精确文件名 (空格分隔多个)\n"
            "4. 按 Enter/Ctrl+C 复制到保存目录\n"
            "\n"
            "快捷键:\n"
            "Ctrl+A - 全选\n"
            "Ctrl+C/Enter - 复制\n"
            "T - 切换置顶"
        ),
        "about_title": "关于 QuickImage",
        "about_text": "QuickImage v1.0\n\n极简图片搜索工具\n基于 Everything 搜索引擎\n\n© NerionX",
        "tray_show": "显示主窗口",
        "tray_exit": "退出",
        "mini_source_required": "未设置源目录",
        "mini_found": "找到 {count} 个文件，按 Enter 复制",
        "mini_not_found": "未找到",
        "mini_copied": "已复制 {count} 个文件",
        "mini_empty": "无文件可复制",
        "deps_prompt_title": "安装搜索组件",
        "deps_prompt_body": (
            "检测到本机还没有可用的 Everything 搜索环境。\n\n"
            "QuickImage 现在可以自动为你完成：\n"
            "1. 下载并安装 Everything（官方）\n"
            "2. 自动下载加速组件 SDK\n"
            "3. 自动准备命令行搜索组件\n\n"
            "整个过程会使用官方 voidtools 下载地址。\n"
            "是否现在开始？\n\n"
            "English:\n"
            "QuickImage can now download and install Everything, the SDK, and the CLI helper automatically.\n"
            "Do you want to continue now?"
        ),
        "deps_installing": "正在自动准备搜索组件，请稍候...",
        "deps_ready": "搜索组件已准备完成",
        "deps_declined": "已跳过自动安装，可稍后再次打开程序进行安装",
        "deps_failed_title": "自动安装失败",
        "deps_failed": (
            "自动安装没有完成。\n\n"
            "请确认网络可访问 voidtools 官网，或者稍后重试。\n\n"
            "English:\n"
            "Automatic setup did not complete. Please check your network and try again."
        ),
        "deps_done_title": "安装完成",
        "deps_done": (
            "搜索组件已准备完成，现在可以直接使用。\n\n"
            "English:\n"
            "Search components are ready. You can use QuickImage now."
        ),
        "deps_repair_title": "修复搜索组件",
        "deps_repair_body": (
            "QuickImage 将重新检查 Everything、SDK 和命令行搜索组件。\n"
            "如果缺少内容，会自动下载并修复。\n\n"
            "是否现在开始？\n\n"
            "English:\n"
            "QuickImage will re-check Everything, the SDK, and the CLI helper, then repair anything missing.\n"
            "Do you want to continue now?"
        ),
        "deps_missing_runtime_title": "搜索组件缺失",
        "deps_missing_runtime": (
            "当前没有可用的搜索组件，因此无法执行搜索。\n\n"
            "是否现在自动修复？\n\n"
            "English:\n"
            "A working search component is missing, so search cannot continue.\n"
            "Would you like QuickImage to repair it now?"
        ),
    },
    "en": {
        "not_set": "Not set",
        "ready": "Ready",
        "searching": "Searching...",
        "menu_file": "File(F)",
        "menu_edit": "Edit(E)",
        "menu_help": "Help(H)",
        "set_source": "Set Source Directory(O)...",
        "set_output": "Set Output Directory(S)...",
        "check_deps": "Check Search Components / 检查搜索组件",
        "language": "Language / 语言 (L)",
        "lang_zh": "Chinese / 中文",
        "lang_en": "English / 英文",
        "exit": "Exit(X)",
        "copy_output": "Copy to Output(C)",
        "select_all": "Select All(A)",
        "topmost": "Always on Top(T)",
        "help": "Help(H)",
        "about": "About QuickImage(A)...",
        "col_name": "Name",
        "col_path": "Path",
        "col_size": "Size",
        "source_prefix": "Source",
        "output_prefix": "Output",
        "engine_prefix": "Engine",
        "backend_not_ready": "Not Ready",
        "source_updated": "Source directory updated",
        "output_updated": "Output directory updated",
        "source_required": "Please set source directory first (File -> Set Source Directory)",
        "display_results": "Showing {display:,} / {total:,} results",
        "results_count": "{count:,} results",
        "not_found": "No matching images found",
        "copied": "Copied {count} files to output directory",
        "help_title": "Help",
        "help_text": (
            "How to use:\n\n"
            "1. File -> Set Source Directory\n"
            "2. File -> Set Output Directory (optional)\n"
            "3. Enter exact file names (space-separated for multiple)\n"
            "4. Press Enter/Ctrl+C to copy to output directory\n"
            "\n"
            "Shortcuts:\n"
            "Ctrl+A - Select all\n"
            "Ctrl+C/Enter - Copy\n"
            "T - Toggle always on top"
        ),
        "about_title": "About QuickImage",
        "about_text": "QuickImage v1.0\n\nMinimal image search tool\nPowered by Everything search engine\n\n© NerionX",
        "tray_show": "Show Main Window",
        "tray_exit": "Exit",
        "mini_source_required": "Source directory is not set",
        "mini_found": "Found {count} files, press Enter to copy",
        "mini_not_found": "No results",
        "mini_copied": "Copied {count} files",
        "mini_empty": "No files to copy",
        "deps_prompt_title": "Install Search Components",
        "deps_prompt_body": (
            "QuickImage could not find a working Everything search environment.\n\n"
            "It can automatically:\n"
            "1. Download and install Everything from voidtools\n"
            "2. Download the SDK for faster search\n"
            "3. Download the CLI helper automatically\n\n"
            "Would you like to continue now?\n\n"
            "中文：\n"
            "QuickImage 可以自动帮你安装 Everything、SDK 和命令行组件。是否现在开始？"
        ),
        "deps_installing": "Preparing search components automatically...",
        "deps_ready": "Search components are ready",
        "deps_declined": "Automatic setup skipped. You can reopen the app later to install it.",
        "deps_failed_title": "Automatic Setup Failed",
        "deps_failed": (
            "Automatic setup did not complete.\n\n"
            "Please check network access to the voidtools website and try again.\n\n"
            "中文：\n"
            "自动安装未完成，请检查网络后重试。"
        ),
        "deps_done_title": "Setup Complete",
        "deps_done": (
            "Search components are ready. You can use QuickImage now.\n\n"
            "中文：\n"
            "搜索组件已准备完成，现在可以直接使用。"
        ),
        "deps_repair_title": "Repair Search Components",
        "deps_repair_body": (
            "QuickImage will re-check Everything, the SDK, and the CLI helper.\n"
            "Anything missing will be downloaded automatically.\n\n"
            "Do you want to continue now?\n\n"
            "中文：\n"
            "QuickImage 会重新检查 Everything、SDK 和命令行组件，并自动修复缺失部分。"
        ),
        "deps_missing_runtime_title": "Search Component Missing",
        "deps_missing_runtime": (
            "A working search component is missing, so search cannot continue.\n\n"
            "Would you like QuickImage to repair it now?\n\n"
            "中文：\n"
            "当前缺少可用搜索组件，是否现在自动修复？"
        ),
    },
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.cfg = load_config()
        self.current_language = self.cfg.get("language", "zh")
        if self.current_language not in I18N:
            self.current_language = "zh"
        self.lang_var = tk.StringVar(value=self.current_language)

        self.colors = {
            "bg_app": "#f6f7f9",
            "bg_card": "#ffffff",
            "bg_subtle": "#f3f4f6",
            "border": "#d9dde3",
            "text": "#1f2933",
            "text_muted": "#6b7280",
            "accent_soft": "#dbeafe",
            "row_alt": "#fafbfc",
        }

        self.spacing = {
            "outer": 6,
            "section": 4,
            "inner": 4,
            "status_top": 3,
        }
        
        self.title("QuickImage")
        self.geometry("920x580")
        self.minsize(600, 400)
        self.configure(bg=self.colors["bg_app"])
        
        
        # 图标
        self.icon_path = os.path.join(os.path.dirname(__file__), "i.png")
        if os.path.exists(self.icon_path):
            try:
                img = tk.PhotoImage(file=self.icon_path)
                self.iconphoto(True, img)
            except:
                pass

        self.tree_font = tkfont.Font(family="Segoe UI", size=9)
        self.heading_font = tkfont.Font(family="Microsoft YaHei", size=9)
        self.status_font = tkfont.Font(family="Microsoft YaHei UI", size=9)
        self.tree_rowheight = max(self.tree_font.metrics("linespace") + 10, 28)
        
        self._setup_styles()
        self.default_name_col_width = 180
        self.max_name_col_width = 280
        self.current_name_col_width = self.default_name_col_width
        
        self.results = []
        self.timer = None
        self.search_delay_ms = 200
        self.search_token = 0
        self.last_search_signature = None
        self.search_queue = queue.Queue(maxsize=1)
        self.search_worker = threading.Thread(target=self._search_worker_loop, daemon=True)
        self.search_worker.start()

        self.size_update_token = 0
        self.render_update_token = 0
        self.render_job = None
        self.geometry_save_job = None

        self.max_display_results = 1000
        self.max_search_results = 5000
        self.render_chunk_size = 60
        self.render_interval_ms = 10
        self.size_preload_limit = 120
        self.name_measure_limit = 120

        self.is_topmost = tk.BooleanVar(value=True)  # 默认置顶
        self.tray_icon = None
        self.bootstrap_in_progress = False
        
        self._menu()
        self._ui()
        self._restore_window_geometry()
        # 不使用系统托盘
        
        # 关闭窗口直接退出
        self.protocol("WM_DELETE_WINDOW", self._quit_app)
        self.bind("<Configure>", self._on_window_configure)
        
        self._update_output_status(self._ensure_output_dir())
        
        # 默认置顶
        self._toggle_topmost()
        self.after(300, self._bootstrap_dependencies_on_first_run)

    def _t(self, key):
        lang_dict = I18N.get(self.current_language, I18N["zh"])
        return lang_dict.get(key, I18N["zh"].get(key, key))

    def _backend_label(self):
        label = get_backend_label()
        if label == "未就绪":
            return self._t("backend_not_ready")
        return label

    def _set_language(self, lang, save=True):
        lang = "en" if lang == "en" else "zh"
        if lang == self.current_language and hasattr(self, "tree"):
            return

        self.current_language = lang
        self.lang_var.set(lang)

        if save:
            self.cfg["language"] = lang
            save_config(self.cfg)

        if hasattr(self, "tree"):
            self._menu()
            self.tree.heading("name", text=self._t("col_name"), anchor="w")
            self.tree.heading("path", text=self._t("col_path"), anchor="w")
            self.tree.heading("size", text=self._t("col_size"), anchor="e")
            self._update_source_status(self.cfg.get("source_path", ""))
            self._update_output_status(self._get_output_dir())
            self._update_engine_status()
            if self.results:
                total_count = len(self.results)
                display_count = min(total_count, self.max_display_results)
                if total_count > display_count:
                    self.status.set(self._t("display_results").format(display=display_count, total=total_count))
                else:
                    self.status.set(self._t("results_count").format(count=total_count))
            elif hasattr(self, "entry") and self.entry.get().strip():
                self.status.set(self._t("not_found"))
            else:
                self.status.set(self._t("ready"))

    def _on_language_changed(self):
        self._set_language(self.lang_var.get(), save=True)

    def _setup_tray(self):
        """设置系统托盘"""
        if not HAS_TRAY:
            return
        
        try:
            icon_img = Image.open(self.icon_path)
        except:
            # 创建简单图标
            icon_img = Image.new('RGB', (64, 64), color='#0078d4')
        
        menu = pystray.Menu(
            pystray.MenuItem(self._t("tray_show"), self._show_from_tray),
            pystray.MenuItem(self._t("tray_exit"), self._quit_app)
        )
        
        self.tray_icon = pystray.Icon("QuickImage", icon_img, "QuickImage", menu)
        
        # 后台运行托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        """隐藏到托盘"""
        self.withdraw()

    def _show_from_tray(self):
        """从托盘恢复"""
        self.after(0, self._do_show)

    def _do_show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_minimize(self, e):
        """最小化时隐藏到托盘"""
        if self.state() == "iconic":
            self.withdraw()

    def _quit_app(self):
        """退出程序"""
        self._save_window_geometry()
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)

    def _is_valid_window_geometry(self, geometry):
        if not isinstance(geometry, str):
            return False
        return bool(re.match(r"^\d+x\d+[+-]\d+[+-]\d+$", geometry.strip()))

    def _parse_window_geometry(self, geometry):
        if not self._is_valid_window_geometry(geometry):
            return None

        m = re.match(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$", geometry.strip())
        if not m:
            return None

        width, height, x, y = m.groups()
        return int(width), int(height), int(x), int(y)

    def _get_default_window_size(self):
        self.update_idletasks()
        screen_w = max(self.winfo_screenwidth(), 800)
        screen_h = max(self.winfo_screenheight(), 600)
        width = min(920, max(screen_w - WINDOW_EDGE_MARGIN * 2, 600))
        height = min(580, max(screen_h - 160, 400))
        return width, height

    def _fit_geometry_to_screen(self, geometry):
        parsed = self._parse_window_geometry(geometry)
        if not parsed:
            return None

        width, height, x, y = parsed
        screen_w = max(self.winfo_screenwidth(), 800)
        screen_h = max(self.winfo_screenheight(), 600)

        max_width = max(screen_w - WINDOW_EDGE_MARGIN * 2, 600)
        max_height = max(screen_h - 120, 400)
        width = min(max(width, 600), max_width)
        height = min(max(height, 400), max_height)

        min_x = 0
        min_y = 0
        max_x = max(screen_w - width, 0)
        max_y = max(screen_h - height - 80, 0)
        x = min(max(x, min_x), max_x)
        y = min(max(y, min_y), max_y)

        return f"{width}x{height}+{x}+{y}"

    def _center_main_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if width <= 1 or height <= 1:
            width, height = self._get_default_window_size()
        else:
            width = min(width, max(screen_w - WINDOW_EDGE_MARGIN * 2, 600))
            height = min(height, max(screen_h - 120, 400))
        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 3, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _restore_window_geometry(self):
        saved_geometry = self.cfg.get("window_geometry", "")
        fitted_geometry = self._fit_geometry_to_screen(saved_geometry)
        if fitted_geometry:
            self.geometry(fitted_geometry)
        else:
            width, height = self._get_default_window_size()
            self.geometry(f"{width}x{height}")
            self._center_main_window()

    def _save_window_geometry(self):
        if self.state() != "normal":
            return
        current_geometry = self.geometry()
        fitted_geometry = self._fit_geometry_to_screen(current_geometry)
        if fitted_geometry:
            self.cfg["window_geometry"] = fitted_geometry
            save_config(self.cfg)

    def _on_window_configure(self, event):
        if event.widget != self:
            return
        if self.state() != "normal":
            return
        if self.geometry_save_job:
            self.after_cancel(self.geometry_save_job)
        self.geometry_save_job = self.after(500, self._save_window_geometry_debounced)

    def _save_window_geometry_debounced(self):
        self.geometry_save_job = None
        self._save_window_geometry()

    def _clamp_popup_position(self, width, height, x, y, top_gap=20):
        screen_w = max(self.winfo_screenwidth(), width)
        screen_h = max(self.winfo_screenheight(), height)
        max_x = max(screen_w - width - 10, 0)
        max_y = max(screen_h - height - 50, 0)
        clamped_x = min(max(x, 0), max_x)
        clamped_y = min(max(y, top_gap), max_y)
        return clamped_x, clamped_y

    def _get_output_dir(self):
        configured_output = str(self.cfg.get("output_path", "")).strip()
        if configured_output:
            return os.path.normpath(configured_output)
        return OUTPUT_DIR

    def _ensure_output_dir(self):
        output_dir = self._get_output_dir()
        try:
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        except:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            self.cfg["output_path"] = ""
            save_config(self.cfg)
            return OUTPUT_DIR

    def _is_64bit_python(self):
        return ctypes.sizeof(ctypes.c_void_p) == 8

    def _dependency_state(self):
        return {
            "everything_exe": find_everything_executable(),
            "es_exe": find_es_exe(),
            "sdk_dll": find_everything_dll(),
        }

    def _bootstrap_dependencies_on_first_run(self):
        if self.cfg.get("dependencies_bootstrapped", False):
            return
        self._bootstrap_dependencies_if_needed(first_run=True)

    def _bootstrap_dependencies_if_needed(self, first_run=False):
        if self.bootstrap_in_progress:
            return

        state = self._dependency_state()
        needs_everything = not state["everything_exe"]
        needs_sdk = not state["sdk_dll"]
        needs_es = not state["es_exe"]

        if not (needs_everything or needs_sdk or needs_es):
            if first_run:
                self.cfg["dependencies_bootstrapped"] = True
                save_config(self.cfg)
            return

        if needs_everything:
            should_continue = messagebox.askyesno(
                self._t("deps_prompt_title"),
                self._t("deps_prompt_body"),
                parent=self,
            )
            if not should_continue:
                self.status.set(self._t("deps_declined"))
                return

        self._start_dependency_bootstrap(needs_everything, needs_sdk, needs_es, first_run=first_run)

    def _start_dependency_bootstrap(self, needs_everything, needs_sdk, needs_es, first_run=False):
        if self.bootstrap_in_progress:
            return

        self.bootstrap_in_progress = True
        self.status.set(self._t("deps_installing"))
        threading.Thread(
            target=self._bootstrap_dependencies_worker,
            args=(needs_everything, needs_sdk, needs_es, first_run),
            daemon=True,
        ).start()

    def _bootstrap_dependencies_worker(self, needs_everything, needs_sdk, needs_es, first_run):
        try:
            links = self._fetch_voidtools_links()
            current_dir = os.path.dirname(os.path.abspath(__file__))

            with tempfile.TemporaryDirectory(prefix="quickimage-setup-") as temp_dir:
                if needs_everything:
                    installer_name = os.path.basename(urllib.parse.urlparse(links["everything_installer"]).path)
                    installer_path = os.path.join(temp_dir, installer_name)
                    self._download_file(links["everything_installer"], installer_path)
                    self._install_everything(installer_path)

                if needs_es:
                    es_zip_name = os.path.basename(urllib.parse.urlparse(links["es_zip"]).path)
                    es_zip_path = os.path.join(temp_dir, es_zip_name)
                    self._download_file(links["es_zip"], es_zip_path)
                    self._extract_zip_member(es_zip_path, "es.exe", os.path.join(current_dir, "es.exe"))

                if needs_sdk:
                    sdk_zip_name = os.path.basename(urllib.parse.urlparse(links["sdk_zip"]).path)
                    sdk_zip_path = os.path.join(temp_dir, sdk_zip_name)
                    self._download_file(links["sdk_zip"], sdk_zip_path)
                    dll_name = "Everything64.dll" if self._is_64bit_python() else "Everything32.dll"
                    self._extract_zip_member(sdk_zip_path, dll_name, os.path.join(current_dir, dll_name))

            final_state = self._dependency_state()
            if not final_state["everything_exe"]:
                raise RuntimeError("Everything executable not found after installation.")
            if not (final_state["sdk_dll"] or final_state["es_exe"]):
                raise RuntimeError("No working search backend was prepared.")

            self.after(0, lambda: self._bootstrap_dependencies_success(first_run))
        except Exception as exc:
            self.after(0, lambda err=str(exc): self._bootstrap_dependencies_failed(err))

    def _bootstrap_dependencies_success(self, first_run):
        self.bootstrap_in_progress = False
        self.cfg["dependencies_bootstrapped"] = True
        save_config(self.cfg)
        self.status.set(self._t("deps_ready"))
        self._update_engine_status()
        if first_run:
            messagebox.showinfo(self._t("deps_done_title"), self._t("deps_done"), parent=self)

    def _bootstrap_dependencies_failed(self, error_text):
        self.bootstrap_in_progress = False
        self._update_engine_status()
        self.status.set(self._t("backend_not_ready"))
        detail_text = f"{self._t('deps_failed')}\n\n{error_text}"
        messagebox.showerror(self._t("deps_failed_title"), detail_text, parent=self)

    def _repair_dependencies(self):
        if self.bootstrap_in_progress:
            return

        should_continue = messagebox.askyesno(
            self._t("deps_repair_title"),
            self._t("deps_repair_body"),
            parent=self,
        )
        if not should_continue:
            return

        self.cfg["dependencies_bootstrapped"] = False
        save_config(self.cfg)

        state = self._dependency_state()
        self._start_dependency_bootstrap(
            not state["everything_exe"],
            not state["sdk_dll"],
            not state["es_exe"],
            first_run=False,
        )

    def _ensure_dependencies_before_search(self):
        state = self._dependency_state()
        has_backend = bool(state["sdk_dll"] or state["es_exe"])
        if state["everything_exe"] and has_backend:
            return True

        should_continue = messagebox.askyesno(
            self._t("deps_missing_runtime_title"),
            self._t("deps_missing_runtime"),
            parent=self,
        )
        if not should_continue:
            return False

        self.cfg["dependencies_bootstrapped"] = False
        save_config(self.cfg)
        self._start_dependency_bootstrap(
            not state["everything_exe"],
            not state["sdk_dll"],
            not state["es_exe"],
            first_run=False,
        )
        return False

    def _fetch_voidtools_links(self):
        html = self._download_text(VOIDTOOLS_DOWNLOADS_URL)
        arch = "x64" if self._is_64bit_python() else "x86"

        everything_installer = self._find_download_link(
            html,
            rf'href="([^"]*Everything-[^"]+\.{arch}\.msi)"',
        )
        es_zip = self._find_download_link(
            html,
            rf'href="([^"]*ES-[^"]+\.{arch}\.zip)"',
        )
        sdk_zip = self._find_download_link(
            html,
            r'href="([^"]*Everything-SDK\.zip)"',
        )

        return {
            "everything_installer": everything_installer,
            "es_zip": es_zip,
            "sdk_zip": sdk_zip,
        }

    def _find_download_link(self, html, pattern):
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if not match:
            raise RuntimeError(f"Download link not found for pattern: {pattern}")
        return urllib.parse.urljoin(VOIDTOOLS_DOWNLOADS_URL, match.group(1))

    def _download_text(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": "QuickImage/1.0"})
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _download_file(self, url, target_path):
        request = urllib.request.Request(url, headers={"User-Agent": "QuickImage/1.0"})
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response, open(target_path, "wb") as output:
            while True:
                block = response.read(DOWNLOAD_BLOCK_SIZE)
                if not block:
                    break
                output.write(block)

    def _install_everything(self, installer_path):
        completed = subprocess.run(
            ["msiexec", "/i", installer_path, "/passive", "/norestart"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "msiexec failed").strip())

    def _extract_zip_member(self, zip_path, member_name, output_path):
        wanted_name = member_name.lower()
        with zipfile.ZipFile(zip_path) as archive:
            for item in archive.infolist():
                if os.path.basename(item.filename).lower() != wanted_name:
                    continue
                with archive.open(item) as src, open(output_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                return
        raise RuntimeError(f"{member_name} not found in archive.")

    def _setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass
        
        self.style.configure("Treeview",
            background=self.colors["bg_card"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["bg_card"],
            rowheight=self.tree_rowheight,
            borderwidth=0,
            relief="flat",
            padding=(4, 2),
            font=self.tree_font
        )
        self.style.configure("Treeview.Heading",
            background=self.colors["bg_subtle"],
            foreground=self.colors["text"],
            borderwidth=0,
            relief="flat",
            font=self.heading_font,
            padding=(8, 6)
        )
        self.style.map("Treeview.Heading",
            background=[("active", self.colors["bg_subtle"])],
            relief=[("pressed", "flat"), ("active", "flat")]
        )
        self.style.map("Treeview",
            background=[("selected", self.colors["accent_soft"])],
            foreground=[("selected", self.colors["text"])]
        )
        
        self.style.configure("Vertical.TScrollbar", width=10)

    def _menu(self):
        menu_bg = "#ffffff"
        menu_fg = "#000000"
        menu_active_bg = "#cce8ff"
        menu_active_fg = "#000000"
        
        m = tk.Menu(self, bg=menu_bg, fg=menu_fg, 
                    activebackground=menu_active_bg, activeforeground=menu_active_fg,
                    relief="flat", bd=0)
        
        f = tk.Menu(m, tearoff=0, bg=menu_bg, fg=menu_fg,
                    activebackground=menu_active_bg, activeforeground=menu_active_fg)
        f.add_command(label=self._t("set_source"), command=self._browse)
        f.add_command(label=self._t("set_output"), command=self._browse_output)
        f.add_command(label=self._t("check_deps"), command=self._repair_dependencies)
        lang_menu = tk.Menu(f, tearoff=0, bg=menu_bg, fg=menu_fg,
                            activebackground=menu_active_bg, activeforeground=menu_active_fg)
        lang_menu.add_radiobutton(label=self._t("lang_zh"), value="zh", variable=self.lang_var, command=self._on_language_changed)
        lang_menu.add_radiobutton(label=self._t("lang_en"), value="en", variable=self.lang_var, command=self._on_language_changed)
        f.add_cascade(label=self._t("language"), menu=lang_menu)
        f.add_separator()
        f.add_command(label=self._t("exit"), command=self._quit_app, accelerator="Alt+F4")
        m.add_cascade(label=self._t("menu_file"), menu=f, underline=0)
        
        e = tk.Menu(m, tearoff=0, bg=menu_bg, fg=menu_fg,
                    activebackground=menu_active_bg, activeforeground=menu_active_fg)
        e.add_command(label=self._t("copy_output"), command=self._copy, accelerator="Ctrl+C")
        e.add_separator()
        e.add_command(label=self._t("select_all"), command=self._select_all, accelerator="Ctrl+A")
        e.add_checkbutton(label=self._t("topmost"), variable=self.is_topmost, command=self._toggle_topmost, accelerator="T")
        m.add_cascade(label=self._t("menu_edit"), menu=e, underline=0)
        
        h = tk.Menu(m, tearoff=0, bg=menu_bg, fg=menu_fg,
                    activebackground=menu_active_bg, activeforeground=menu_active_fg)
        h.add_command(label=self._t("help"), command=self._help, accelerator="F1")
        h.add_separator()
        h.add_command(label=self._t("about"), command=self._about, accelerator="Ctrl+F1")
        m.add_cascade(label=self._t("menu_help"), menu=h, underline=0)
        
        self.config(menu=m)
        
        self.bind("<Control-a>", lambda e: self._select_all())
        self.bind("<Control-c>", lambda e: self._copy())
        self.bind("<t>", lambda e: self._toggle_topmost_key())
        self.bind("<T>", lambda e: self._toggle_topmost_key())
        self.bind("<F1>", lambda e: self._help())
        self.bind("<Control-F1>", lambda e: self._about())

    def _ui(self):
        body = tk.Frame(self, bg=self.colors["bg_app"])
        body.pack(
            fill="both",
            expand=True,
            padx=self.spacing["outer"],
            pady=(self.spacing["outer"], 0)
        )

        search_card = tk.Frame(
            body,
            bg=self.colors["bg_card"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        search_card.pack(fill="x", pady=(0, self.spacing["section"]))

        search_frame = tk.Frame(search_card, bg=self.colors["bg_card"])
        search_frame.pack(
            fill="x",
            padx=self.spacing["inner"],
            pady=self.spacing["inner"]
        )
        
        self.entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            bd=0
        )
        self.entry.pack(fill="x", ipady=2)
        self.entry.bind("<KeyRelease>", self._key)
        self.entry.bind("<Return>", lambda e: self._copy())
        self.entry.bind("<Button-1>", self._on_entry_focus)
        self.entry.bind("<FocusIn>", self._on_entry_focus)
        
        list_frame = tk.Frame(
            body,
            bg=self.colors["bg_card"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        list_frame.pack(fill="both", expand=True)
        
        cols = ("name", "path", "size")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended")
        
        self.tree.heading("name", text=self._t("col_name"), anchor="w")
        self.tree.heading("path", text=self._t("col_path"), anchor="w")
        self.tree.heading("size", text=self._t("col_size"), anchor="e")
        
        self.tree.column("name", width=self.default_name_col_width, minwidth=120, anchor="w", stretch=False)
        self.tree.column("path", width=420, minwidth=180, anchor="w", stretch=True)
        self.tree.column("size", width=86, minwidth=70, anchor="e", stretch=False)

        self.tree.tag_configure("base", background=self.colors["bg_card"])
        self.tree.tag_configure("alt", background=self.colors["row_alt"])
        
        self.vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._on_tree_scroll)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Configure>", self._resize_tree_columns)
        list_frame.bind("<Configure>", self._resize_tree_columns)
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        status_frame = tk.Frame(
            self,
            bg=self.colors["bg_card"],
            highlightthickness=1,
            highlightbackground=self.colors["border"]
        )
        status_frame.pack(
            side="bottom",
            fill="x",
            padx=self.spacing["outer"],
            pady=(self.spacing["status_top"], self.spacing["outer"])
        )
        status_top = tk.Frame(status_frame, bg=self.colors["bg_card"])
        status_top.pack(fill="x", padx=8, pady=(4, 0))

        status_bottom = tk.Frame(status_frame, bg=self.colors["bg_card"])
        status_bottom.pack(fill="x", padx=8, pady=(0, 4))
        
        self.status = tk.StringVar(value=self._t("ready"))
        self.source_info = tk.StringVar(value=f"{self._t('source_prefix')}: {self._t('not_set')}")
        self.output_info = tk.StringVar(value=f"{self._t('output_prefix')}: {self._t('not_set')}")
        self.engine_info = tk.StringVar(value=f"{self._t('engine_prefix')}: {self._t('backend_not_ready')}")

        tk.Label(
            status_top,
            textvariable=self.status,
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"],
            anchor="w",
            font=self.status_font,
            pady=1
        ).pack(side="left", fill="x", expand=True)

        tk.Label(
            status_top,
            textvariable=self.engine_info,
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"],
            anchor="e",
            font=self.status_font,
            pady=1
        ).pack(side="right")

        tk.Label(
            status_bottom,
            textvariable=self.source_info,
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"],
            anchor="w",
            font=self.status_font,
            pady=1
        ).pack(side="left", fill="x", expand=True)

        tk.Label(
            status_bottom,
            textvariable=self.output_info,
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"],
            anchor="e",
            font=self.status_font,
            pady=1
        ).pack(side="right")

        self._update_source_status(self.cfg.get("source_path", ""))
        self._update_output_status(self._get_output_dir())
        self._update_engine_status()
        self.after(0, self._resize_tree_columns)

    def _update_name_col_width(self, max_name_px=0):
        self.current_name_col_width = max(self.default_name_col_width, min(max_name_px + 24, self.max_name_col_width))
        self._resize_tree_columns()

    def _resize_tree_columns(self, event=None):
        if not hasattr(self, "tree"):
            return

        total_width = self.tree.winfo_width()
        if total_width <= 1 and event is not None:
            total_width = event.width
        if total_width <= 1:
            return

        size_width = 86
        path_min = 180
        name_width = min(self.current_name_col_width, max(total_width - size_width - path_min, 120))
        path_width = max(total_width - name_width - size_width - 4, path_min)

        self.tree.column("name", width=name_width)
        self.tree.column("path", width=path_width)
        self.tree.column("size", width=size_width)

    def _on_tree_scroll(self, first, last):
        if hasattr(self, "vsb"):
            self.vsb.set(first, last)
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.vsb.grid_remove()
            else:
                self.vsb.grid()

    def _short_path(self, path, max_len=32):
        if not path:
            return self._t("not_set")
        if len(path) <= max_len:
            return path
        head = max_len // 2 - 2
        tail = max_len - head - 3
        return f"{path[:head]}...{path[-tail:]}"

    def _update_source_status(self, path):
        if not hasattr(self, "source_info"):
            return
        self.source_info.set(f"{self._t('source_prefix')}: {self._short_path(path, 28)}")

    def _update_output_status(self, path):
        if not hasattr(self, "output_info"):
            return
        self.output_info.set(f"{self._t('output_prefix')}: {self._short_path(path, 28)}")

    def _update_engine_status(self):
        if not hasattr(self, "engine_info"):
            return
        self.engine_info.set(f"{self._t('engine_prefix')}: {self._backend_label()}")

    def _browse(self):
        p = filedialog.askdirectory()
        if p:
            self.cfg["source_path"] = p
            save_config(self.cfg)
            self._update_source_status(p)
            self.status.set(self._t("source_updated"))

    def _browse_output(self):
        initial_dir = self._get_output_dir()
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

        p = filedialog.askdirectory(initialdir=initial_dir)
        if p:
            self.cfg["output_path"] = os.path.normpath(p)
            save_config(self.cfg)
            output_dir = self._ensure_output_dir()
            self._update_output_status(output_dir)
            self.status.set(self._t("output_updated"))

    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)

    def _toggle_topmost(self):
        self.attributes('-topmost', self.is_topmost.get())

    def _toggle_topmost_key(self):
        self.is_topmost.set(not self.is_topmost.get())
        self._toggle_topmost()

    def _key(self, e):
        if e.keysym in ["Control_L","Control_R","Shift_L","Shift_R","Alt_L","Alt_R","Return"]:
            return
        if not self._ensure_dependencies_before_search():
            return
        self._interrupt_pending_ui_work()
        if self.timer:
            self.after_cancel(self.timer)
        self.timer = self.after(self.search_delay_ms, self._search)

    def _search(self):
        src = self.cfg.get("source_path", "")
        txt = self.entry.get().strip()

        if not src:
            self.search_token += 1
            self.last_search_signature = None
            self._clear_search_queue()
            self.status.set(self._t("source_required"))
            self._update_source_status("")
            return
        if not txt:
            self.search_token += 1
            self.last_search_signature = None
            self._clear_search_queue()
            self._show([], src, "")
            return

        signature = (os.path.normcase(os.path.normpath(src)), txt)
        if signature == self.last_search_signature:
            return

        self.last_search_signature = signature
        self.search_token += 1
        current_token = self.search_token
        self.status.set(self._t("searching"))
        self._enqueue_search(current_token, src, txt)

    def _clear_search_queue(self):
        while True:
            try:
                self.search_queue.get_nowait()
                self.search_queue.task_done()
            except queue.Empty:
                break

    def _enqueue_search(self, token, source_path, query_text):
        self._clear_search_queue()
        try:
            self.search_queue.put_nowait((token, source_path, query_text))
        except queue.Full:
            pass

    def _search_worker_loop(self):
        while True:
            token, source_path, query_text = self.search_queue.get()
            try:
                keywords = parse_keywords(query_text)
                exts = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]
                results = search_images(keywords, source_path, exts, True, max_results=self.max_search_results)
            except Exception:
                results = []
            finally:
                self.search_queue.task_done()

            self.after(
                0,
                lambda t=token, r=results, s=source_path, q=query_text: self._on_search_done(t, r, s, q),
            )

    def _on_search_done(self, token, results, source_path, query_text):
        if token != self.search_token:
            return
        self._show(results, source_path, query_text)

    def _interrupt_pending_ui_work(self):
        if self.render_job:
            self.after_cancel(self.render_job)
            self.render_job = None
        self.render_update_token += 1
        self.size_update_token += 1

    def _on_entry_focus(self, event=None):
        self._interrupt_pending_ui_work()

    def _show(self, res, source_path, query_text=""):
        self.results = res
        self.size_update_token += 1
        current_size_token = self.size_update_token

        self.render_update_token += 1
        current_render_token = self.render_update_token

        if self.render_job:
            self.after_cancel(self.render_job)
            self.render_job = None

        rows = self.tree.get_children()
        if rows:
            self.tree.delete(*rows)

        self._update_source_status(source_path)

        if res:
            total_count = len(res)
            display_count = min(total_count, self.max_display_results)
            render_state = {
                "results": res[:display_count],
                "index": 0,
                "source_path": os.path.normpath(source_path),
                "max_name_px": 0,
                "size_rows": [],
            }

            self._render_result_chunk(render_state, current_render_token, current_size_token)

            if total_count > display_count:
                self.status.set(self._t("display_results").format(display=display_count, total=total_count))
            else:
                self.status.set(self._t("results_count").format(count=total_count))
        else:
            self._update_name_col_width(0)
            if query_text:
                self.status.set(self._t("not_found"))
            else:
                self.status.set(self._t("ready"))

        self._update_engine_status()

    def _render_result_chunk(self, state, render_token, size_token):
        if render_token != self.render_update_token:
            return

        results = state["results"]
        start = state["index"]
        end = min(start + self.render_chunk_size, len(results))
        source_prefix = state["source_path"]
        source_prefix_lower = source_prefix.lower()
        prefix_len = len(source_prefix)

        for idx in range(start, end):
            file_path = results[idx]
            name = os.path.basename(file_path)

            if idx < self.name_measure_limit:
                state["max_name_px"] = max(state["max_name_px"], self.tree_font.measure(name))

            full_dir = os.path.dirname(file_path)
            if full_dir.lower().startswith(source_prefix_lower):
                relative_dir = full_dir[prefix_len:].lstrip(os.sep)
            else:
                relative_dir = full_dir

            display_path = self._short_path(relative_dir, 34)
            row_tag = "alt" if idx % 2 else "base"
            item_id = self.tree.insert("", "end", values=(name, display_path, ""), tags=(row_tag,))

            if idx < self.size_preload_limit:
                state["size_rows"].append((item_id, file_path))

        state["index"] = end

        if end < len(results):
            self.render_job = self.after(
                self.render_interval_ms,
                lambda s=state, rt=render_token, st=size_token: self._render_result_chunk(s, rt, st),
            )
            return

        self.render_job = None
        self._update_name_col_width(state["max_name_px"])
        self._load_sizes_async(state["size_rows"], size_token)

    def _load_sizes_async(self, size_rows, token):
        if not size_rows:
            return
        threading.Thread(target=self._load_sizes_worker, args=(size_rows, token), daemon=True).start()

    def _load_sizes_worker(self, size_rows, token):
        batch = []
        for item_id, file_path in size_rows:
            if token != self.size_update_token:
                return

            batch.append((item_id, self._format_size_kb(file_path)))
            if len(batch) >= 80:
                chunk = batch
                batch = []
                self.after(0, lambda updates=chunk, current=token: self._apply_size_batch(updates, current))

        if batch:
            self.after(0, lambda updates=batch, current=token: self._apply_size_batch(updates, current))

    def _apply_size_batch(self, updates, token):
        if token != self.size_update_token:
            return

        for item_id, size_text in updates:
            if not self.tree.exists(item_id):
                continue
            values = list(self.tree.item(item_id, "values"))
            if len(values) < 3:
                continue
            values[2] = size_text
            self.tree.item(item_id, values=values)

    def _format_size_kb(self, file_path):
        try:
            return f"{os.path.getsize(file_path)//1024:,} KB"
        except:
            return ""

    def _copy_files(self, files):
        if not files:
            return 0
        output_dir = self._ensure_output_dir()
        self._update_output_status(output_dir)

        c = 0
        for s in files:
            try:
                shutil.copy2(s, os.path.join(output_dir, os.path.basename(s)))
                c += 1
            except:
                pass

        self.status.set(self._t("copied").format(count=c))
        return c

    def _copy(self):
        if not self.results:
            return
        self._copy_files(self.results)

    def _help(self):
        messagebox.showinfo(
            self._t("help_title"),
            self._t("help_text"),
            parent=self,
        )

    def _about(self):
        messagebox.showinfo(
            self._t("about_title"),
            self._t("about_text"),
            parent=self,
        )

    def _hotkey(self):
        try:
            import keyboard
            self.mini_win = None
            keyboard.add_hotkey("ctrl+`", self._on_hotkey)
        except:
            pass

    def _on_hotkey(self):
        self.after(0, self._show_mini)

    def _show_mini(self):
        """显示极简浮动搜索框"""
        if self.mini_win and self.mini_win.winfo_exists():
            self.mini_win.destroy()
            self.mini_win = None
            return
        
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
        except:
            x, y = 500, 300
        
        self.mini_win = tk.Toplevel(self)
        self.mini_win.overrideredirect(True)
        self.mini_win.attributes('-topmost', True)
        self.mini_win.configure(bg="#c0c0c0")
        
        # 主容器
        main_frame = tk.Frame(self.mini_win, bg="#f5f5f5")
        main_frame.pack(padx=1, pady=1)
        
        # 顶部标题栏 (可拖动)
        title_bar = tk.Frame(main_frame, bg="#e0e0e0", height=28)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        
        title_label = tk.Label(title_bar, text="QuickImage - by NerionX", bg="#e0e0e0", fg="#555",
                 font=("Segoe UI", 9))
        title_label.pack(side="left", padx=6)
        title_label.bind("<Button-1>", self._mini_drag_start)
        title_label.bind("<B1-Motion>", self._mini_drag_move)
        
        # 只保留关闭按钮
        close_btn = tk.Label(title_bar, text="×", bg="#e0e0e0", fg="#666", 
                             font=("Segoe UI", 14), cursor="hand2", padx=10)
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._close_mini())
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#e81123", fg="white"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#e0e0e0", fg="#666"))
        
        # 搜索输入框 - 字体颜色浅一点
        self.mini_entry = tk.Entry(main_frame, font=("Microsoft YaHei", 14), width=35, 
                                   bg="white", fg="#333", insertbackground="#333",
                                   relief="solid", bd=1)
        self.mini_entry.pack(ipady=8, padx=4, pady=4)
        
        # 底部状态标签 (可拖动)
        self.mini_status = tk.Label(main_frame, text="", bg="#e8e8e8", fg="#666", 
                                    font=("Segoe UI", 9), anchor="w", padx=6, pady=4)
        self.mini_status.pack(fill="x")
        self.mini_status.bind("<Button-1>", self._mini_drag_start)
        self.mini_status.bind("<B1-Motion>", self._mini_drag_move)
        
        # 定位
        self.mini_win.update_idletasks()
        mini_w = self.mini_win.winfo_reqwidth()
        mini_h = self.mini_win.winfo_reqheight()
        x, y = self._clamp_popup_position(mini_w, mini_h, x - mini_w // 2, y - 60)
        self.mini_win.geometry(f"+{x}+{y}")
        
        # 拖动支持
        self._drag_x = 0
        self._drag_y = 0
        title_bar.bind("<Button-1>", self._mini_drag_start)
        title_bar.bind("<B1-Motion>", self._mini_drag_move)
        
        # 事件绑定
        self.mini_entry.bind("<KeyRelease>", self._mini_key)
        self.mini_entry.bind("<Return>", self._mini_enter)
        self.mini_entry.bind("<Escape>", lambda e: self._close_mini())
        
        self.mini_entry.focus_set()
        self.mini_results = []
        self.mini_timer = None

    def _mini_drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _mini_drag_move(self, e):
        x = self.mini_win.winfo_x() + e.x - self._drag_x
        y = self.mini_win.winfo_y() + e.y - self._drag_y
        x, y = self._clamp_popup_position(
            self.mini_win.winfo_width(),
            self.mini_win.winfo_height(),
            x,
            y,
            top_gap=0,
        )
        self.mini_win.geometry(f"+{x}+{y}")

    def _close_mini(self):
        if self.mini_win and self.mini_win.winfo_exists():
            self.mini_win.destroy()
        self.mini_win = None

    def _mini_key(self, e):
        if e.keysym in ["Control_L","Control_R","Shift_L","Shift_R","Alt_L","Alt_R","Return","Escape"]:
            return
        if not self._ensure_dependencies_before_search():
            return
        if self.mini_timer:
            self.after_cancel(self.mini_timer)
        self.mini_timer = self.after(150, self._mini_search)

    def _mini_search(self):
        src = self.cfg.get("source_path", "")
        txt = self.mini_entry.get().strip()
        
        if not src:
            self.mini_status.config(text=self._t("mini_source_required"))
            return
        if not txt:
            self.mini_status.config(text="")
            self.mini_results = []
            return

        def run():
            kws = parse_keywords(txt)
            exts = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]
            res = search_images(kws, src, exts, True, max_results=self.max_search_results)
            self.after(0, lambda: self._mini_show(res))

        threading.Thread(target=run, daemon=True).start()

    def _mini_show(self, res):
        self.mini_results = res
        if res:
            self.mini_status.config(text=self._t("mini_found").format(count=len(res)))
        else:
            self.mini_status.config(text=self._t("mini_not_found"))

    def _mini_enter(self, e):
        if self.mini_results:
            c = self._copy_files(self.mini_results)
            self.mini_status.config(text=self._t("mini_copied").format(count=c))
        else:
            self.mini_status.config(text=self._t("mini_empty"))


if __name__ == "__main__":
    App().mainloop()
