# -*- coding: utf-8 -*-
"""生成 texts.json：经典文本 + 逐字拼音 + 小鹤双拼编码。
用法：uv run --with pypinyin python gen_texts.py
"""
import json
import os
import re
import sys
import unicodedata

from pypinyin import pinyin, Style

from texts_src import BOOKS

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PYO = os.path.join(HERE, "xiaohe_data.json")
OUT_PATH = os.path.join(HERE, "texts.json")

# ---- 小鹤双拼转换（与 gen_data.py 一致）----
INITIALS2 = ("zh", "ch", "sh")
INI_MAP = {"zh": "v", "ch": "i", "sh": "u"}
INITIALS1 = set("bpmfdtnlgkhjqxrzcsyw")
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
    s = syl.strip().lower()
    if not re.fullmatch(r"[a-z]+", s):
        return None
    if s == "er":
        return "er"
    if s[:2] in INITIALS2:
        ini, fin = s[:2], s[2:]
    elif s[0] in INITIALS1:
        ini, fin = s[0], s[1:]
    else:
        ini, fin = "", s
    for f, k in FINALS:
        if fin == f:
            if not ini:
                return fin[0] + k
            return INI_MAP.get(ini, ini) + k
    return None


def tone_to_plain(s):
    return "".join(ch for ch in unicodedata.normalize("NFD", s)
                   if not unicodedata.combining(ch)).replace("ü", "v")


# ---- 多音字校正 ----
# 生僻字强制读音（经典文读，作用于全部经典文本）
PREEMPT = {
    "说": "yuè", "莩": "piǎo", "蕡": "fén", "摽": "biào", "姝": "shū",
    "俟": "sì", "娈": "luán", "踟": "chí", "蹰": "chú", "炜": "wěi",
    "荑": "tí", "洵": "xún", "贻": "yí", "琚": "jū", "玖": "jiǔ",
    "曷": "hé", "埘": "shí", "佸": "huó", "衿": "jīn", "喈": "jiē",
    "瘳": "chōu", "漙": "tuán", "瀼": "ráng", "廛": "chán", "貆": "huán",
    "穑": "sè", "辐": "fú", "漘": "chún", "囷": "qūn", "鹑": "chún",
    "飧": "sūn", "黍": "shǔ", "爰": "yuán", "溯": "sù", "洄": "huí",
    "萋": "qī", "晞": "xī", "湄": "méi", "跻": "jī", "坻": "chí",
    "涘": "sì", "沚": "zhǐ", "呦": "yōu", "苹": "píng", "簧": "huáng",
    "皋": "gāo", "渚": "zhǔ", "萚": "tuò", "榖": "gǔ", "篑": "kuì",
    "鳏": "guān", "肴": "yáo", "擭": "huò", "儽": "lěi", "飂": "liù",
    "朘": "zuī", "嗄": "shà", "橐": "tuó", "龠": "yuè", "纇": "lèi",
    "琭": "lù", "珞": "luò", "繟": "chǎn", "兕": "sì", "隳": "huī",
    "歙": "xī", "睨": "nì", "慥": "zào", "跲": "jiá", "蓍": "shī",
    "鼋": "yuán", "鼍": "tuó", "帱": "dào", "絅": "jiǒng", "鈇": "fū",
    "輶": "yóu", "缗": "mín", "諟": "shì", "懥": "zhì", "偾": "fèn",
    "媢": "mào", "寔": "shí", "僇": "lù", "翕": "xī", "揜": "yǎn",
    "啻": "chì", "廋": "sōu", "杇": "wū", "輗": "ní", "軏": "yuè",
    "饩": "xì", "鄹": "zōu", "缊": "yùn", "魋": "tuí", "葸": "xǐ",
    "黻": "fú", "洫": "xù", "僎": "zhuàn", "谌": "chén", "圉": "yǔ",
    "鮀": "tuó", "愬": "sù", "鞟": "kuò", "瑚": "hú", "琏": "liǎn",
    "醯": "xī", "骍": "xīng", "佾": "yì", "坫": "diàn", "蓧": "diào",
    "蒉": "kuì", "耰": "yōu", "騧": "guā", "鼗": "táo", "怵": "chù",
    "馁": "něi", "慊": "qiè", "闵": "mǐn", "揠": "yà", "瞷": "jiàn",
    "墦": "fán", "餍": "yàn", "雠": "chóu", "铄": "shuò", "畎": "quǎn",
    "鬲": "gé", "蹴": "cù", "弈": "yì", "炙": "zhì", "粢": "zī",
    "寤": "wù", "虢": "guó", "佗": "tuō", "雉": "zhì", "廪": "lǐn",
    "缮": "shàn", "寘": "zhì", "颍": "yǐng", "羹": "gēng", "繄": "yī",
    "刿": "guì", "孚": "fú", "轼": "shì", "翫": "wàn", "馨": "xīn",
    "氾": "fàn", "佚": "yì", "缒": "zhuì", "戍": "shù", "怼": "duì",
    "旌": "jīng", "泓": "hóng", "歼": "jiān", "勍": "qíng", "耇": "gǒu",
    "儳": "chán", "汜": "sì", "诬": "wū", "绵": "mián", "斋": "zhāi",
    "懿": "yì", "衷": "zhōng",
}

