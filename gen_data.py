# -*- coding: utf-8 -*-
"""一次性数据生成脚本：jieba 词频单字 + pypinyin 拼音 → 小鹤双拼编码
用法：uv run --with pypinyin python gen_data.py <dict.txt> <输出json>
"""
import json
import re
import sys

from pypinyin import pinyin, Style

DICT_PATH = sys.argv[1]
OUT_PATH = sys.argv[2]
TOP_N = 2000

# ---- 小鹤双拼转换规则（依据 Rime 官方 double_pinyin_flypy 方案推导）----
INITIALS2 = ("zh", "ch", "sh")
INI_MAP = {"zh": "v", "ch": "i", "sh": "u"}
INITIALS1 = set("bpmfdtnlgkhjqxrzcsyw")
# 韵母 → 键位（按全等匹配，顺序无关）
FINALS = [
    ("iang", "l"), ("uang", "l"), ("iong", "s"), ("iao", "n"), ("ian", "m"),
    ("uai", "k"), ("uan", "r"), ("ing", "k"), ("ang", "h"), ("ong", "s"),
    ("eng", "g"), ("ia", "x"), ("ua", "x"), ("ie", "p"), ("ve", "t"),
    ("ue", "t"), ("ui", "v"), ("un", "y"), ("iu", "q"), ("ei", "w"),
    ("ou", "z"), ("ao", "c"), ("ai", "d"), ("an", "j"), ("en", "f"),
    ("in", "b"), ("uo", "o"), ("a", "a"), ("o", "o"), ("e", "e"), ("i", "i"),
    ("u", "u"), ("v", "v"),
]


def to_flypy(syl):
    """全拼音节 → 两键小鹤编码；无法转换返回 None"""
    s = syl.strip().lower()
    if not re.fullmatch(r"[a-z]+", s):
        return None
    if s == "er":  # 唯一例外：er 原样
        return "er"
    if s[:2] in INITIALS2:
        ini, fin = s[:2], s[2:]
    elif s[0] in INITIALS1:
        ini, fin = s[0], s[1:]
    else:
        ini, fin = "", s  # 零声母
    for f, k in FINALS:
        if fin == f:
            if not ini:  # 零声母：韵母首字母 + 韵母键
                return fin[0] + k
            return INI_MAP.get(ini, ini) + k
    return None


# ---- 自检：覆盖声母/韵母/零声母/特殊音节 ----
CHECKS = {
    "han": "hj", "shi": "ui", "shuang": "ul", "ai": "ad", "jun": "jy",
    "yue": "yt", "zhui": "vv", "ruan": "rr", "nv": "nv", "kuai": "kk",
    "chuang": "il", "yun": "yy", "yong": "ys", "you": "yz", "jiu": "jq",
    "xu": "xu", "ju": "ju", "er": "er", "en": "ef", "a": "aa", "o": "oo",
    "e": "ee", "zhuang": "vl", "xiang": "xl", "qiong": "qs", "xue": "xt",
    "yuan": "yr", "shui": "uv", "zhu": "vu", "chu": "iu", "shu": "uu",
    "niao": "nn", "liang": "ll", "wei": "ww", "weng": "wg", "wu": "wu",
    "ya": "ya", "yi": "yi", "ying": "yk", "yin": "yb", "yan": "yj",
    "yang": "yh", "yao": "yc", "wen": "wf", "wang": "wh", "wai": "wd",
    "wan": "wj", "wo": "wo", "duan": "dr", "guai": "gk", "song": "ss",
    "suan": "sr", "shun": "uy", "chun": "iy", "zhun": "vy", "lun": "ly",
    "run": "ry", "gun": "gy", "bin": "bb", "bie": "bp", "diu": "dq",
    "zui": "zv", "shuo": "uo", "ruo": "ro", "zuo": "zo", "shei": "uw",
    "fen": "ff", "feng": "fg", "meng": "mg", "ang": "ah", "eng": "eg",
    "ao": "ac", "ou": "oz", "an": "aj", "ei": "ew", "liu": "lq",
    "niu": "nq",
}
bad = {k: (to_flypy(k), v) for k, v in CHECKS.items() if to_flypy(k) != v}
if bad:
    print("转换自检失败：", bad)
    sys.exit(1)
print(f"转换自检通过（{len(CHECKS)} 例）")

# ---- 从 jieba 词频表取常用单字 ----
freq = {}
with open(DICT_PATH, encoding="utf-8") as fh:
    for line in fh:
        parts = line.rstrip("\n").split(" ")
        if len(parts) < 2:
            continue
        w, f = parts[0], parts[1]
        if len(w) != 1:
            continue
        if not (0x4E00 <= ord(w) <= 0x9FFF):
            continue
        try:
            f = int(f)
        except ValueError:
            continue
        freq[w] = max(freq.get(w, 0), f)

chars = sorted(freq, key=lambda c: -freq[c])[: TOP_N * 2]
out, seen = [], set()
for ch in chars:
    if ch in seen:
        continue
    seen.add(ch)
    py_tone = pinyin(ch, style=Style.TONE, errors="ignore")[0][0]
    py_plain = pinyin(ch, style=Style.NORMAL, errors="ignore")[0][0]
    code = to_flypy(py_plain)
    if not code or len(code) != 2 or not re.fullmatch(r"[a-z]+", py_plain):
        continue
    out.append({"c": ch, "p": py_tone, "f": code})
    if len(out) >= TOP_N:
        break

with open(OUT_PATH, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False)
print(f"已生成 {len(out)} 个字 → {OUT_PATH}")
for e in out[:6]:
    print(e)
