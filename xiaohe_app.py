# -*- coding: utf-8 -*-
"""小鹤双拼编码练习 —— Windows 桌面小程序（仅依赖标准库 tkinter）

屏幕给出汉字和全拼，输入对应的小鹤双拼两键编码。
编码规则与 Rime 官方 double_pinyin_flypy 方案一致：
  声母：zh→V  ch→I  sh→U，其余声母取原字母；y、w 按声母处理（按全拼拼写取韵母）
  韵母：iu=Q ei=W uan=R ue/ve=T un=Y uo=O ie=P ong/iong=S ing/uai=K
        iang/uang=L ai=D en=F eng=G ang=H an=J ou=Z ia/ua=X iao=N
        ao=C ui=V in=B ian=M
  零声母：韵母首字母 + 韵母键（爱 ai→ad、恩 en→ef），er 例外→er

内容：常用 2000 字随机练习，或《道德经》/四书五经整段打字（texts.json）。
主题：跟随系统 / 浅色 / 深色（设置保存在 stats.json）。
"""
import json
import os
import random
import re
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

if getattr(sys, "frozen", False):
    # PyInstaller 打包后：资源在临时解包目录，可写文件放 exe 所在目录
    _BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    _RES_DIR = getattr(sys, "_MEIPASS", _BASE_DIR)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _RES_DIR = _BASE_DIR
APP_DIR = _BASE_DIR
DATA_FILE = os.path.join(_RES_DIR, "xiaohe_data.json")
TEXTS_FILE = os.path.join(_RES_DIR, "texts.json")
ICON_FILE = os.path.join(_RES_DIR, "app.ico")
STATS_FILE = os.path.join(APP_DIR, "stats.json")

YA = "Microsoft YaHei UI"

# ---------- 主题调色板 ----------
LIGHT = dict(
    bg="#eef1f6", panel="#ffffff", fg="#22303f", grey="#8a97a5",
    blue="#1e88e5", orange="#fb8c00", purple="#8e44ad",
    green="#2f9e44", red="#d6453d",
    key_bg="#ffffff", key_mod="#eef2f6", key_border="#cfd8e2",
    ctrl_bg="#e2e8f0", ctrl_active="#d3dce6", ctrl_fg="#22303f",
    select="#ffffff", hl_sub="#dcebff", menu_bg="#ffffff",
)
DARK = dict(
    bg="#1e242c", panel="#272e38", fg="#e8ecf1", grey="#97a3b0",
    blue="#3d8bfd", orange="#f5a623", purple="#a06cd5",
    green="#4caf50", red="#e05a52",
    key_bg="#303945", key_mod="#262e38", key_border="#3c4654",
    ctrl_bg="#2c3540", ctrl_active="#3a4452", ctrl_fg="#e8ecf1",
    select="#3c4654", hl_sub="#bcd9ff", menu_bg="#2b3340",
)

THEMES = [("跟随系统", "system"), ("浅色", "light"), ("深色", "dark")]

SCOPES = [("前 300 字", 300), ("前 600 字", 600),
          ("前 1000 字", 1000), ("前 1500 字", 1500), ("全部 2000 字", None)]

KB_INFO = {
    "Q": "iu", "W": "ei", "E": "e", "R": "uan", "T": "ue", "Y": "un",
    "U": "u·sh", "I": "i·ch", "O": "o·uo", "P": "ie",
    "A": "a", "S": "ong·iong", "D": "ai", "F": "en", "G": "eng",
    "H": "ang", "J": "an", "K": "ing·uai", "L": "iang·uang",
    "Z": "ou", "X": "ia·ua", "C": "ao", "V": "ui·zh", "B": "in",
    "N": "iao", "M": "ian",
}
# 真实键盘布局（ANSI，总键距 15u）：(标签, 键宽u)
KB_ROWS = [
    [("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1), ("6", 1),
     ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1), ("=", 1), ("⌫", 2)],
    [("Tab", 1.5)] + [(c, 1) for c in "QWERTYUIOP"] + [("[", 1), ("]", 1), ("\\", 1.5)],
    [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("'", 1), ("Enter", 2.25)],
    [("Shift", 2.25)] + [(c, 1) for c in "ZXCVBNM"] + [(",", 1), (".", 1), ("/", 1), ("Shift", 2.75)],
    [("Ctrl", 1.25), ("Win", 1.25), ("Alt", 1.25), ("空格", 6.25),
     ("Alt", 1.25), ("Win", 1.25), ("Fn", 1.25), ("Ctrl", 1.25)],
]
KB_UNIT_TOTAL = 15.0