# 语境多音字：句内出现任一语境词时，该字读对应音
CTX_RULES = [
    ("说", "shuì", ["说大人"]),
    ("女", "rǔ", ["诲女知之", "女弗能救", "女为君子儒", "女奚不曰",
                  "女以予为多学", "女闻六言", "女安", "女为《周南》",
                  "匪女之为美", "怿女美", "三岁贯女", "逝将去女",
                  "往之女家", "与女偕隐", "女与回也孰愈", "女，器也"]),
    ("行", "hàng", ["行行如"]),
    ("恶", "wù", ["人之所恶", "物或恶之", "羞恶", "无恶于志", "恶而知其美",
                  "所恶于上", "恶郑声", "恶称人之恶者", "如恶恶臭",
                  "民之所恶", "众恶之", "恶居下流", "非恶其声", "遂恶之",
                  "恶人之所好", "货恶其弃", "力恶其不出", "我所恶",
                  "年四十而见恶焉", "亦有恶", "恶其文", "贱恶"]),
    ("乐", "yào", ["知者乐水", "仁者乐山", "尊德乐义"]),
    ("乐", "yuè", ["图为乐", "钟鼓云", "语暴以好乐", "好乐何如",
                   "王之好乐甚", "直好世俗", "今之乐犹古之乐", "为王言乐",
                   "乐云乐云"]),
    ("数", "cù", ["数罟"]),
    ("弟", "tì", ["孝弟", "出则弟", "民兴弟", "弟者，所以事长", "称弟"]),
    ("期", "jī", ["期月", "期之丧"]),
    ("重", "chóng", ["重积德"]),
    ("齐", "zhāi", ["齐，战，疾"]),
    ("叶", "shè", ["叶公"]),
    ("识", "zhì", ["默而识", "而识之", "小子识之"]),
    ("和", "hè", ["而后和之"]),
    ("孙", "xùn", ["不孙", "言孙", "孙以出之"]),
    ("称", "chèn", ["不称其力"]),
    ("曾", "zēng", ["曾子", "曾皙", "曾益"]),
    ("内", "nà", ["内交"]),
    ("施", "yì", ["施及庄公"]),
    ("施", "yí", ["唯施是畏", "施施从"]),
    ("阿", "ē", ["唯之与阿"]),
    ("帱", "dào", ["覆帱"]),
    ("於", "wū", ["於穆", "於乎", "於缉熙"]),
    ("队", "zhuì", ["霜露所队"]),
    ("射", "yì", ["矧可射思", "在此无射"]),
    ("缪", "miù", ["不缪"]),
    ("卷", "quán", ["卷石"]),
    ("暴", "pù", ["一日暴之", "无暴其气"]),
    ("共", "gōng", ["共叔段"]),
    ("亟", "jì", ["亟请"]),
    ("祭", "zhài", ["祭仲"]),
    ("辟", "pì", ["焉辟害", "辟人之士", "辟世", "辟地", "辟色", "辟言",
                  "而辟焉", "趋而辟之"]),
    ("遗", "wèi", ["请以遗之", "尔有母遗"]),
    ("语", "yù", ["公语之故"]),
    ("阙", "quē", ["阙地", "不阙秦", "阙秦以利晋"]),
    ("泄", "yì", ["其乐也泄"]),
    ("锡", "cì", ["永锡尔类"]),
    ("大", "tài", ["大伯", "京城大叔", "大王之昭"]),
    ("冯", "píng", ["神所冯"]),
    ("腊", "là", ["不腊矣"]),
    ("逢", "páng", ["逢孙"]),
    ("挑", "tāo", ["挑兮达兮"]),
    ("达", "tà", ["挑兮达兮"]),
    ("县", "xuán", ["尔庭有县"]),
    ("雨", "yù", ["雨雪"]),
    ("冠", "guàn", ["丈夫之冠"]),
    ("重", "shàng", ["不重伤", "如何勿重", "若爱重伤", "重有忧"]),
    ("长", "zhàng", ["敖不可长"]),
    ("从", "zòng", ["欲不可从"]),
    ("缴", "zhuó", ["弓缴"]),
    ("句", "gōu", ["宋句践"]),
    ("与", "jǔ", ["选贤与能"]),
    ("矜", "guān", ["矜、寡"]),
    ("分", "fèn", ["男有分"]),
    ("荷", "hè", ["以杖荷", "荷蓧", "荷蒉"]),
    ("絜", "jié", ["享祀丰絜", "粢盛既絜"]),
    ("絜", "xié", ["絜矩"]),
    ("谦", "qiè", ["此之谓自谦"]),
    ("胖", "pán", ["心广体胖"]),
    ("好", "hào", ["好学", "好为人师", "好谋而成", "从吾所好", "好德",
                   "王如好", "非能好", "好问", "好仁", "好察", "人之好我",
                   "好古", "王好战", "好游", "好从事", "民之所好好之",
                   "上好", "其心好之", "好勇", "好知", "好信", "好直",
                   "好刚", "好礼", "好义", "好善", "好径"]),
    ("鲜", "xiǎn", ["鲜能", "鲜矣", "天下鲜矣", "民鲜", "之道鲜矣"]),
    ("鲜", "xiān", ["烹小鲜"]),
    ("恶", "wū", ["恶乎"]),
    ("行", "xíng", ["行不言之教", "行己"]),
    # ---- 《弟子规》 ----
    ("说", "shuō", ["话说多", "彼说长", "此说短", "切莫说"]),
    ("行", "xíng", ["行勿懒", "力行", "行高者"]),
    ("应", "yìng", ["应勿缓"]),
    ("为", "wéi", ["擅为", "即为偷", "力为具"]),
    ("见", "xiàn", ["勿见能"]),
    ("处", "chǔ", ["居处变"]),
    ("长", "cháng", ["彼说长", "报恩长"]),
    ("弟", "tì", ["弟道恭", "兄弟睦"]),
    ("悌", "tì", ["首孝悌"]),
    ("省", "xǐng", ["晨则省", "即内省"]),
    ("号", "háo", ["号泣"]),
    ("更", "gēng", ["谏使更"]),
    ("凊", "qìng", ["夏则凊"]),
    ("便", "pián", ["便溺"]),
    ("溺", "niào", ["便溺"]),
    ("丧", "sāng", ["丧三年", "丧尽礼"]),
    ("恶", "wù", ["亲所恶"]),
    ("长", "zhǎng", ["长者", "尊长", "长呼人", "长无言", "长浮华",
                     "长国家"]),
    ("少", "shào", ["年方少"]),
    ("还", "huán", ["及时还", "还原处"]),
    ("的", "dì", ["知未的"]),
    ("重", "zhòng", ["凡道字", "人所重"]),
    ("訾", "zǐ", ["勿轻訾"]),
    ("几", "jī", ["几案"]),
    ("卷", "juǎn", ["卷束齐"]),
    ("屏", "bǐng", ["屏勿视"]),
    ("塞", "sè", ["滞塞"]),
    ("斗", "dòu", ["斗闹场"]),
    ("分", "fèn", ["上循分"]),
    ("称", "chèn", ["下称家"]),
    ("朝", "zhāo", ["朝起早"]),
    ("驯", "xún", ["可驯致"]),
    ("要", "yào", ["信皆要"]),
    # ---- 《黄帝内经》 ----
    ("夫", "fú", ["夫上古圣人", "夫自古通天者", "夫病已成", "夫道者"]),
    ("邪", "yé", ["材力尽邪"]),
    ("写", "xiè", ["乃能写"]),
    ("解", "xiè", ["筋骨解堕"]),
    # 「五藏」zàng：只放在各含单处「藏」的句级语境里；
    # 「肾者主水…」一句兼有「藏之」cáng，由 POS_MAPS 按位置指定
    ("藏", "zàng", ["今五藏皆衰", "浊阴走五藏", "其次治五藏", "治五藏者",
                    "人有五藏化五气", "五藏、十二节"]),
    ("肖", "xiào", ["不肖"]),
    ("为", "wéi", ["夏为寒变", "秋为痎疟", "冬为飧泄", "春为痿厥"]),
    ("处", "chǔ", ["居处变", "处百病"]),
    # 「发长极」cháng 由 POS_MAPS 按位置指定（同句的齿更发长读 zhǎng）
    ("长", "cháng", ["长有天命"]),
    ("调", "tiáo", ["调虚实"]),
    ("被", "pī", ["被发"]),
    ("蕃", "fán", ["蕃秀"]),
    ("惔", "dàn", ["恬惔"]),
    ("薄", "bó", ["使人薄厥"]),
    ("疟", "nüè", ["痎疟"]),
    ("痎", "jiē", ["痎疟"]),
    ("亟", "qì", ["使气亟夺"]),
    ("数", "shuò", ["数犯此"]),
    ("辟", "bì", ["辟积"]),
    ("菀", "yù", ["血菀"]),
    ("卒", "cù", ["卒然逢疾风"]),
]

