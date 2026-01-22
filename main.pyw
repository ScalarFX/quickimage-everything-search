"""
QuickImage - 极简图片搜索 (Everything 风格)
使用 .pyw 扩展名隐藏控制台窗口
"""
import os
import shutil
import threading
import time
import tkinter as tk
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
from search_engine import search_images, parse_keywords

# 系统托盘支持
try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "每日JIT")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.cfg = load_config()
        
        self.title("QuickImage")
        self.geometry("1024x680")
        self.minsize(600, 400)
        self.configure(bg="white")
        
        # 启动时隐藏主窗口
        self.withdraw()
        
        # 图标
        self.icon_path = os.path.join(os.path.dirname(__file__), "i.png")
        if os.path.exists(self.icon_path):
            try:
                img = tk.PhotoImage(file=self.icon_path)
                self.iconphoto(True, img)
            except:
                pass
        
        self._setup_styles()
        
        self.results = []
        self.timer = None
        self.is_topmost = tk.BooleanVar(value=False)  # 默认不置顶
        self.tray_icon = None
        
        self._menu()
        self._ui()
        self._setup_tray()
        
        # 最小化时隐藏到托盘
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.bind("<Unmap>", self._on_minimize)
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 延迟加载全局热键（加速启动）
        self.after(1000, self._hotkey)

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
            pystray.MenuItem("显示主窗口", self._show_from_tray),
            pystray.MenuItem("退出", self._quit_app)
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
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('vista')
        
        self.style.configure("Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            rowheight=26,
            font=("Segoe UI", 10)
        )
        self.style.configure("Treeview.Heading",
            font=("Microsoft YaHei", 9),
            padding=(5, 4)
        )
        self.style.map("Treeview",
            background=[("selected", "#cce8ff")],
            foreground=[("selected", "black")]
        )
        
        self.style.configure("Vertical.TScrollbar", width=14)

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
        f.add_command(label="设置源目录(O)...", command=self._browse)
        f.add_separator()
        f.add_command(label="退出(X)", command=self._quit_app, accelerator="Alt+F4")
        m.add_cascade(label="文件(F)", menu=f, underline=0)
        
        e = tk.Menu(m, tearoff=0, bg=menu_bg, fg=menu_fg,
                    activebackground=menu_active_bg, activeforeground=menu_active_fg)
        e.add_command(label="复制到桌面(C)", command=self._copy, accelerator="Ctrl+C")
        e.add_separator()
        e.add_command(label="全选(A)", command=self._select_all, accelerator="Ctrl+A")
        e.add_checkbutton(label="窗口置顶(T)", variable=self.is_topmost, command=self._toggle_topmost, accelerator="T")
        m.add_cascade(label="编辑(E)", menu=e, underline=0)
        
        h = tk.Menu(m, tearoff=0, bg=menu_bg, fg=menu_fg,
                    activebackground=menu_active_bg, activeforeground=menu_active_fg)
        h.add_command(label="帮助(H)", command=self._help, accelerator="F1")
        h.add_separator()
        h.add_command(label="关于 QuickImage(A)...", command=self._about, accelerator="Ctrl+F1")
        m.add_cascade(label="帮助(H)", menu=h, underline=0)
        
        self.config(menu=m)
        
        self.bind("<Control-a>", lambda e: self._select_all())
        self.bind("<Control-c>", lambda e: self._copy())
        self.bind("<t>", lambda e: self._toggle_topmost_key())
        self.bind("<T>", lambda e: self._toggle_topmost_key())
        self.bind("<F1>", lambda e: self._help())
        self.bind("<Control-F1>", lambda e: self._about())

    def _ui(self):
        search_frame = tk.Frame(self, bg="white")
        search_frame.pack(fill="x", padx=3, pady=4)
        
        self.entry = tk.Entry(search_frame, font=("Segoe UI", 12), relief="solid", bd=1)
        self.entry.pack(fill="x", ipady=4)
        self.entry.bind("<KeyRelease>", self._key)
        self.entry.bind("<Return>", lambda e: self._copy())
        
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        cols = ("name", "path", "size", "date")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended")
        
        self.tree.heading("name", text="名称", anchor="w")
        self.tree.heading("path", text="路径", anchor="w")
        self.tree.heading("size", text="大小", anchor="e")
        self.tree.heading("date", text="修改时间", anchor="w")
        
        self.tree.column("name", width=180, minwidth=100, anchor="w")
        self.tree.column("path", width=480, minwidth=200, anchor="w")
        self.tree.column("size", width=90, minwidth=70, anchor="e")
        self.tree.column("date", width=160, minwidth=140, anchor="w")
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        status_frame = tk.Frame(self, bg="#f0f0f0", height=24, relief="sunken", bd=1)
        status_frame.pack(side="bottom", fill="x")
        status_frame.pack_propagate(False)
        
        self.status = tk.StringVar(value="")
        tk.Label(status_frame, textvariable=self.status, bg="#f0f0f0", fg="#333", 
                 anchor="w", font=("Segoe UI", 9), padx=5).pack(fill="both", expand=True)

    def _browse(self):
        p = filedialog.askdirectory()
        if p:
            self.cfg["source_path"] = p
            save_config(self.cfg)
            self.status.set(f"源目录: {p}")

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
        if self.timer:
            self.after_cancel(self.timer)
        self.timer = self.after(150, self._search)

    def _search(self):
        src = self.cfg.get("source_path", "")
        txt = self.entry.get().strip()
        
        if not src:
            self.status.set("请先设置源目录 (文件 → 设置源目录)")
            return
        if not txt:
            self._show([], src)
            return

        def run():
            kws = parse_keywords(txt)
            exts = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]
            res = search_images(kws, src, exts, True)
            self.after(0, lambda: self._show(res, src))

        threading.Thread(target=run, daemon=True).start()

    def _show(self, res, source_path):
        self.results = res
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        if res:
            prefix = os.path.normpath(source_path)
            prefix_len = len(prefix)
            
            for fp in res:
                nm = os.path.basename(fp)
                full_dir = os.path.dirname(fp)
                if full_dir.lower().startswith(prefix.lower()):
                    pt = full_dir[prefix_len:].lstrip(os.sep)
                else:
                    pt = full_dir
                
                try:
                    sz = f"{os.path.getsize(fp)//1024:,} KB"
                    dt = time.strftime("%Y/%m/%d %H:%M", time.localtime(os.path.getmtime(fp)))
                except:
                    sz, dt = "", ""
                self.tree.insert("", "end", values=(nm, pt, sz, dt))
            self.status.set(f"{len(res):,} 个对象")
        else:
            self.status.set("")

    def _copy(self):
        if not self.results:
            return
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        c = 0
        for s in self.results:
            try:
                shutil.copy2(s, os.path.join(OUTPUT_DIR, os.path.basename(s)))
                c += 1
            except:
                pass
        self.status.set(f"已复制 {c} 个文件到 每日JIT")

    def _show_dialog(self, title, msg):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg="white")
        
        frame = tk.Frame(dlg, bg="white", padx=25, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text=msg, justify="left", font=("Microsoft YaHei", 10), bg="white").pack(anchor="w")
        
        btn_frame = tk.Frame(dlg, bg="#f0f0f0", pady=10)
        btn_frame.pack(fill="x", side="bottom")
        ttk.Button(btn_frame, text="确定", width=10, command=dlg.destroy).pack()
        
        dlg.update_idletasks()
        dw, dh = dlg.winfo_width(), dlg.winfo_height()
        px, py = self.winfo_x(), self.winfo_y()
        pw, ph = self.winfo_width(), self.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        dlg.geometry(f"+{x}+{y}")
        
        dlg.wait_window()

    def _help(self):
        self._show_dialog("帮助", 
            "使用方法:\n\n"
            "1. 文件 → 设置源目录\n"
            "2. 输入精确文件名 (空格分隔多个)\n"
            "3. 按 Enter/Ctrl+C 复制到桌面/每日JIT\n"
            "4. Ctrl+` 打开悬浮搜索框\n\n"
            "快捷键:\n"
            "Ctrl+` - 悬浮搜索框\n"
            "Ctrl+A - 全选\n"
            "Ctrl+C/Enter - 复制\n"
            "T - 切换置顶\n"
            "Esc - 关闭悬浮框")

    def _about(self):
        self._show_dialog("关于 QuickImage", 
            "QuickImage v1.0\n\n"
            "极简图片搜索工具\n"
            "基于 Everything 搜索引擎\n\n"
            "© NerionX")

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
        self.mini_win.geometry(f"+{x-200}+{y-60}")
        
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
        self.mini_win.geometry(f"+{x}+{y}")

    def _close_mini(self):
        if self.mini_win and self.mini_win.winfo_exists():
            self.mini_win.destroy()
        self.mini_win = None

    def _mini_key(self, e):
        if e.keysym in ["Control_L","Control_R","Shift_L","Shift_R","Alt_L","Alt_R","Return","Escape"]:
            return
        if self.mini_timer:
            self.after_cancel(self.mini_timer)
        self.mini_timer = self.after(150, self._mini_search)

    def _mini_search(self):
        src = self.cfg.get("source_path", "")
        txt = self.mini_entry.get().strip()
        
        if not src:
            self.mini_status.config(text="未设置源目录")
            return
        if not txt:
            self.mini_status.config(text="")
            self.mini_results = []
            return

        def run():
            kws = parse_keywords(txt)
            exts = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]
            res = search_images(kws, src, exts, True)
            self.after(0, lambda: self._mini_show(res))

        threading.Thread(target=run, daemon=True).start()

    def _mini_show(self, res):
        self.mini_results = res
        if res:
            self.mini_status.config(text=f"找到 {len(res)} 个文件，按 Enter 复制")
        else:
            self.mini_status.config(text="未找到")

    def _mini_enter(self, e):
        if self.mini_results:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            c = 0
            for s in self.mini_results:
                try:
                    shutil.copy2(s, os.path.join(OUTPUT_DIR, os.path.basename(s)))
                    c += 1
                except:
                    pass
            self.mini_status.config(text=f"已复制 {c} 个文件")
        else:
            self.mini_status.config(text="无文件可复制")


if __name__ == "__main__":
    App().mainloop()