HANZI = re.compile(r"[\u3400-\u9fff]")
PUNCT = "，。？！；：、·—…《》〈〉（）"

SEG_LIMIT = 16          # 段内最多汉字数


def sys_prefers_dark():
    """读取 Windows「应用深色模式」注册表（非 win 平台视为浅色）。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return int(val) == 0
    except Exception:
        return False


def _pre_disable_ime():
    """在本线程首个窗口创建前禁用 IME（仅影响本进程，不影响系统其他窗口）"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        imm32 = ctypes.windll.imm32
        ok = imm32.ImmDisableIME(kernel32.GetCurrentThreadId())
        print(f"IME: ImmDisableIME -> {bool(ok)}", flush=True)
    except Exception as e:
        print("IME: pre-disable failed:", e, flush=True)


class App(tk.Tk):
    def __init__(self):
        _pre_disable_ime()
        super().__init__()
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        self.title("小鹤双拼练习")
        self.geometry("1000x700")
        self.minsize(780, 540)
        try:
            self.iconbitmap(ICON_FILE)
        except Exception:
            pass

        with open(DATA_FILE, encoding="utf-8") as f:
            self.chars = json.load(f)
        self.books = []
        try:
            with open(TEXTS_FILE, encoding="utf-8") as f:
                self.books = json.load(f).get("texts", [])
        except Exception:
            pass

        # 设置 / 统计
        store = self._load_store()
        self.cum = {"practiced": store.get("practiced", 0),
                    "correct": store.get("correct", 0),
                    "wrong": store.get("wrong", 0)}
        self.theme_mode = store.get("theme", "system")
        self.content_id = store.get("content", "chars")
        self.pos_map = store.get("pos", {})

        self.scope_name = tk.StringVar(value="前 1000 字")
        self.theme_name = tk.StringVar(
            value=next((n for n, v in THEMES if v == self.theme_mode),
                       "跟随系统"))
        self.content_name = tk.StringVar(value="常用 2000 字")
        self.show_py = tk.BooleanVar(value=True)
        self.show_kb = tk.BooleanVar(value=True)

        self.typed = ""
        self.cur = None
        self.state = "typing"        # typing / locked_ok / locked_no
        self.started_at = None       # 首次输入时间（计速起点）
        self.answered = 0
        self.ok = 0
        self.bad = 0
        self.streak = 0
        self.best = 0
        self._auto_next_job = None
        self._resize_job = None
        self._cur_eff_dark = None

        # 经典文本模式状态
        self.book = None             # 当前书 dict 或 None
        self.t_ch = 0                # 章下标
        self.t_seg = 0               # 段下标
        self.t_pos = 0               # 段内下一个待输入字（body 绝对下标）
        self.t_segs = []             # 当前章的段 [(s0, s1), ...]
        self.t_ch_counts = []        # 每章段数（缓存）
        self.t_total = 0             # 全书总段数

        self.P = LIGHT               # 当前调色板
        self._build_ui()
        self._apply_theme()
        self._select_content(self.content_id, restore=True)
        self._toggle_kb()
        self.update_idletasks()
        self._rescale()
        self._sync_titlebar()
        self._disable_ime()

        self.bind("<Key>", self.on_key)
        self.bind("<ButtonRelease-1>", lambda e: self.focus_set())
        self.bind("<Configure>", self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(1000, self._tick)

    # ---------- UI ----------
    def _build_ui(self):
        # 上下对半布局：第 2 行（字）与第 3 行（键盘）等权重
        self.grid_rowconfigure(2, weight=1, uniform="half")
        self.grid_rowconfigure(3, weight=1, uniform="half")
        self.grid_columnconfigure(0, weight=1)

        top = tk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 2))
        self.top = top
        self.lb_title = tk.Label(top, text="⌨ 小鹤双拼练习")
        self.lb_title.pack(side="left")

        right = tk.Frame(top)
        right.pack(side="right")
        self.theme_menu = self._mk_menu(right, self.theme_name,
                                        [n for n, _ in THEMES],
                                        self.on_theme_change)
        self.theme_menu.pack(side="left", padx=(0, 10))
        self.content_menu = self._mk_menu(
            right, self.content_name, self._content_names(),
            self.on_content_change)
        self.content_menu.pack(side="left", padx=(0, 10))
        self.scope_menu = self._mk_menu(
            right, self.scope_name, [n for n, _ in SCOPES],
            lambda _v: self.reset_session())
        self.scope_menu.pack(side="left", padx=(0, 10))
        self.cb_py = tk.Checkbutton(right, text="显示拼音",
                                    variable=self.show_py,
                                    command=self._refresh_answer,
                                    takefocus=0)
        self.cb_py.pack(side="left", padx=4)
        self.cb_kb = tk.Checkbutton(right, text="键位图",
                                    variable=self.show_kb,
                                    command=self._toggle_kb, takefocus=0)
        self.cb_kb.pack(side="left", padx=4)
        self.btn_reset = tk.Button(right, text="重新开始",
                                   command=self.reset_session,
                                   relief="flat", takefocus=0, padx=12)
        self.btn_reset.pack(side="left", padx=(10, 0))

        bar = tk.Frame(self)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 0))
        self.bar = bar
        self.lb_scope = tk.Label(bar)
        self.lb_scope.pack(side="left")
        self.lb_stats = tk.Label(bar)
        self.lb_stats.pack(side="left", padx=18)
        self.lb_cum = tk.Label(bar)
        self.lb_cum.pack(side="right")

        self.main = tk.Frame(self)
        self.main.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        # 段落显示（经典模式可见）
        self.t_text = tk.Text(self.main, height=1, wrap="char", bd=0,
                              highlightthickness=0, takefocus=0,
                              cursor="arrow")
        self.t_text.tag_configure("done")
        self.t_text.tag_configure("cur")
        self.t_text.tag_configure("todo")
        self.lb_char = tk.Label(self.main)
        self.lb_char.pack(expand=True)
        self.lb_py = tk.Label(self.main)
        self.lb_py.pack()
        slots = tk.Frame(self.main)
        slots.pack(pady=(4, 0))
        self.slots = slots
        self.slot1 = tk.Label(slots, text="＿")
        self.slot1.pack(side="left", padx=8)
        self.slot2 = tk.Label(slots, text="＿")
        self.slot2.pack(side="left", padx=8)
        self.lb_status = tk.Label(self.main)
        self.lb_status.pack(pady=(2, 0))

        self.kb = tk.Frame(self)
        self.kb.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.lb_rule = tk.Label(
            self.kb, justify="center",
            text="声母 zh→V ch→I sh→U ｜ 零声母 = 韵母首字母 + 韵母键（爱 ai→ad）｜ er 除外 ｜ 空格跳过")
        self.lb_rule.pack(side="bottom", pady=(0, 6))
        self.kcanvas = tk.Canvas(self.kb, highlightthickness=0, bd=0)
        self.kcanvas.pack(fill="both", expand=True)
        self.key_items = {}          # letter -> item ids
        self._kb_draw_job = None
        self.kcanvas.bind("<Configure>", self._on_kb_configure)

    def _mk_menu(self, parent, var, names, command):
        m = tk.OptionMenu(parent, var, *names, command=command)
        m.configure(relief="flat", takefocus=0)
        m["menu"].configure(font=(YA, 11))
        return m

    def _content_names(self):
        names = ["常用 2000 字"]
        names += [b["name"] + ("（选）" if b.get("select") else "")
                  for b in self.books]
        return names

    # ---------- 主题 ----------
    def _sync_titlebar(self):
        """让系统标题栏颜色跟随应用主题（Win11 直接设标题栏色，旧系统退回深色模式开关）"""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            P = self.P

            def colorref(h):
                r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
                return (b << 16) | (g << 8) | r

            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                self.after(300, self._sync_titlebar)
                return
            dwm = ctypes.windll.dwmapi
            cap = ctypes.c_int(colorref(P["bg"]))
            txt = ctypes.c_int(colorref(P["fg"]))
            bor = ctypes.c_int(colorref(P["bg"]))
            if dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(cap), 4) != 0:
                dark = ctypes.c_int(1 if P is DARK else 0)
                if dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), 4) != 0:
                    dwm.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark), 4)
            dwm.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(txt), 4)
            dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(bor), 4)
        except Exception:
            pass

    def on_theme_change(self, _value):
        self.theme_mode = dict(THEMES)[self.theme_name.get()]
        self._save_store()
        self._apply_theme()

    def _eff_dark(self):
        if self.theme_mode == "dark":
            return True
        if self.theme_mode == "system":
            return sys_prefers_dark()
        return False

    def _apply_theme(self):
        self.P = DARK if self._eff_dark() else LIGHT
        self._cur_eff_dark = self._eff_dark()
        P = self.P
        self.configure(bg=P["bg"])
        self.top.configure(bg=P["bg"])
        self.lb_title.configure(bg=P["bg"], fg=P["fg"])
        self.bar.configure(bg=P["bg"])
        self.lb_scope.configure(bg=P["bg"], fg=P["grey"])
        self.lb_stats.configure(bg=P["bg"], fg=P["fg"])
        self.lb_cum.configure(bg=P["bg"], fg=P["grey"])
        for w in (self.theme_menu, self.content_menu, self.scope_menu):
            w.configure(bg=P["ctrl_bg"], fg=P["ctrl_fg"],
                        activebackground=P["ctrl_active"],
                        activeforeground=P["ctrl_fg"])
            w["menu"].configure(bg=P["menu_bg"], fg=P["ctrl_fg"],
                                activebackground=P["ctrl_active"],
                                activeforeground=P["ctrl_fg"])
        for cb in (self.cb_py, self.cb_kb):
            cb.configure(bg=P["bg"], fg=P["fg"], activebackground=P["bg"],
                         selectcolor=P["select"])
        self.btn_reset.configure(bg=P["ctrl_bg"], fg=P["ctrl_fg"],
                                 activebackground=P["ctrl_active"],
                                 activeforeground=P["ctrl_fg"])
        self.main.configure(bg=P["panel"])
        self.t_text.configure(bg=P["panel"], fg=P["fg"],
                              insertbackground=P["fg"])
        self.t_text.tag_configure("done", foreground=P["grey"])
        self.t_text.tag_configure("cur", background=P["blue"],
                                  foreground="#ffffff")
        self.t_text.tag_configure("todo", foreground=P["fg"])
        self.lb_char.configure(bg=P["panel"], fg=P["fg"])
        self.lb_py.configure(bg=P["panel"], fg=P["grey"])
        self.slots.configure(bg=P["panel"])
        for s in (self.slot1, self.slot2, self.lb_status):
            s.configure(bg=P["panel"], fg=P["grey"])
        self.kb.configure(bg=P["bg"])
        self.lb_rule.configure(bg=P["bg"], fg=P["grey"])
        self.kcanvas.configure(bg=P["bg"])
        self._highlight_keys()
        self._sync_titlebar()

    # ---------- 缩放 ----------
    def _rescale(self):
        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)
        s = max(0.55, min(2.2, min(w / 1000.0, h / 700.0)))
        fonts = {
            "title": ((YA, 15, "bold"), (YA, max(13, int(15 * s)), "bold")),
            "stats": ((YA, 12), (YA, max(10, int(12 * s)))),
            "char": ((YA, 82, "bold"), (YA, max(24, int(82 * s)), "bold")),
            "char_text": ((YA, 54, "bold"),
                          (YA, max(18, int(54 * s)), "bold")),
            "py": ((YA, 28), (YA, max(13, int(28 * s)))),
            "py_text": ((YA, 22), (YA, max(11, int(22 * s)))),
            "slot": (("Consolas", 40, "bold"),
                     ("Consolas", max(15, int(40 * s)), "bold")),
            "status": ((YA, 16), (YA, max(11, int(16 * s)))),
            "rule": ((YA, 11), (YA, max(9, int(11 * s)))),
            "ctrl": ((YA, 11), (YA, max(10, int(11 * s)))),
            "text": ((YA, 22), (YA, max(12, int(22 * s)))),
        }
        try:
            self.lb_title.configure(font=fonts["title"][1])
            self.lb_stats.configure(font=fonts["stats"][1])
            self.lb_scope.configure(font=fonts["stats"][0])
            self.lb_cum.configure(font=fonts["stats"][0])
            self.lb_char.configure(
                font=fonts["char_text" if self._is_text_mode()
                           else "char"][1])
            self.lb_py.configure(
                font=fonts["py_text" if self._is_text_mode()
                           else "py"][1])
            self.slot1.configure(font=fonts["slot"][1])
            self.slot2.configure(font=fonts["slot"][1])
            self.lb_status.configure(font=fonts["status"][1])
            self.lb_rule.configure(font=fonts["rule"][0])
            for w2 in (self.theme_menu, self.content_menu, self.scope_menu,
                       self.cb_py, self.cb_kb, self.btn_reset):
                w2.configure(font=fonts["ctrl"][0])
            self.t_text.configure(font=fonts["text"][1],
                                  spacing1=fonts["text"][1][1] // 2)
        except tk.TclError:
            pass

    # ---------- 练习逻辑 ----------
    def _disable_ime(self):
        """兜底：再对本线程当前所有相关窗口解除 IME 关联"""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            imm32 = ctypes.windll.imm32
            for h in (user32.GetParent(self.winfo_id()), self.winfo_id()):
                if h:
                    imm32.ImmAssociateContext(h, None)
            self.after(600, self._disable_ime_focus)
        except Exception:
            pass

    def _disable_ime_focus(self):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            h = user32.GetFocus()
            if h:
                ctypes.windll.imm32.ImmAssociateContext(h, None)
            print(f"IME: focus hwnd {h} disabled", flush=True)
        except Exception:
            pass

    # ----- 内容选择 -----
    def _is_text_mode(self):
        return self.book is not None

    def _select_content(self, cid, restore=False):
        self.book = next((b for b in self.books
                          if b["id"] == cid and b.get("chapters")), None)
        self.content_id = cid if self.book else "chars"
        if self.book is None:
            self.content_name.set("常用 2000 字")
            self.scope_menu.pack(side="left", padx=(0, 10),
                                 before=self.cb_py)
            self.t_text.pack_forget()
        else:
            name = self.book["name"] + ("（选）" if self.book.get("select")
                                        else "")
            self.content_name.set(name)
            self.scope_menu.pack_forget()
            self.t_text.pack(fill="x", pady=(2, 0),
                             before=self.lb_char)
            ch = self.pos_map.get(self.content_id, [0, 0]) if restore else [0, 0]
            self.t_ch, self.t_seg = ch[0], ch[1]
            self._cache_book()
            self._load_segments()
            self.t_pos = 0
        self._save_store()
        self._rescale()
        self.reset_session(keep_pos=restore)

    def on_content_change(self, value):
        name = value.replace("（选）", "")
        cid = next((b["id"] for b in self.books if b["name"] == name),
                   "chars")
        self._select_content(cid)

    def _chapters(self):
        return self.book["chapters"] if self.book else []

    def _chapter(self):
        chs = self._chapters()
        return chs[self.t_ch] if chs else None

    def _cache_book(self):
        self.t_ch_counts = [len(self._segments_of(c["body"]))
                            for c in self._chapters()]
        self.t_total = sum(self.t_ch_counts)

    def _segments_of(self, body):
        """把章正文切成 ≤SEG_LIMIT 个汉字的段（标点跟随前段）。"""
        segs, start, count = [], 0, 0
        for i, ch in enumerate(body):
            if ch in PUNCT:
                if count > 0:
                    segs.append((start, i + 1))
                    start, count = i + 1, 0
                else:
                    start = i + 1
            elif HANZI.fullmatch(ch):
                count += 1
                if count >= SEG_LIMIT:
                    segs.append((start, i + 1))
                    start, count = i + 1, 0
        if start < len(body) and count > 0:
            segs.append((start, len(body)))
        return segs

    def _load_segments(self):
        chs = self._chapters()
        self.t_ch = max(0, min(self.t_ch, len(chs) - 1)) if chs else 0
        ch = self._chapter()
        self.t_segs = self._segments_of(ch["body"]) if ch else []
        if self.t_seg >= len(self.t_segs):
            self.t_seg = 0

    # ----- 出题 -----
    def _scoped(self):
        n = dict(SCOPES)[self.scope_name.get()]
        return self.chars if n is None else self.chars[:n]

    def _expected(self):
        """返回 (双拼码, 当前汉字, 拼音显示)；无内容时 ("", "", "")。"""
        if not self._is_text_mode():
            if self.cur is None:
                return "", "", ""
            return self.cur["f"], self.cur["c"], self.cur["p"]
        ch = self._chapter()
        if ch is None:
            return "", "", ""
        s0, s1 = self.t_segs[self.t_seg]
        i = self.t_pos
        body = ch["body"]
        while i < s1 and not HANZI.fullmatch(body[i]):
            i += 1
        self.t_pos = i
        if i >= s1:
            return "", "", ""
        pyl = ch["pyl"]
        ent = pyl[i] if i < len(pyl) else None
        return (ent[1] if ent else "", body[i], ent[0] if ent else "")

    def _advance_text(self):
        """推进到下一个待练字；返回 True 表示有效。"""
        chs = self._chapters()
        if not chs:
            return False
        for _ in range(self.t_total + len(chs) + 2):
            if self.t_seg >= len(self.t_segs):
                self.t_ch = (self.t_ch + 1) % len(chs)
                self._load_segments()
                self.t_pos = 0
                self._save_text_pos()
                continue
            s0, s1 = self.t_segs[self.t_seg]
            if self.t_pos < s0:
                self.t_pos = s0        # 进入新段：从段首起
            i = self.t_pos
            body = self._chapter()["body"]
            while i < s1 and not HANZI.fullmatch(body[i]):
                i += 1
            if i < s1:
                self.t_pos = i
                return True
            self.t_seg += 1
            self.t_pos = 0
            self._save_text_pos()
        return False

    def _next_char(self, first=False):
        self._cancel_auto()
        self.typed = ""
        self.state = "typing"
        if self._is_text_mode():
            if not self._advance_text():
                self.book = None
                return self._select_content("chars")
            self.lb_char.configure(text=self._expected()[1])
            self._render_segment()
        else:
            pool = self._scoped() or self.chars
            last = None if first or self.cur is None else self.cur["c"]
            while True:
                self.cur = random.choice(pool)
                if last is None or self.cur["c"] != last or len(pool) < 2:
                    break
            self.lb_char.configure(text=self.cur["c"])
        self._refresh_answer()
        self.slot1.configure(text="＿", fg=self.P["grey"])
        self.slot2.configure(text="＿", fg=self.P["grey"])
        self.lb_status.configure(text="输入两键编码", fg=self.P["grey"])
        self._refresh_stats()
        self._highlight_keys()

    def _refresh_answer(self):
        code, _disp, py = self._expected()
        if not code:
            return
        if self.show_py.get() or self.state != "typing":
            self.lb_py.configure(text=py)
        else:
            self.lb_py.configure(text="· ·（拼音已隐藏）")

    def _render_segment(self):
        ch = self._chapter()
        if ch is None:
            return
        s0, s1 = self.t_segs[self.t_seg]
        t = self.t_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("1.0", ch["body"][s0:s1])
        e = self.t_pos
        body = ch["body"]
        for i in range(s0, s1):
            tag = "done" if i < e else ("cur" if i == e else None)
            if tag:
                t.tag_add(tag, f"1.{i - s0}", f"1.{i - s0 + 1}")
        if e > s0:
            t.tag_add("done", "1.0", f"1.{min(e, s1) - s0}")
        t.configure(state="disabled")
        self._refresh_scope_label()

    def _save_text_pos(self):
        if self._is_text_mode():
            self.pos_map[self.content_id] = [self.t_ch, self.t_seg]
            self._save_store()

    def _toggle_kb(self):
        if self.show_kb.get():
            self.kb.grid()
            self.main.grid(row=2, column=0, rowspan=1, sticky="nsew",
                           padx=16, pady=8)
        else:
            # 隐藏键盘后字区跨两行占满整个窗口，不留空白
            self.kb.grid_remove()
            self.main.grid(row=2, column=0, rowspan=2, sticky="nsew",
                           padx=16, pady=8)
        self._highlight_keys()

    def _highlight_keys(self):
        code = self._expected()[0]
        self._draw_keyboard(code[:1].upper(), code[1:2].upper())

    def _expect_pair(self):
        code = self._expected()[0]
        return (code[0], code[1]) if len(code) == 2 else ("", "")

    def _give_up(self):
        c0, c1 = self._expect_pair()
        if not c0:
            return
        self.answered += 1
        self.bad += 1
        self.streak = 0
        self.cum["practiced"] += 1
        self.cum["wrong"] += 1
        self.state = "locked_no"
        self.slot1.configure(text=c0, fg=self.P["orange"])
        self.slot2.configure(text=c1, fg=self.P["orange"])
        self.lb_status.configure(
            text=f"已跳过 · 正确编码：{c0} {c1}（空格继续）",
            fg=self.P["grey"])
        self._refresh_stats()
        self._save_store()
        self._auto_next_job = self.after(2600, self._continue)

    def on_key(self, event):
        ks = event.keysym
        if ks in ("space", "Return", "KP_Enter"):
            if self.state == "typing":
                self._give_up()
            elif self.state == "locked_no":
                self._continue()
            return "break"
        ch = event.char.lower()
        if ch not in "abcdefghijklmnopqrstuvwxyz":
            return
        if self.state == "locked_ok":
            return
        if self.state == "locked_no":
            self._continue()
            return
        if self.started_at is None:
            self.started_at = time.time()
        self.typed += ch
        if len(self.typed) == 1:
            self.slot1.configure(text=self.typed, fg=self.P["blue"])
        else:
            self.slot2.configure(text=self.typed[1], fg=self.P["orange"])
            self._judge()

    def _judge(self):
        c0, c1 = self._expect_pair()
        if not c0:
            return
        expected = c0 + c1
        self.answered += 1
        self.cum["practiced"] += 1
        if self.typed == expected:
            self.ok += 1
            self.streak += 1
            self.best = max(self.best, self.streak)
            self.cum["correct"] += 1
            self.state = "locked_ok"
            self.slot1.configure(text=expected[0], fg=self.P["green"])
            self.slot2.configure(text=expected[1], fg=self.P["green"])
            msg = "✓ 正确！"
            if self.streak >= 3:
                msg += f"  连对 {self.streak}"
            self.lb_status.configure(text=msg, fg=self.P["green"])
            self._refresh_stats()
            self._save_store()
            self._auto_next_job = self.after(300 if self._is_text_mode()
                                             else 420, self._continue)
        else:
            self.bad += 1
            self.streak = 0
            self.cum["wrong"] += 1
            self.state = "locked_no"
            self.slot1.configure(text=self.typed[0], fg=self.P["red"])
            self.slot2.configure(text=self.typed[1], fg=self.P["red"])
            self.lb_status.configure(
                text=f"✗ 正确编码：{expected[0]} {expected[1]}（空格继续）",
                fg=self.P["red"])
            self._refresh_answer()
            self._refresh_stats()
            self._save_store()
            self._auto_next_job = self.after(2600, self._continue)

    def _continue(self):
        if self._auto_next_job is not None:
            self.after_cancel(self._auto_next_job)
            self._auto_next_job = None
        if self._is_text_mode():
            self.t_pos += 1
        self._next_char()

    def _cancel_auto(self):
        if self._auto_next_job is not None:
            self.after_cancel(self._auto_next_job)
            self._auto_next_job = None

    def reset_session(self, keep_pos=False):
        self._cancel_auto()
        self.answered = self.ok = self.bad = 0
        self.streak = 0
        self.started_at = None
        if self._is_text_mode() and not keep_pos:
            self.t_ch = 0
            self.t_seg = 0
            self._load_segments()
            self.t_pos = 0
            self._save_text_pos()
        self._next_char()

    def _refresh_scope_label(self):
        if self._is_text_mode():
            ch = self._chapter()
            done = sum(self.t_ch_counts[:self.t_ch]) + self.t_seg + 1
            self.lb_scope.configure(
                text=f"{self.book['name']} · {ch['t']} · 第 {done}/{self.t_total} 段")
        else:
            self.lb_scope.configure(text=f"词库 {len(self._scoped())} 字")

    def _refresh_stats(self):
        acc = self.ok / self.answered * 100 if self.answered else 0
        spd = "—"
        if self.started_at and self.answered:
            sec = time.time() - self.started_at
            if sec > 8:
                spd = f"{self.answered / (sec / 60):.0f} 字/分"
        self.lb_stats.configure(
            text=f"✓ {self.ok}   ✗ {self.bad}   连对 {self.streak}"
                 f"（最佳 {self.best}）   正确率 {acc:.0f}%   速度 {spd}")
        c = self.cum
        cacc = c["correct"] / c["practiced"] * 100 if c["practiced"] else 0
        self._refresh_scope_label()
        self.lb_cum.configure(
            text=f"累计已练 {c['practiced']} 字 · 正确率 {cacc:.0f}%")

    def _tick(self):
        try:
            # 跟随系统主题：轮询注册表变化
            if self.theme_mode == "system":
                dark = sys_prefers_dark()
                if dark != self._cur_eff_dark:
                    self._apply_theme()
            self._refresh_stats()
        except tk.TclError:
            return
        self.after(1000, self._tick)

    # ---------- 键盘图（真实 ANSI 布局，圆角键帽） ----------
    @staticmethod
    def _round_pts(x0, y0, x1, y1, r, seg=6):
        """圆角矩形的平滑多边形顶点"""
        import math
        r = max(2, min(r, (x1 - x0) / 2 - 1, (y1 - y0) / 2 - 1))
        pts = []
        corners = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0),
                   (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
        for cx, cy, a0 in corners:
            for t in range(seg + 1):
                a = math.radians(a0 + 90 * t / seg)
                pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        return pts

    def _draw_keyboard(self, k1, k2, event=None):
        c = self.kcanvas
        P = self.P
        W, H = c.winfo_width(), c.winfo_height()
        if W < 60 or H < 50:
            return
        c.delete("all")
        self.key_items = {}
        pitch = W / KB_UNIT_TOTAL
        gap = max(2, pitch * 0.04)
        vgap = max(3, H * 0.018)
        key_h = min((H - (len(KB_ROWS) - 1) * vgap) / len(KB_ROWS), 120)
        rad = max(3, key_h * 0.22)
        f_letter = ("Consolas", max(8, int(key_h * 0.24)), "bold")
        f_sub = (YA, max(7, int(key_h * 0.15)))
        f_mod = (YA, max(7, int(key_h * 0.17)))
        f_alt = ("Consolas", max(7, int(key_h * 0.20)), "bold")
        y = 0.0
        for row in KB_ROWS:
            x = 0.0
            for label, units in row:
                x0 = x * pitch + gap
                x1 = (x + units) * pitch - gap
                y0, y1 = y, y + key_h
                letter = (len(label) == 1 and label.isalpha()
                          and label.isupper())
                if letter and label == k1 == k2:
                    bg, fg, sfg = P["purple"], "#ffffff", "#ffffff"
                elif letter and label == k1:
                    bg, fg, sfg = P["blue"], "#ffffff", P["hl_sub"]
                elif letter and label == k2:
                    bg, fg, sfg = P["orange"], "#ffffff", P["hl_sub"]
                elif letter:
                    bg, fg, sfg = P["key_bg"], P["fg"], P["grey"]
                else:
                    bg, fg, sfg = P["key_mod"], P["grey"], P["grey"]
                outline = bg if letter else P["key_border"]
                c.create_polygon(
                    *self._round_pts(x0, y0, x1, y1, rad),
                    smooth=True, fill=bg, outline=outline, width=1)
                cx = (x0 + x1) / 2
                if letter:
                    c.create_text(cx, y0 + key_h * 0.30, text=label,
                                  font=f_letter, fill=fg)
                    sub = KB_INFO[label]
                    if label in ("U", "I", "V"):
                        # 声母 sh / ch / zh 用红色醒目标出
                        left, ini = sub.split("·", 1)
                        fm = tkfont.Font(font=f_sub)
                        lw, rw = fm.measure(left), fm.measure(ini)
                        start = cx - (lw + rw) / 2
                        ini_c = "#ff9d94" if bg != P["key_bg"] else P["red"]
                        c.create_text(start, y0 + key_h * 0.70, text=left,
                                      font=f_sub, fill=sfg, anchor="w")
                        c.create_text(start + lw, y0 + key_h * 0.70, text=ini,
                                      font=f_sub, fill=ini_c, anchor="w")
                    else:
                        c.create_text(cx, y0 + key_h * 0.70, text=sub,
                                      font=f_sub, fill=sfg)
                elif label == "空格":
                    c.create_text(cx, (y0 + y1) / 2, text="空格 · 跳过",
                                  font=f_mod, fill=fg)
                else:
                    c.create_text(cx, (y0 + y1) / 2, text=label,
                                  font=f_alt if len(label) <= 2 else f_mod,
                                  fill=fg)
                x += units
            y += key_h + vgap

    def _on_kb_configure(self, event):
        if self._kb_draw_job is not None:
            self.after_cancel(self._kb_draw_job)
        self._kb_draw_job = self.after(60, self._highlight_keys)

    # ---------- 持久化 / 缩放 ----------
    def _load_store(self):
        try:
            with open(STATS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_store(self):
        data = {"practiced": self.cum["practiced"],
                "correct": self.cum["correct"],
                "wrong": self.cum["wrong"],
                "theme": self.theme_mode,
                "content": self.content_id,
                "pos": self.pos_map}
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._rescale)

    def on_close(self):
        self._save_store()
        if self._auto_next_job is not None:
            self.after_cancel(self._auto_next_job)
        self.destroy()


def main():
    if not os.path.exists(DATA_FILE):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("小鹤双拼练习", f"缺少数据文件：\n{DATA_FILE}")
        return
    App().mainloop()


if __name__ == "__main__":
    main()