# 位置校正：整句内按偏移指定读音
POS_MAPS = {
    "独乐乐，与人乐乐，孰乐": {1: "yuè", 4: "yuè"},
    "与少乐乐，与众乐乐，孰乐": {2: "yuè", 3: "lè", 7: "yuè", 8: "lè"},
    # 上古天真论：句内「五藏」zàng 而通假「藏之」cáng，句级语境无法区分
    "肾者主水，受五藏六府之精而藏之，故五藏盛，乃能写。": {7: "zàng", 18: "zàng"},
    # 上古天真论：同一句里 齿更发长(zhǎng)／真牙生而长极(zhǎng)／发长极(cháng)
    ("女子七岁，肾气盛，齿更发长；二七而天癸至，任脉通，太冲脉盛，月事以时下，"
     "故有子；三七，肾气平均，故真牙生而长极；四七，筋骨坚，发长极，身体盛壮"):
        {12: "zhǎng", 53: "zhǎng", 64: "cháng"},
}

HANZI = re.compile(r"[\u3400-\u9fff]")


def sentence_spans(body):
    """[(start, end, text)]，句以 。？！ 分隔；无句读的段落整体成句。"""
    spans, start = [], 0
    for m in re.finditer(r"[。？！]", body):
        end = m.end()
        seg = body[start:end]
        if HANZI.search(seg):
            spans.append((start, end, seg))
        start = end
    if start < len(body):
        seg = body[start:]
        if HANZI.search(seg):
            spans.append((start, len(body), seg))
    return spans


