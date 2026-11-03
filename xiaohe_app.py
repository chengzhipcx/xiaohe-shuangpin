# -*- coding: utf-8 -*-
"""小鹤双拼编码练习 —— Windows 桌面小程序（仅依赖标准库 tkinter）

屏幕给出汉字和全拼，输入对应的小鹤双拼两键编码。
编码规则与 Rime 官方 double_pinyin_flypy 方案一致：
  声母：zh→V  ch→I  sh→U，其余声母取原字母；y、w 按声母处理（按全拼拼写取韵母）
  韵母：iu=Q ei=W uan=R ue/ve=T un=Y uo=O ie=P ong/iong=S ing/uai=K
        iang/uang=L ai=D en=F eng=G ang=H an=J ou=Z ia/ua=X iao=N
        ao=C ui=V in=B ian=M
  零声母：韵母首字母 + 韵母键（爱 ai→ad、恩 en→ef），er 例外→er
"""
import json
import os
import random
import sys
import time
import tkinter as tk
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
ICON_FILE = os.path.join(_RES_DIR, "app.ico")
STATS_FILE = os.path.join(APP_DIR, "stats.json")

BG = "#eef1f6"
PANEL = "#ffffff"
FG = "#22303f"
BLUE = "#1e88e5"     # 声母位高亮
ORANGE = "#fb8c00"   # 韵母位高亮
PURPLE = "#8e44ad"   # 两键相同
GREEN = "#2f9e44"
RED = "#d6453d"
GREY = "#8a97a5"
KEY_BG = "#ffffff"
KEY_BORDER = "#d5dce4"

YA = "Microsoft YaHei UI"

SCOPES = [("前 300 字", 300), ("前 600 字", 600),
          ("前 1000 字", 1000), ("前 1500 字", 1500), ("全部 2000 字", None)]

