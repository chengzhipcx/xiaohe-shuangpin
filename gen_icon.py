# -*- coding: utf-8 -*-
"""生成应用图标 app.ico：渐变蓝底 + 白色键帽 + 「鹤」字 + V 键角标。

每个尺寸独立绘制（小尺寸自动省略细描边/底部文字、加大主字形），
避免从 256 母版直接缩小导致的模糊。用法：python gen_icon.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(HERE, "app.ico")
PREVIEW_PATH = os.path.join(HERE, "_icon_preview.png")
SIZES = [16, 20, 24, 32, 48, 64, 128, 256]


def font(path_fallbacks, size):
    for p in path_fallbacks:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    print("no font found", file=sys.stderr)
    sys.exit(1)


def draw(S):
    """按目标尺寸原生绘制一帧（坐标全部按 256 母版比例缩放）。"""
    k = S / 256.0
    tier_full = S >= 96          # 全要素：投影/描边/角标字母/底部文字
    tier_mid = 32 <= S < 96      # 中档：投影/角标色块，无底部文字
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # 渐变背景（圆角方形）
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    c_top, c_bot = (96, 165, 250), (21, 93, 214)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=lerp(c_top, c_bot, y / S) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [round(8 * k)] * 2 + [S - round(8 * k)] * 2,
        radius=max(2, round(58 * k)), fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    tiny = S < 48
    # 小尺寸键帽放大占满，主字形加描边增粗
    cap = [round(v * k) for v in ((48, 32, 208, 184) if tiny
                                  else (56, 40, 200, 176))]

    # 键帽投影 + 高光描边（小尺寸省略，避免糊成灰边）
    if tier_full or tier_mid:
        d.rounded_rectangle(
            [cap[0] + max(1, round(7 * k)), cap[1] + max(1, round(12 * k)),
             cap[2] + max(1, round(7 * k)), cap[3] + max(1, round(12 * k))],
            radius=max(2, round(30 * k)), fill=(10, 42, 96, 170))
    d.rounded_rectangle(cap, radius=max(2, round(30 * k)),
                        fill=(255, 255, 255, 255))
    if tier_full:
        d.rounded_rectangle(
            [cap[0] + round(9 * k), cap[1] + round(9 * k),
             cap[2] - round(9 * k), cap[3] - round(30 * k)],
            radius=max(2, round(24 * k)), outline=(214, 224, 238, 255),
            width=max(1, round(2 * k)))

    # 「鹤」字：小尺寸相对放大并加描边，保证笔画可辨
    hanzi_size = round(92 * k) if tier_full else max(round(92 * k),
                                                     round(S * 0.50))
    f_hanzi = font([r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                    r"C:\Windows\Fonts\simhei.ttf"], hanzi_size)
    d.text(((cap[0] + cap[2]) / 2, (cap[1] + cap[3]) / 2 - 4 * k), "鹤",
           font=f_hanzi, fill=(28, 46, 70, 255), anchor="mm")

    # 右下角 V 键角标（小鹤双拼 zh 的键位）
    if tier_full or tier_mid:
        badge = [round(v * k) for v in (158, 128, 194, 164)]
        d.rounded_rectangle(badge, radius=max(1, round(9 * k)),
                            fill=(255, 184, 0, 255))
        if tier_full:
            f_key = font([r"C:\Windows\Fonts\consolab.ttf",
                          r"C:\Windows\Fonts\msyhbd.ttc"], round(26 * k))
            d.text(((badge[0] + badge[2]) / 2, (badge[1] + badge[3]) / 2),
                   "V", font=f_key, fill=(255, 255, 255, 255), anchor="mm")

    # 底部名称（仅大尺寸保留，小尺寸缩成噪点）
    if tier_full:
        f_name = font([r"C:\Windows\Fonts\msyhbd.ttc",
                       r"C:\Windows\Fonts\msyh.ttc"], round(30 * k))
        d.text((S / 2, 226 * k), "小鹤双拼", font=f_name,
               fill=(255, 255, 255, 255), anchor="mm")
    return img


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    frames = {S: draw(S) for S in SIZES}
    master = frames[256]
    master.save(ICO_PATH, sizes=[(S, S) for S in SIZES],
                append_images=[frames[S] for S in SIZES if S != 256])

    # 预览图：小尺寸按 4 倍最近邻放大，直观看清晰度
    pad = 8
    shown = [16, 20, 24, 32, 48, 64]
    tiles = [frames[S].resize((S * 4, S * 4), Image.NEAREST) for S in shown]
    W = sum(t.width for t in tiles) + pad * (len(tiles) + 1)
    H = max(t.height for t in tiles) + pad * 2
    grid = Image.new("RGBA", (W, H), (40, 44, 52, 255))
    x = pad
    for t in tiles:
        grid.paste(t, (x, pad), t)
        x += t.width + pad
    grid.save(PREVIEW_PATH)

    with Image.open(ICO_PATH) as im:
        print("ico 帧数:", len(im.info.get("sizes", [])))
    print("icon saved:", ICO_PATH)


if __name__ == "__main__":
    main()
