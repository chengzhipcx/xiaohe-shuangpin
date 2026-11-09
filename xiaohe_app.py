# -*- coding: utf-8 -*-
"""小鹤双拼编码练习 —— Windows 桌面小程序（仅依赖标准库 tkinter）

屏幕给出汉字和全拼，输入对应的小鹤双拼两键编码。
编码规则与 Rime 官方 double_pinyin_flypy 方案一致：
  声母：zh→V  ch→I  sh→U，其余声母取原字母；y、w 按声母处理（按全拼拼写取韵母）
  韵母：iu=Q ei=W uan=R ue/ve=T un=Y uo=O ie=P ong/iong=S ing/uai=K
        iang/uang=L ai=D en=F eng=G ang=H an=J ou=Z ia/ua=X iao=N
        ao=C ui=V in=B ian=M
  零声母：韵母首字母 + 韵母键（爱 ai→ad、恩 en→ef），er 例外→er

内容：常用 2000 字随机练习、错字练习（错题本）、自定义文本（粘贴/导入），
      或《道德经》/《弟子规》/《黄帝内经》/四书五经整段打字（texts.json）。
主题：跟随系统 / 浅色 / 深色；打字音效可开关（音效勾选框）。
暂停：Ctrl+P 或按钮暂停休息，计时冻结、按键屏蔽，任意键继续。
挑战：统计栏「60 秒挑战」限时测速，结束出成绩单；历史按钮看打卡曲线。
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
if sys.platform != "win32" and getattr(sys, "frozen", False):
    # mac .app / Linux 二进制所在目录通常不可写：统计与设置放用户目录
    APP_DIR = os.path.join(os.path.expanduser("~"), ".xiaohe-shuangpin")
    os.makedirs(APP_DIR, exist_ok=True)
DATA_FILE = os.path.join(_RES_DIR, "xiaohe_data.json")
TEXTS_FILE = os.path.join(_RES_DIR, "texts.json")
ICON_FILE = os.path.join(_RES_DIR, "app.ico")
STATS_FILE = os.path.join(APP_DIR, "stats.json")
CUSTOM_FILE = os.path.join(APP_DIR, "custom_text.txt")

# 跨平台字体：中文界面字体 + 等宽编码字体
if sys.platform == "darwin":
    YA, MONO = "PingFang SC", "Menlo"
elif sys.platform == "win32":
    YA, MONO = "Microsoft YaHei UI", "Consolas"
else:
    YA, MONO = "Noto Sans CJK SC", "DejaVu Sans Mono"

# ---------- 主题调色板 ----------
LIGHT = dict(
    bg="#eef1f6", panel="#ffffff", fg="#22303f", grey="#8a97a5",
    blue="#1e88e5", orange="#fb8c00", purple="#8e44ad",
    green="#2f9e44", red="#d6453d",
    key_bg="#ffffff", key_mod="#eef2f6", key_border="#cfd8e2",
    ctrl_bg="#e2e8f0", ctrl_active="#d3dce6", ctrl_fg="#22303f",
    select="#ffffff", hl_sub="#dcebff", menu_bg="#ffffff",
    ok_bg="#e2f5e9", bad_bg="#fde9e7",
)
DARK = dict(
    bg="#1e242c", panel="#272e38", fg="#e8ecf1", grey="#97a3b0",
    blue="#3d8bfd", orange="#f5a623", purple="#a06cd5",
    green="#4caf50", red="#e05a52",
    key_bg="#303945", key_mod="#262e38", key_border="#3c4654",
    ctrl_bg="#2c3540", ctrl_active="#3a4452", ctrl_fg="#e8ecf1",
    select="#3c4654", hl_sub="#bcd9ff", menu_bg="#2b3340",
    ok_bg="#1d3d2b", bad_bg="#4d2622",
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
WRONG_CAP = 80          # 错字本上限（保留最近答错的）
CHALLENGE_SECS = 60     # 限时挑战时长（秒）
HISTORY_KEEP = 400      # 每日统计保留天数


# ---------- 打字音效：运行时合成 wav（无音频文件/第三方依赖） ----------
def _sfx_tone(freq, ms, vol=0.4, decay=4.0):
    """8000Hz 16bit 单音采样（指数衰减），返回原始 PCM 字节。"""
    import math
    import struct
    n = max(1, int(8000 * ms / 1000))
    out = bytearray()
    for i in range(n):
        s = vol * (0.5 ** (i / n * decay)) * math.sin(2 * math.pi * freq * i / 8000)
        out += struct.pack("<h", max(-32768, min(32767, int(s * 32767))))
    return bytes(out)


def _sfx_wav(*parts):
    """把 PCM 片段包成最小可用 wav 文件字节。"""
    import struct
    payload = b"".join(parts)
    return (b"RIFF" + struct.pack("<I", len(payload) + 36) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, 8000, 16000, 2, 16) +
            b"data" + struct.pack("<I", len(payload)) + payload)


def _sfx_build():
    return {
        "tick": _sfx_wav(_sfx_tone(1800, 14, 0.15)),          # 击键轻响
        "ok": _sfx_wav(_sfx_tone(1050, 35, 0.32),             # 答对双音上扬
                       _sfx_tone(1450, 55, 0.32)),
        "bad": _sfx_wav(_sfx_tone(210, 130, 0.42)),           # 答错低鸣
    }


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
        self._char_map = {c["c"]: c for c in self.chars}
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
        self.sfx_on = tk.BooleanVar(value=store.get("sfx", True))
        self.history = store.get("history", {})   # 每日: practiced/correct/time
        self._sfx = None                          # 惰性生成的音效 wav
        self._last_answer_ts = None               # 上一题作答时刻（记历史用时）
        self._custom_book = None                  # 自定义文本构建后的书
        # 限时挑战
        self.challenge_end = None
        self.ch_answered = 0
        self.ch_ok = 0
        self.ch_wrong = []

        self.typed = ""
        self.cur = None
        self.state = "typing"        # typing / locked_ok / locked_no
        self.started_at = None       # 首次输入时间（计速起点）
        self.paused_at = None        # 暂停时刻（None = 未暂停）
        self.paused_total = 0.0      # 本轮累计暂停时长（不计入速度）
        self._status_size = 16       # 状态栏字号（_rescale 时更新）
        self.answered = 0
        self.ok = 0
        self.bad = 0
        self.streak = 0
        self.best = 0
        self._auto_next_job = None
        self._resize_job = None
        self._cur_eff_dark = None
        self._pending_key = ""       # 答对锁定期间缓存的下一字键（最多2键）
        self._store_dirty = False
        self._just_wrapped = False
        self.wrong_recent = [        # 错字本（跨会话，两种模式都记）
            self._char_map[h] for h in store.get("wrong_chars", [])
            if h in self._char_map][:WRONG_CAP]
        self._flash_job = None       # 对/错底色闪烁定时器
        self._zero_job = None        # 错字清零后回常用字的定时器
        # 键盘增量重绘状态
        self._kb_keys = {}           # letter -> (poly, 主文字, 子标注ids)
        self._kb_size = (0, 0)
        self._kb_k1k2 = ("", "")
        self._kb_force = False

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
        self.bind("<Control-Right>", lambda e: self._jump_segment(1))
        self.bind("<Control-Left>", lambda e: self._jump_segment(-1))
        self.bind("<Control-p>", lambda e: self.toggle_pause())
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
        self.btn_pause = tk.Button(right, text="暂停", command=self.toggle_pause,
                                   relief="flat", takefocus=0, padx=12)
        self.btn_pause.pack(side="left", padx=(10, 0))
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
        self.cb_sfx = tk.Checkbutton(bar, text="音效", variable=self.sfx_on,
                                     takefocus=0, command=self._save_store)
        self.cb_sfx.pack(side="right", padx=(0, 14))
        self.btn_history = tk.Button(bar, text="历史",
                                     command=self._open_history,
                                     relief="flat", takefocus=0, padx=10)
        self.btn_history.pack(side="right", padx=(0, 10))
        self.btn_challenge = tk.Button(bar, text="60 秒挑战",
                                       command=self._toggle_challenge,
                                       relief="flat", takefocus=0, padx=10)
        self.btn_challenge.pack(side="right", padx=(0, 10))

        self.main = tk.Frame(self)
        self.main.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        # 段落显示（经典模式可见）：两行上下文，当前字高亮
        self.t_text = tk.Text(self.main, height=2, wrap="char", bd=0,
                              highlightthickness=0, takefocus=0,
                              cursor="arrow")
        self.t_text.tag_configure("done")
        self.t_text.tag_configure("cur")
        self.t_text.tag_configure("todo")
        self.lb_char = tk.Label(self.main)
        self.lb_py = tk.Label(self.main)
        slots = tk.Frame(self.main)
        self.slots = slots
        self.slot1 = tk.Label(slots, text="＿")
        self.slot1.pack(side="left", padx=8)
        self.slot2 = tk.Label(slots, text="＿")
        self.slot2.pack(side="left", padx=8)
        self.lb_status = tk.Label(self.main)
        # 先从底部固定状态行 / 码槽 / 拼音，剩余空间全给大字：
        # 保证判定后加粗放大的状态行不被窗口高度裁剪
        self.lb_status.pack(side="bottom", pady=(0, 2))
        slots.pack(side="bottom", pady=(4, 2))
        self.lb_py.pack(side="bottom")
        self.lb_char.pack(expand=True, fill="both")

        self.kb = tk.Frame(self)
        self.kb.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.lb_rule = tk.Label(
            self.kb, justify="center",
            text="声母 zh→V ch→I sh→U ｜ 零声母 = 韵母首字母 + 韵母键（爱 ai→ad）｜ er 除外 ｜ 空格跳过 ｜ Ctrl+P 暂停")
        self.lb_rule.pack(side="bottom", pady=(0, 6))
        self.kcanvas = tk.Canvas(self.kb, highlightthickness=0, bd=0)
        self.kcanvas.pack(fill="both", expand=True)
        self._kb_draw_job = None
        self.kcanvas.bind("<Configure>", self._on_kb_configure)

    def _mk_menu(self, parent, var, names, command):
        m = tk.OptionMenu(parent, var, *names, command=command)
        m.configure(relief="flat", takefocus=0)
        m["menu"].configure(font=(YA, 11))
        return m

    def _content_names(self):
        names = ["常用 2000 字", "错字练习", "自定义文本"]
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
                if self.winfo_exists():
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
        for cb in (self.cb_py, self.cb_kb, self.cb_sfx):
            cb.configure(bg=P["bg"], fg=P["fg"], activebackground=P["bg"],
                         selectcolor=P["select"])
        for w in (self.btn_pause, self.btn_reset, self.btn_challenge,
                  self.btn_history):
            w.configure(bg=P["ctrl_bg"], fg=P["ctrl_fg"],
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
        self._kb_force = True        # 配色全套变了，键盘需全量重绘
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
            "char_text": ((YA, 44, "bold"),
                          (YA, max(15, int(44 * s)), "bold")),
            "py": ((YA, 28), (YA, max(13, int(28 * s)))),
            "py_text": ((YA, 16), (YA, max(9, int(16 * s)))),
            "slot": ((MONO, 40, "bold"),
                     (MONO, max(15, int(40 * s)), "bold")),
            "status": ((YA, 16), (YA, max(11, int(16 * s)))),
            "rule": ((YA, 11), (YA, max(9, int(11 * s)))),
            "ctrl": ((YA, 11), (YA, max(10, int(11 * s)))),
            "text": ((YA, 20), (YA, max(11, int(20 * s)))),
        }
        self._status_size = max(11, int(16 * s))
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
                       self.cb_py, self.cb_kb, self.cb_sfx, self.btn_pause,
                       self.btn_reset, self.btn_challenge, self.btn_history):
                w2.configure(font=fonts["ctrl"][0])
            for w2 in (self.theme_menu, self.content_menu, self.scope_menu):
                w2["menu"].configure(font=fonts["ctrl"][0])
            self.t_text.configure(font=fonts["text"][1], spacing1=1)
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
        if self._zero_job is not None:
            self.after_cancel(self._zero_job)
            self._zero_job = None
        if cid == "wrong":
            if restore and not self.wrong_recent:
                cid = "chars"      # 错字本为空：启动时不落在空模式
            else:
                self.book = None
                self.content_id = "wrong"
                self.content_name.set("错字练习")
                self.scope_menu.pack_forget()
                self.t_text.pack_forget()
                self._save_store()
                self._rescale()
                self.reset_session()
                return
        if cid == "custom":
            book = self._custom_book or self._load_custom_book()
            if book is None:
                if restore:        # 启动时无保存文本：落回常用字
                    cid = "chars"
                else:
                    self._open_custom_editor()
                    return
            else:
                self._custom_book = book
                self.book = book
                self.content_id = "custom"
                self.content_name.set("自定义文本")
                self.scope_menu.pack_forget()
                self.t_text.pack(fill="x", pady=(0, 0),
                                 before=self.lb_char)
                ch = self.pos_map.get("custom", [0, 0]) if restore else [0, 0]
                self.t_ch, self.t_seg = ch[0], ch[1]
                self._cache_book()
                self._load_segments()
                self.t_pos = 0
                self._save_store()
                self._rescale()
                self.reset_session(keep_pos=restore)
                return
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
            self.t_text.pack(fill="x", pady=(0, 0),
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
        if value == "错字练习":
            self._select_content("wrong")
            return
        if value == "自定义文本":
            self._open_custom_editor()
            return
        name = value.replace("（选）", "")
        cid = next((b["id"] for b in self.books if b["name"] == name),
                   "chars")
        self._select_content(cid)

    def _chapters(self):
        return self.book["chapters"] if self.book else []

    # ----- 自定义文本 -----
    def _load_custom_book(self):
        try:
            with open(CUSTOM_FILE, encoding="utf-8") as f:
                return self._build_custom_book(f.read())
        except Exception:
            return None

    def _build_custom_book(self, text):
        """空行分段→单节 ≤500 字切章，逐字配拼音（未收录汉字自动跳过）。"""
        blocks = [b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
        chunks = []
        for b in blocks:
            b = "".join(b.split())          # 段内去掉空白与换行
            for i in range(0, len(b), 500):
                chunks.append(b[i:i + 500])
        if not chunks:
            return None
        chaps = []
        for idx, cbody in enumerate(chunks, 1):
            ent = self._char_map
            pyl = [[ent[ch]["p"], ent[ch]["f"]] if ch in ent else None
                   for ch in cbody]
            chaps.append({"t": f"第 {idx}/{len(chunks)} 节",
                          "body": cbody, "pyl": pyl})
        return {"id": "custom", "name": "自定义文本", "select": False,
                "chapters": chaps}

    def _open_custom_editor(self):
        prev = self.content_name.get()
        applied = []
        win = tk.Toplevel(self)
        win.title("自定义文本")
        win.geometry("560x430")
        win.configure(bg=self.P["panel"])
        win.transient(self)

        tip = tk.Label(
            win, wraplength=520, justify="left",
            text="粘贴或导入要练习的文章（空行分段；未收录的生僻字会自动跳过）",
            bg=self.P["panel"], fg=self.P["grey"])
        tip.pack(anchor="w", padx=14, pady=(12, 4))
        body = tk.Text(win, wrap="char", bd=0, font=(YA, 12),
                       bg=self.P["key_bg"], fg=self.P["fg"],
                       insertbackground=self.P["fg"], height=10)
        body.pack(fill="both", expand=True, padx=14, pady=6)
        try:
            with open(CUSTOM_FILE, encoding="utf-8") as f:
                body.insert("1.0", f.read())
        except Exception:
            pass

        btns = tk.Frame(win, bg=self.P["panel"])
        btns.pack(fill="x", padx=14, pady=(0, 12))

        def do_import():
            from tkinter import filedialog
            p = filedialog.askopenfilename(
                parent=win, title="导入文本",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
            if not p:
                return
            for enc in ("utf-8", "gbk"):
                try:
                    with open(p, encoding=enc) as f:
                        data = f.read()
                    break
                except (UnicodeDecodeError, OSError):
                    data = None
            if data is None:
                messagebox.showinfo("自定义文本", "无法读取该文件（编码不是 UTF-8/GBK）")
                return
            body.delete("1.0", "end")
            body.insert("1.0", data)

        def do_ok():
            text = body.get("1.0", "end").strip()
            book = self._build_custom_book(text)
            if book is None:
                messagebox.showinfo("自定义文本", "没有可练习的内容（需要包含汉字）")
                return
            applied.append(True)
            self._custom_book = book
            try:
                with open(CUSTOM_FILE, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception:
                pass
            win.destroy()
            self._select_content("custom")

        def on_cancel():
            if not applied:            # 取消：菜单显示回到原模式
                self.content_name.set(prev)
            win.destroy()

        tk.Button(btns, text="导入 .txt…", command=do_import,
                  bg=self.P["ctrl_bg"], fg=self.P["ctrl_fg"],
                  activebackground=self.P["ctrl_active"],
                  activeforeground=self.P["ctrl_fg"],
                  relief="flat", padx=12).pack(side="left")
        tk.Button(btns, text="取消", command=on_cancel,
                  bg=self.P["ctrl_bg"], fg=self.P["ctrl_fg"],
                  activebackground=self.P["ctrl_active"],
                  activeforeground=self.P["ctrl_fg"],
                  relief="flat", padx=12).pack(side="right")
        tk.Button(btns, text="开始练习", command=do_ok,
                  bg=self.P["blue"], fg="#ffffff",
                  activebackground=self.P["blue"],
                  activeforeground="#ffffff",
                  relief="flat", padx=14).pack(side="right", padx=(0, 8))
        win.protocol("WM_DELETE_WINDOW", on_cancel)

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

    @staticmethod
    def _typeable(body, i, pyl):
        """可练字 = 汉字且带有效双拼码（无码字自动跳过，防卡死）"""
        if not HANZI.fullmatch(body[i]):
            return False
        ent = pyl[i] if i < len(pyl) else None
        return bool(ent) and len(ent[1]) == 2

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
        pyl = ch["pyl"]
        while i < s1 and not self._typeable(body, i, pyl):
            i += 1
        self.t_pos = i
        if i >= s1:
            return "", "", ""
        return pyl[i][1], body[i], pyl[i][0]

    def _advance_text(self):
        """推进到下一个待练字；返回 True 表示有效。"""
        chs = self._chapters()
        if not chs:
            return False
        for _ in range(self.t_total + len(chs) + 2):
            if self.t_seg >= len(self.t_segs):
                if self.t_ch >= len(chs) - 1:
                    self._just_wrapped = True   # 练完最后一章
                self.t_ch = (self.t_ch + 1) % len(chs)
                self.t_seg = 0                  # 跨章：段号归零（勿残留上一章段号）
                self._load_segments()
                self.t_pos = 0
                self._save_text_pos()
                continue
            s0, s1 = self.t_segs[self.t_seg]
            if self.t_pos < s0:
                self.t_pos = s0        # 进入新段：从段首起
            i = self.t_pos
            ch = self._chapter()
            body, pyl = ch["body"], ch["pyl"]
            while i < s1 and not self._typeable(body, i, pyl):
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
        self._stop_flash()
        self.typed = ""
        self.state = "typing"
        status = "输入两键编码"
        if self._is_text_mode():
            if not self._advance_text():
                self.book = None
                return self._select_content("chars")
            self.lb_char.configure(text=self._expected()[1],
                                   fg=self.P["fg"])
            self._render_segment()
        else:
            last = None if first or self.cur is None else self.cur["c"]
            if self.content_id == "wrong":
                if not self.wrong_recent:
                    self.cur = None
                    self.lb_char.configure(text="🎉", fg=self.P["fg"])
                    self.lb_py.configure(text="错字本已清空")
                    self.lb_status.configure(
                        text="🎉 错字全部练对了！稍后回到常用字练习",
                        fg=self.P["green"])
                    if self._zero_job is None:
                        self._zero_job = self.after(
                            1800, lambda: self._select_content("chars"))
                    return
                pool = self.wrong_recent
                while True:
                    self.cur = random.choice(pool)
                    if last is None or self.cur["c"] != last or len(pool) < 2:
                        break
            else:
                pool = self._scoped() or self.chars
                requeue = None
                if self.wrong_recent and random.random() < 0.35:
                    cand = [c for c in self.wrong_recent[:15]
                            if c["c"] != last]
                    if cand:
                        requeue = random.choice(cand)
                if requeue is not None:
                    self.cur = requeue
                    status = "错字重练 · 输入两键编码"
                else:
                    while True:
                        self.cur = random.choice(pool)
                        if last is None or self.cur["c"] != last or len(pool) < 2:
                            break
            self.lb_char.configure(text=self.cur["c"], fg=self.P["fg"])
        self._refresh_answer()
        self.slot1.configure(text="＿", fg=self.P["grey"])
        self.slot2.configure(text="＿", fg=self.P["grey"])
        if self._just_wrapped:
            self._just_wrapped = False
            status = "🎉 已练完一轮，从头继续"
        self.lb_status.configure(text=status, fg=self.P["grey"],
                                 font=(YA, self._status_size))
        self._refresh_stats()
        self._highlight_keys()
        # 补上锁定期间预输入的键（最多两键，快速连打不丢键）
        pk, self._pending_key = self._pending_key, ""
        for ch in pk:
            if self.state != "typing":
                break
            self._apply_letter(ch)

    def _refresh_answer(self):
        code, _disp, py = self._expected()
        if not code:
            return
        if self.show_py.get() or self.state != "typing":
            self.lb_py.configure(text=py)
        else:
            self.lb_py.configure(text="· ·（拼音已隐藏）")

    def _render_segment(self):
        """显示当前句上下文（约两行），当前字高亮，随打字滚动。"""
        ch = self._chapter()
        if ch is None:
            return
        body = ch["body"]
        s0, _s1 = self.t_segs[self.t_seg]
        e = self.t_pos
        # 锚定句首（。？！；之后），向后再取约两屏字符
        d0 = max(body.rfind(p, 0, s0) for p in "。？！；") + 1
        d1 = min(len(body), d0 + 72)
        if e >= d1:                     # 超长句：以当前字为尾锚
            d1 = min(len(body), e + 12)
            d0 = max(0, d1 - 72)
        t = self.t_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("1.0", body[d0:d1])
        for i in range(d0, d1):
            tag = "done" if i < e else ("cur" if i == e else None)
            if tag:
                t.tag_add(tag, f"1.{i - d0}", f"1.{i - d0 + 1}")
        if e > d0:
            t.tag_add("done", "1.0", f"1.{min(e, d1) - d0}")
        t.configure(state="disabled")
        try:
            t.see(f"1.{e - d0}")        # 保证当前字可见
        except tk.TclError:
            pass
        self._refresh_scope_label()

    def _save_text_pos(self):
        if self._is_text_mode():
            self.pos_map[self.content_id] = [self.t_ch, self.t_seg]
            self._mark_dirty()

    def _mark_dirty(self):
        """练习数据待落盘（由 _tick 每秒统一写一次，避免高速打字时频繁写盘）"""
        self._store_dirty = True

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
        """更新键位高亮：优先增量重着色，仅在尺寸/主题变化时全量重绘。"""
        code = self._expected()[0]
        k1, k2 = code[:1].upper(), code[1:2].upper()
        c = self.kcanvas
        size = (c.winfo_width(), c.winfo_height())
        if self._kb_force or not self._kb_keys or self._kb_size != size:
            self._kb_force = False
            self._draw_keyboard(k1, k2)
            return
        if (k1, k2) != self._kb_k1k2:
            for lbl in {self._kb_k1k2[0], self._kb_k1k2[1], k1, k2} - {"", None}:
                self._kb_apply(lbl, k1, k2)
            self._kb_k1k2 = (k1, k2)

    def _kb_apply(self, label, k1, k2):
        """按 (k1, k2) 重着色单个字母键（增量刷新）。"""
        entry = self._kb_keys.get(label)
        if not entry:
            return
        P = self.P
        if label == k1 == k2:
            bg, fg, sfg, hi = P["purple"], "#ffffff", "#ffffff", True
        elif label == k1:
            bg, fg, sfg, hi = P["blue"], "#ffffff", P["hl_sub"], True
        elif label == k2:
            bg, fg, sfg, hi = P["orange"], "#ffffff", P["hl_sub"], True
        else:
            bg, fg, sfg, hi = P["key_bg"], P["fg"], P["grey"], False
        poly, main_id, subs = entry
        c = self.kcanvas
        c.itemconfigure(poly, fill=bg, outline=bg)
        c.itemconfigure(main_id, fill=fg)
        if label in ("U", "I", "V"):
            left_id, ini_id = subs
            c.itemconfigure(left_id, fill=sfg)
            c.itemconfigure(ini_id, fill=("#ff9d94" if hi else P["red"]))
        else:
            c.itemconfigure(subs[0], fill=sfg)

    def _expect_pair(self):
        code = self._expected()[0]
        return (code[0], code[1]) if len(code) == 2 else ("", "")

    def _remember_wrong(self):
        """记录答错的字（两种模式都记，供错字练习与错字重练）"""
        if self._is_text_mode():
            c = self._char_map.get(self._expected()[1])
        else:
            c = self.cur
        if c is None:
            return
        if c in self.wrong_recent:
            self.wrong_recent.remove(c)
        self.wrong_recent.insert(0, c)
        del self.wrong_recent[WRONG_CAP:]

    def _give_up(self):
        c0, c1 = self._expect_pair()
        if not c0:
            return
        self.answered += 1
        self.bad += 1
        self.streak = 0
        self.cum["practiced"] += 1
        self.cum["wrong"] += 1
        self._remember_wrong()
        self._record_history(False)
        if self.challenge_end is not None:
            self.ch_answered += 1
            self.ch_wrong.append(self._expected()[1])
        self.state = "locked_no"
        self.slot1.configure(text=c0, fg=self.P["orange"])
        self.slot2.configure(text=c1, fg=self.P["orange"])
        self.lb_status.configure(
            text=f"已跳过 · 正确编码：{c0} {c1}（空格继续）",
            fg=self.P["grey"])
        self._refresh_stats()
        self._mark_dirty()
        self._auto_next_job = self.after(2600, self._continue)

    def on_key(self, event):
        ks = event.keysym
        if self.paused_at is not None:       # 暂停中：任意键自动继续
            self.toggle_pause()
            return "break"
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
            self._pending_key = (self._pending_key + ch)[:2]   # 缓存预输入键
            return
        if self.state == "locked_no":
            self._continue()
            return
        self._apply_letter(ch)

    def _apply_letter(self, ch):
        """键入一个字母：更新码槽，凑满两键即判定。"""
        if self.started_at is None:
            self.started_at = time.time()
        self._play("tick")
        self.typed += ch
        if len(self.typed) == 1:
            self.slot1.configure(text=ch, fg=self.P["blue"])
        else:
            self.slot2.configure(text=ch, fg=self.P["orange"])
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
            if self._is_text_mode():
                ent = self._char_map.get(self._expected()[1])
            else:
                ent = self.cur
            if ent in self.wrong_recent:
                self.wrong_recent.remove(ent)   # 答对即移出错字本
            self._record_history(True)
            if self.challenge_end is not None:
                self.ch_answered += 1
                self.ch_ok += 1
            self.state = "locked_ok"
            self.slot1.configure(text=expected[0], fg=self.P["green"])
            self.slot2.configure(text=expected[1], fg=self.P["green"])
            msg = "✓ 正确！"
            if self.streak >= 3:
                msg += f"  连对 {self.streak}"
            self.lb_status.configure(text=msg, fg=self.P["green"])
            self._play("ok")
            self._flash(True)
            self._refresh_stats()
            self._mark_dirty()
            self._auto_next_job = self.after(300 if self._is_text_mode()
                                             else 420, self._continue)
        else:
            self.bad += 1
            self.streak = 0
            self.cum["wrong"] += 1
            self._remember_wrong()
            self._record_history(False)
            if self.challenge_end is not None:
                self.ch_answered += 1
                self.ch_wrong.append(self._expected()[1])
            self.state = "locked_no"
            self.slot1.configure(text=self.typed[0], fg=self.P["red"])
            self.slot2.configure(text=self.typed[1], fg=self.P["red"])
            self.lb_status.configure(
                text=f"✗ 正确编码：{expected[0]} {expected[1]}（空格继续）",
                fg=self.P["red"])
            self._play("bad")
            self._flash(False)
            self._refresh_answer()
            self._refresh_stats()
            self._mark_dirty()
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

    # ----- 暂停 / 继续：休息期间冻结计时、屏蔽打字 -----
    def _elapsed(self):
        """本轮有效练习时长（扣除暂停），秒。"""
        if self.started_at is None:
            return 0.0
        end = self.paused_at if self.paused_at is not None else time.time()
        return max(0.0, end - self.started_at - self.paused_total)

    def toggle_pause(self):
        if self.challenge_end is not None:      # 挑战中不允许暂停（防作弊）
            self.lb_status.configure(text="挑战进行中，不能暂停",
                                     fg=self.P["orange"])
            return
        if self.paused_at is not None:      # 继续
            self.paused_total += time.time() - self.paused_at
            self.paused_at = None
            self.btn_pause.configure(text="暂停")
            if self.state == "typing":
                self.lb_status.configure(
                    text="输入两键编码", fg=self.P["grey"],
                    font=(YA, self._status_size))
            else:                            # 暂停时冻结的判定，恢复后补上下一字
                self._continue()
        else:                                # 暂停
            self.paused_at = time.time()
            self._cancel_auto()              # 自动下一字也一并冻结
            self.btn_pause.configure(text="继续")
            self.lb_status.configure(
                text="⏸ 已暂停 · 休息一下，按任意键或点「继续」接着练",
                fg=self.P["orange"], font=(YA, self._status_size))

    # ----- 60 秒限时挑战 -----
    def _toggle_challenge(self):
        if self.challenge_end is not None:      # 再点一次 = 提前结束出成绩
            self._end_challenge()
            return
        self.challenge_end = time.time() + CHALLENGE_SECS
        self.ch_answered = self.ch_ok = 0
        self.ch_wrong = []
        self.btn_challenge.configure(text="结束挑战")
        self.lb_status.configure(text=f"⏱ {CHALLENGE_SECS} 秒挑战开始，加油！",
                                 fg=self.P["blue"],
                                 font=(YA, self._status_size))
        self._refresh_scope_label()

    def _cancel_challenge(self):
        """静默取消（重新开始/切换内容时），不出成绩单。"""
        if self.challenge_end is not None:
            self.challenge_end = None
            self.btn_challenge.configure(text="60 秒挑战")
            self._refresh_scope_label()

    def _end_challenge(self):
        if self.challenge_end is None:
            return
        self._cancel_challenge()
        n, ok = self.ch_answered, self.ch_ok
        acc = ok / n * 100 if n else 0
        lines = [f"字数 {n} · 正确 {ok} · 正确率 {acc:.0f}%",
                 f"速度 {n} 字/分（限时 {CHALLENGE_SECS} 秒）"]
        wrongs = list(dict.fromkeys(self.ch_wrong))
        if wrongs:
            lines.append("错字：" + "、".join(wrongs[:12]))
        win = tk.Toplevel(self)
        win.title("挑战成绩")
        win.geometry("360x230")
        win.configure(bg=self.P["panel"])
        win.transient(self)
        win.grab_set()
        tk.Label(win, text="⏱ 挑战结束", bg=self.P["panel"], fg=self.P["fg"],
                 font=(YA, 16, "bold")).pack(pady=(18, 6))
        tk.Label(win, text="\n".join(lines), bg=self.P["panel"],
                 fg=self.P["fg"], font=(YA, 13), justify="left").pack(padx=24)
        btns = tk.Frame(win, bg=self.P["panel"])
        btns.pack(pady=16)

        def again():
            win.destroy()
            self._toggle_challenge()

        def done():
            win.destroy()
            self.lb_status.configure(text="挑战结束 · 继续练习",
                                     fg=self.P["grey"])
        tk.Button(btns, text="再来一轮", command=again, relief="flat",
                  padx=14, bg=self.P["blue"], fg="#ffffff",
                  activebackground=self.P["blue"],
                  activeforeground="#ffffff").pack(side="left", padx=8)
        tk.Button(btns, text="继续练习", command=done, relief="flat",
                  padx=14, bg=self.P["ctrl_bg"], fg=self.P["ctrl_fg"],
                  activebackground=self.P["ctrl_active"],
                  activeforeground=self.P["ctrl_fg"]).pack(side="left", padx=8)

    # ----- 每日打卡 / 历史统计 -----
    def _record_history(self, ok):
        today = time.strftime("%Y-%m-%d")
        d = self.history.setdefault(
            today, {"practiced": 0, "correct": 0, "time": 0.0})
        d["practiced"] += 1
        if ok:
            d["correct"] += 1
        if self._last_answer_ts is not None:
            d["time"] += min(120.0, max(0.0, time.time() - self._last_answer_ts))
        self._last_answer_ts = time.time()
        if len(self.history) > HISTORY_KEEP:      # 只保留最近 HISTORY_KEEP 天
            for k in sorted(self.history)[:-HISTORY_KEEP]:
                del self.history[k]

    def _streak_days(self):
        """连续打卡天数（今天已练则含今天，否则截至昨天）。"""
        from datetime import date, timedelta
        d, streak = date.today(), 0
        if not self.history.get(d.isoformat(), {}).get("practiced"):
            d -= timedelta(days=1)
        while self.history.get(d.isoformat(), {}).get("practiced"):
            streak += 1
            d -= timedelta(days=1)
        return streak

    def _open_history(self):
        win = tk.Toplevel(self)
        win.title("历史统计（近 30 天）")
        win.geometry("700x340")
        win.configure(bg=self.P["panel"])
        win.transient(self)
        canvas = tk.Canvas(win, highlightthickness=0, bd=0,
                           bg=self.P["panel"])
        canvas.pack(fill="both", expand=True, padx=12, pady=10)
        win.update_idletasks()
        self._draw_history(canvas)
        canvas.bind("<Configure>", lambda e: self._draw_history(canvas))

    def _draw_history(self, canvas):
        canvas.delete("all")
        W = canvas.winfo_width()
        H = canvas.winfo_height()
        if W < 60 or H < 60:
            return
        P = self.P
        from datetime import date, timedelta
        days = []
        d = date.today()
        for _ in range(30):
            days.append(d.isoformat())
            d -= timedelta(days=1)
        days.reverse()
        data = [self.history.get(k) or {} for k in days]
        counts = [e.get("practiced", 0) for e in data]
        speeds = []
        for e in data:
            t = e.get("time", 0.0)
            c = e.get("correct", 0)
            speeds.append(c / (t / 60) if t >= 30 and c else None)
        x0, y0 = 46, 24                      # 绘图区
        x1, y1 = W - 16, H - 34
        maxc = max(10, max(counts))
        grey = P["grey"]
        # 横网格 + 刻度
        for i in range(1, 4):
            y = y1 - (y1 - y0) * i / 4
            canvas.create_line(x0, y, x1, y, fill=P["key_border"], dash=(2, 4))
            canvas.create_text(x0 - 6, y, text=str(int(maxc * i / 4)),
                               fill=grey, anchor="e", font=(YA, 9))
        bw = (x1 - x0) / 30
        for i, n in enumerate(counts):
            if not n:
                continue
            h = (y1 - y0) * n / maxc
            canvas.create_rectangle(x0 + i * bw + 1, y1 - h,
                                    x0 + (i + 1) * bw - 1, y1,
                                    fill=P["blue"], outline="")
        # 速度折线
        pts = []
        for i, s in enumerate(speeds):
            if s:
                maxs = 80.0
                y = y1 - (y1 - y0) * min(1.0, s / maxs)
                pts.extend([x0 + (i + 0.5) * bw, y])
        if len(pts) >= 4:
            canvas.create_line(*pts, fill=P["orange"], width=2, smooth=True)
        # 日期轴
        for i in range(0, 30, 5):
            label = days[i][5:]              # MM-DD
            canvas.create_text(x0 + (i + 0.5) * bw, y1 + 14, text=label,
                               fill=grey, font=(YA, 9))
        canvas.create_line(x0, y1, x1, y1, fill=P["key_border"])
        canvas.create_text(x0, y0 - 10, anchor="w", fill=grey, font=(YA, 10),
                           text="柱 = 每日字数    橙线 = 速度（字/分）")
        if max(counts) == 0:
            canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2,
                               text="还没有练习记录，先打几题吧",
                               fill=grey, font=(YA, 14))

    # ----- 打字音效 -----
    def _play(self, kind):
        if not self.sfx_on.get():
            return
        try:
            if self._sfx is None:
                self._sfx = _sfx_build()
            wav = self._sfx[kind]
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(wav, winsound.SND_MEMORY
                                   | winsound.SND_ASYNC)
            elif sys.platform == "darwin":
                import subprocess
                sfx_dir = os.path.join(APP_DIR, "sfx")
                os.makedirs(sfx_dir, exist_ok=True)
                path = os.path.join(sfx_dir, kind + ".wav")
                if not os.path.exists(path):
                    with open(path, "wb") as f:
                        f.write(wav)
                subprocess.Popen(["afplay", path],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # ----- 对/错视觉反馈：面板底色闪烁 + 大字变色 + 状态加粗放大 -----
    def _flash(self, ok):
        P = self.P
        color = P["ok_bg"] if ok else P["bad_bg"]
        fg = P["green"] if ok else P["red"]
        for w in (self.main, self.t_text, self.lb_char, self.lb_py,
                  self.slots, self.slot1, self.slot2, self.lb_status):
            try:
                w.configure(bg=color)
            except tk.TclError:
                pass
        self.lb_char.configure(fg=fg)
        size = max(13, int(self._status_size * 1.35))
        self.lb_status.configure(font=(YA, size, "bold"))
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
        self._flash_job = self.after(300 if ok else 550, self._stop_flash)

    def _stop_flash(self):
        self._flash_job = None
        P = self.P
        for w in (self.main, self.t_text, self.lb_char, self.lb_py,
                  self.slots, self.slot1, self.slot2, self.lb_status):
            try:
                w.configure(bg=P["panel"])
            except tk.TclError:
                pass

    def reset_session(self, keep_pos=False):
        self._cancel_auto()
        self._cancel_challenge()
        if self._zero_job is not None:
            self.after_cancel(self._zero_job)
            self._zero_job = None
        if self.paused_at is not None:       # 新一轮直接回到未暂停态
            self.paused_at = None
            self.btn_pause.configure(text="暂停")
        self.paused_total = 0.0
        self._last_answer_ts = None
        self._pending_key = ""
        self._just_wrapped = False
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
        if self.challenge_end is not None:
            left = max(0, int(self.challenge_end - time.time() + 0.999))
            self.lb_scope.configure(
                text=f"⏱ 60 秒挑战 · 剩余 {left}s")
            return
        if self._is_text_mode():
            ch = self._chapter()
            done = sum(self.t_ch_counts[:self.t_ch]) + self.t_seg + 1
            self.lb_scope.configure(
                text=f"{self.book['name']} · {ch['t']} · 第 {done}/{self.t_total} 段")
        elif self.content_id == "wrong":
            n = len(self.wrong_recent)
            self.lb_scope.configure(
                text=f"错字本 {n} 字 · 答对一个移出一个")
        else:
            self.lb_scope.configure(text=f"词库 {len(self._scoped())} 字")

    def _refresh_stats(self):
        acc = self.ok / self.answered * 100 if self.answered else 0
        spd = "—"
        if self.started_at and self.answered:
            sec = self._elapsed()
            if sec > 8:
                spd = f"{self.answered / (sec / 60):.0f} 字/分"
        self.lb_stats.configure(
            text=f"✓ {self.ok}   ✗ {self.bad}   连对 {self.streak}"
                 f"（最佳 {self.best}）   正确率 {acc:.0f}%   速度 {spd}")
        c = self.cum
        cacc = c["correct"] / c["practiced"] * 100 if c["practiced"] else 0
        self._refresh_scope_label()
        self.lb_cum.configure(
            text=f"累计已练 {c['practiced']} 字 · 正确率 {cacc:.0f}%"
                 f" · 连续打卡 {self._streak_days()} 天")

    def _tick(self):
        try:
            if self._store_dirty:
                self._store_dirty = False
                self._save_store()
            # 跟随系统主题：轮询注册表变化
            if self.theme_mode == "system":
                dark = sys_prefers_dark()
                if dark != self._cur_eff_dark:
                    self._apply_theme()
            if self.challenge_end is not None:
                left = self.challenge_end - time.time()
                if left <= 0:
                    self._end_challenge()
                else:
                    self._refresh_scope_label()
            self._refresh_stats()
        except tk.TclError:
            pass    # 瞬时错误不中断心跳链
        try:
            self.after(1000, self._tick)
        except tk.TclError:
            pass

    def _jump_segment(self, delta):
        """文本模式 Ctrl+←/→ 跳段（可跨章）"""
        if not self._is_text_mode():
            return "break"
        self._cancel_auto()
        self.t_seg += delta
        if self.t_seg < 0:
            self.t_ch = (self.t_ch - 1) % len(self._chapters())
            self._load_segments()
            self.t_seg = max(0, len(self.t_segs) - 1)
        elif self.t_seg >= len(self.t_segs):
            self.t_ch = (self.t_ch + 1) % len(self._chapters())
            self._load_segments()
            self.t_seg = 0
        self.t_pos = 0
        self._save_text_pos()
        self._next_char()
        return "break"

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

    def _draw_keyboard(self, k1, k2):
        c = self.kcanvas
        P = self.P
        W, H = c.winfo_width(), c.winfo_height()
        if W < 60 or H < 50:
            return
        c.delete("all")
        self._kb_keys = {}
        pitch = W / KB_UNIT_TOTAL
        gap = max(2, pitch * 0.04)
        vgap = max(3, H * 0.018)
        key_h = min((H - (len(KB_ROWS) - 1) * vgap) / len(KB_ROWS), 120)
        rad = max(3, key_h * 0.22)
        f_letter = (MONO, max(8, int(key_h * 0.24)), "bold")
        f_sub = (YA, max(7, int(key_h * 0.15)))
        f_mod = (YA, max(7, int(key_h * 0.17)))
        f_alt = (MONO, max(7, int(key_h * 0.20)), "bold")
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
                poly = c.create_polygon(
                    *self._round_pts(x0, y0, x1, y1, rad),
                    smooth=True, fill=bg, outline=outline, width=1)
                cx = (x0 + x1) / 2
                if letter:
                    main = c.create_text(cx, y0 + key_h * 0.30, text=label,
                                         font=f_letter, fill=fg)
                    sub = KB_INFO[label]
                    if label in ("U", "I", "V"):
                        # 声母 sh / ch / zh 用红色醒目标出
                        left, ini = sub.split("·", 1)
                        fm = tkfont.Font(font=f_sub)
                        lw, rw = fm.measure(left), fm.measure(ini)
                        start = cx - (lw + rw) / 2
                        ini_c = "#ff9d94" if bg != P["key_bg"] else P["red"]
                        left_id = c.create_text(start, y0 + key_h * 0.70,
                                                text=left, font=f_sub,
                                                fill=sfg, anchor="w")
                        ini_id = c.create_text(start + lw, y0 + key_h * 0.70,
                                               text=ini, font=f_sub,
                                               fill=ini_c, anchor="w")
                        self._kb_keys[label] = (poly, main, (left_id, ini_id))
                    else:
                        sub_id = c.create_text(cx, y0 + key_h * 0.70, text=sub,
                                               font=f_sub, fill=sfg)
                        self._kb_keys[label] = (poly, main, (sub_id,))
                elif label == "空格":
                    c.create_text(cx, (y0 + y1) / 2, text="空格 · 跳过",
                                  font=f_mod, fill=fg)
                else:
                    c.create_text(cx, (y0 + y1) / 2, text=label,
                                  font=f_alt if len(label) <= 2 else f_mod,
                                  fill=fg)
                x += units
            y += key_h + vgap
        self._kb_size = (W, H)
        self._kb_k1k2 = (k1, k2)
        self._kb_force = False

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
                "pos": self.pos_map,
                "wrong_chars": [e["c"] for e in self.wrong_recent],
                "sfx": bool(self.sfx_on.get()),
                "history": self.history}
        try:
            # 原子写：防中途崩溃损坏 stats.json
            tmp = STATS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, STATS_FILE)
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
        for job in (self._auto_next_job, self._kb_draw_job,
                    self._resize_job, self._flash_job, self._zero_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
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