def main():
    with open(BASE_PYO, encoding="utf-8") as f:
        base = {e["c"]: (e["p"], e["f"]) for e in json.load(f)}

    missing = []
    texts = []
    total = 0

    for book in BOOKS:
        chaps = []
        for title, body in book.CHAPS:
            pyl = [None] * len(body)     # 与 body 逐位对齐：[带调拼音, 双拼码]
            for s0, s1, sent in sentence_spans(body):
                for i in range(s0, s1):
                    c = body[i]
                    if not HANZI.fullmatch(c):
                        continue
                    disp = None
                    # 1) 位置校正（同章内同字异读，如「独乐乐」）
                    for substr, idxmap in POS_MAPS.items():
                        p = sent.find(substr)
                        if p >= 0 and (i - s0 - p) in idxmap:
                            disp = idxmap[i - s0 - p]
                            break
                    # 2) 语境校正
                    if disp is None:
                        for ch, d, ctxs in CTX_RULES:
                            if ch == c and any(x in sent for x in ctxs):
                                disp = d
                                break
                    # 3) 生僻字强制
                    if disp is None and c in PREEMPT:
                        disp = PREEMPT[c]
                    # 4) 常用字表 / 5) pypinyin
                    if disp is not None:
                        plain = tone_to_plain(disp)
                        code = to_flypy(plain)
                        if not code or len(code) != 2:
                            missing.append((book.ID, title, c, disp, "code"))
                            continue
                        pyl[i] = [disp, code]
                    elif c in base:
                        pyl[i] = list(base[c])
                    else:
                        t = pinyin(c, style=Style.TONE, errors="ignore")[0][0]
                        n = pinyin(c, style=Style.NORMAL, errors="ignore")[0][0]
                        code = to_flypy(n)
                        if not re.fullmatch(r"[a-z]+", n) or not code or len(code) != 2:
                            missing.append((book.ID, title, c, t, "py"))
                            continue
                        pyl[i] = [t, code]
            chaps.append({"t": title, "body": body, "pyl": pyl})
            total += sum(1 for e in pyl if e)
        texts.append({"id": book.ID, "name": book.NAME,
                      "select": book.SELECT, "chapters": chaps})

    out = {"texts": texts}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"已生成 {OUT_PATH}")
    print(f"共 {len(texts)} 部书，{total} 条逐位拼音，覆盖 {sum(len(HANZI.findall(ch['body'])) for t in texts for ch in t['chapters'])} 个待练字")
    if missing:
        print("缺失/异常：")
        for m in missing:
            print("  ", m)
        sys.exit(1)


if __name__ == "__main__":
    main()