KB_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
KB_INFO = {
    "Q": "iu", "W": "ei", "E": "e", "R": "uan", "T": "ue", "Y": "un",
    "U": "u·sh", "I": "i·ch", "O": "o·uo", "P": "ie",
    "A": "a", "S": "ong·iong", "D": "ai", "F": "en", "G": "eng",
    "H": "ang", "J": "an", "K": "ing·uai", "L": "iang·uang",
    "Z": "ou", "X": "ia·ua", "C": "ao", "V": "ui·zh", "B": "in",
    "N": "iao", "M": "ian",
}


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
        self.configure(bg=BG)
        try:
            self.iconbitmap(ICON_FILE)
        except Exception:
            pass

        with open(DATA_FILE, encoding="utf-8") as f:
            self.chars = json.load(f)
        self.cum = self._load_stats()

        self.scope_name = tk.StringVar(value="前 1000 字")
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

        self._build_ui()
        self._toggle_kb()
        self.update_idletasks()
        self._rescale()
        self._disable_ime()

        self.bind("<Key>", self.on_key)
        self.bind("<ButtonRelease-1>", lambda e: self.focus_set())
        self.bind("<Configure>", self.on_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._next_char(first=True)
        self.after(1000, self._tick)

    # ---------- UI ----------
    def _build_ui(self):
        # 上下对半布局：第 2 行（字）与第 3 行（键盘）等权重
        self.grid_rowconfigure(2, weight=1, uniform="half")
        self.grid_rowconfigure(3, weight=1, uniform="half")
        self.grid_columnconfigure(0, weight=1)

        top = tk.Frame(self, bg=BG)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 2))
        self.lb_title = tk.Label(top, text="⌨ 小鹤双拼练习", bg=BG, fg=FG)
        self.lb_title.pack(side="left")

        right = tk.Frame(top, bg=BG)
        right.pack(side="right")
        self.scope_menu = tk.OptionMenu(
            right, self.scope_name, *[n for n, _ in SCOPES],
            command=lambda _v: self.reset_session())
        self.scope_menu.configure(relief="flat", bg="#e2e8f0",
                                  activebackground="#d3dce6", takefocus=0)
        self.scope_menu["menu"].configure(bg="#ffffff", font=(YA, 11))
        self.scope_menu.pack(side="left", padx=(0, 10))
        self.cb_py = tk.Checkbutton(right, text="显示拼音", variable=self.show_py,
                                    command=self._toggle_py, bg=BG, fg=FG,
                                    activebackground=BG, selectcolor="#ffffff",
                                    takefocus=0)
        self.cb_py.pack(side="left", padx=4)
        self.cb_kb = tk.Checkbutton(right, text="键位图", variable=self.show_kb,
                                    command=self._toggle_kb, bg=BG, fg=FG,
                                    activebackground=BG, selectcolor="#ffffff",
                                    takefocus=0)
        self.cb_kb.pack(side="left", padx=4)
        self.btn_reset = tk.Button(right, text="重新开始", command=self.reset_session,
                                   relief="flat", bg="#e2e8f0", fg=FG,
                                   activebackground="#d3dce6", takefocus=0,
                                   padx=12)
        self.btn_reset.pack(side="left", padx=(10, 0))

        bar = tk.Frame(self, bg=BG)
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 0))
        self.lb_scope = tk.Label(bar, bg=BG, fg=GREY)
        self.lb_scope.pack(side="left")
        self.lb_stats = tk.Label(bar, bg=BG, fg=FG)
        self.lb_stats.pack(side="left", padx=18)
        self.lb_cum = tk.Label(bar, bg=BG, fg=GREY)
        self.lb_cum.pack(side="right")

        self.main = tk.Frame(self, bg=PANEL)
        self.main.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self.lb_char = tk.Label(self.main, bg=PANEL, fg=FG)
        self.lb_char.pack(expand=True)
        self.lb_py = tk.Label(self.main, bg=PANEL, fg=GREY)
        self.lb_py.pack()
        slots = tk.Frame(self.main, bg=PANEL)
        slots.pack(pady=(4, 0))
        self.slot1 = tk.Label(slots, text="＿", bg=PANEL, fg=GREY)
        self.slot1.pack(side="left", padx=8)
        self.slot2 = tk.Label(slots, text="＿", bg=PANEL, fg=GREY)
        self.slot2.pack(side="left", padx=8)
        self.lb_status = tk.Label(self.main, bg=PANEL, fg=GREY)
        self.lb_status.pack(pady=(2, 0))

        self.kb = tk.Frame(self, bg=BG)
        self.kb.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.lb_rule = tk.Label(
            self.kb, bg=BG, fg=GREY, justify="center",
            text="声母 zh→V ch→I sh→U ｜ 零声母 = 韵母首字母 + 韵母键（爱 ai→ad）｜ er 除外 ｜ 空格跳过")
        self.lb_rule.pack(side="bottom", pady=(0, 6))
        self.kcanvas = tk.Canvas(self.kb, bg=BG, highlightthickness=0, bd=0)
        self.kcanvas.pack(fill="both", expand=True)
        self.key_items = {}          # letter -> (poly_id, text_id, sub_id)
        self._kb_draw_job = None
        self.kcanvas.bind("<Configure>", self._on_kb_configure)

    def _rescale(self):
        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)
        s = max(0.55, min(2.2, min(w / 1000.0, h / 700.0)))
        fonts = {
            "title": ((YA, 15, "bold"), (YA, max(13, int(15 * s)), "bold")),
            "stats": ((YA, 12), (YA, max(10, int(12 * s)))),
            "char": ((YA, 82, "bold"), (YA, max(24, int(82 * s)), "bold")),
            "py": ((YA, 28), (YA, max(13, int(28 * s)))),
            "slot": (("Consolas", 40, "bold"),
                     ("Consolas", max(15, int(40 * s)), "bold")),
            "status": ((YA, 16), (YA, max(11, int(16 * s)))),
            "rule": ((YA, 11), (YA, max(9, int(11 * s)))),
            "ctrl": ((YA, 11), (YA, max(10, int(11 * s)))),
        }
        for kind, (small, big) in fonts.items():
            try:
                if kind == "title":
                    self.lb_title.configure(font=big)
                elif kind == "stats":
                    self.lb_stats.configure(font=big)
                    self.lb_scope.configure(font=small)
                    self.lb_cum.configure(font=small)
                elif kind == "char":
                    self.lb_char.configure(font=big)
                elif kind == "py":
                    self.lb_py.configure(font=big)
                elif kind == "slot":
                    self.slot1.configure(font=big)
                    self.slot2.configure(font=big)
                elif kind == "status":
                    self.lb_status.configure(font=big)
                elif kind == "rule":
                    self.lb_rule.configure(font=small)
                elif kind == "ctrl":
                    self.scope_menu.configure(font=small)
                    self.cb_py.configure(font=small)
                    self.cb_kb.configure(font=small)
                    self.btn_reset.configure(font=small)
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

    def _scoped(self):
        n = dict(SCOPES)[self.scope_name.get()]
        return self.chars if n is None else self.chars[:n]

    def _next_char(self, first=False):
        pool = self._scoped() or self.chars
        last = None if first or self.cur is None else self.cur["c"]
        while True:
            self.cur = random.choice(pool)
            if last is None or self.cur["c"] != last or len(pool) < 2:
                break
        self.typed = ""
        self.state = "typing"
        self.lb_char.configure(text=self.cur["c"])
        self._toggle_py()
        self.slot1.configure(text="＿", fg=GREY)
        self.slot2.configure(text="＿", fg=GREY)
        self.lb_status.configure(text="输入两键编码", fg=GREY)
        self._refresh_stats()
        self._highlight_keys()

    def _toggle_py(self):
        if self.cur is None:
            return
        if self.show_py.get() or self.state != "typing":
            self.lb_py.configure(text=self.cur["p"])
        else:
            self.lb_py.configure(text="· ·（拼音已隐藏）")

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

    def _highlight_keys(self):
        self._draw_keyboard()

    # ---------- 键盘图（Canvas 圆角键帽，铺满下半区） ----------
    @staticmethod
    def _round_pts(x0, y0, x1, y1, r, seg=7):
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

    def _draw_keyboard(self, event=None):
        c = self.kcanvas
        W, H = c.winfo_width(), c.winfo_height()
        if W < 60 or H < 50 or self.cur is None:
            return
        c.delete("all")
        self.key_items = {}
        gap = max(5, int(W * 0.006))
        vgap = max(5, int(H * 0.045))
        rows = KB_ROWS
        key_h = (H - (len(rows) - 1) * vgap) / len(rows)
        key_h = min(key_h, 130)
        rad = min(20, key_h * 0.30)
        f_letter = ("Consolas", max(9, int(key_h * 0.20)), "bold")
        f_sub = (YA, max(8, int(key_h * 0.135)))
        k1, k2 = self.cur["f"][0].upper(), self.cur["f"][1].upper()
        for ri, row in enumerate(rows):
            n = len(row)
            kw = (W - (n + 1) * gap) / n
            y0 = ri * (key_h + vgap)
            for i, letter in enumerate(row):
                x0 = gap + i * (kw + gap)
                x1 = x0 + kw
                if letter == k1 == k2:
                    bg, fg, sfg = PURPLE, "#ffffff", "#ffffff"
                elif letter == k1:
                    bg, fg, sfg = BLUE, "#ffffff", "#dcebff"
                elif letter == k2:
                    bg, fg, sfg = ORANGE, "#ffffff", "#fff0d9"
                else:
                    bg, fg, sfg = KEY_BG, FG, GREY
                poly = c.create_polygon(
                    *self._round_pts(x0, y0, x0 + kw, y0 + key_h, rad),
                    smooth=True, fill=bg,
                    outline=("#c9d4e0" if bg == KEY_BG else bg), width=1)
                cx = x0 + kw / 2
                t1 = c.create_text(cx, y0 + key_h * 0.32, text=letter,
                                   font=f_letter, fill=fg)
                t2 = c.create_text(cx, y0 + key_h * 0.70,
                                   text=KB_INFO[letter], font=f_sub, fill=sfg)
                self.key_items[letter] = (poly, t1, t2)

    def _on_kb_configure(self, event):
        if self._kb_draw_job is not None:
            self.after_cancel(self._kb_draw_job)
        self._kb_draw_job = self.after(60, self._draw_keyboard)

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
            self.slot1.configure(text=self.typed, fg=BLUE)
        else:
            self.slot2.configure(text=self.typed[1], fg=ORANGE)
            self._judge()

    def _judge(self):
        exp = self.cur["f"]
        self.answered += 1
        self.cum["practiced"] += 1
        if self.typed == exp:
            self.ok += 1
            self.streak += 1
            self.best = max(self.best, self.streak)
            self.cum["correct"] += 1
            self.state = "locked_ok"
            self.slot1.configure(text=exp[0], fg=GREEN)
            self.slot2.configure(text=exp[1], fg=GREEN)
            msg = "✓ 正确！"
            if self.streak >= 3:
                msg += f"  连对 {self.streak}"
            self.lb_status.configure(text=msg, fg=GREEN)
            self._auto_next_job = self.after(420, self._continue)
        else:
            self.bad += 1
            self.streak = 0
            self.cum["wrong"] += 1
            self.state = "locked_no"
            self.slot1.configure(text=self.typed[0], fg=RED)
            self.slot2.configure(text=self.typed[1], fg=RED)
            self.lb_status.configure(
                text=f"✗ 正确编码：{exp[0]} {exp[1]}（空格继续）", fg=RED)
            self._toggle_py()
            self._auto_next_job = self.after(2600, self._continue)
        self._refresh_stats()
        self._save_stats()

    def _give_up(self):
        exp = self.cur["f"]
        self.answered += 1
        self.bad += 1
        self.streak = 0
        self.cum["practiced"] += 1
        self.cum["wrong"] += 1
        self.state = "locked_no"
        self.slot1.configure(text=exp[0], fg=ORANGE)
        self.slot2.configure(text=exp[1], fg=ORANGE)
        self.lb_status.configure(
            text=f"已跳过 · 正确编码：{exp[0]} {exp[1]}（空格继续）", fg=GREY)
        self._refresh_stats()
        self._save_stats()
        self._auto_next_job = self.after(2600, self._continue)

    def _continue(self):
        if self._auto_next_job is not None:
            self.after_cancel(self._auto_next_job)
            self._auto_next_job = None
        self._next_char()

    def reset_session(self):
        if self._auto_next_job is not None:
            self.after_cancel(self._auto_next_job)
            self._auto_next_job = None
        self.answered = self.ok = self.bad = 0
        self.streak = 0
        self.started_at = None
        self._next_char()

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
        n = dict(SCOPES)[self.scope_name.get()]
        self.lb_scope.configure(text=f"词库 {len(self._scoped())} 字")
        self.lb_cum.configure(
            text=f"累计已练 {c['practiced']} 字 · 正确率 {cacc:.0f}%")

    def _tick(self):
        try:
            self._refresh_stats()
        except tk.TclError:
            return
        self.after(1000, self._tick)

    # ---------- 持久化 / 缩放 ----------
    def _load_stats(self):
        try:
            with open(STATS_FILE, encoding="utf-8") as f:
                d = json.load(f)
            return {"practiced": int(d.get("practiced", 0)),
                    "correct": int(d.get("correct", 0)),
                    "wrong": int(d.get("wrong", 0))}
        except Exception:
            return {"practiced": 0, "correct": 0, "wrong": 0}

    def _save_stats(self):
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cum, f, ensure_ascii=False)
        except Exception:
            pass

    def on_resize(self, event):
        if event.widget is not self:
            return
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._rescale)

    def on_close(self):
        self._save_stats()
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
