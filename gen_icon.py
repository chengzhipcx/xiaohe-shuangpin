# -*- coding: utf-8 -*-
"""生成应用图标 app.ico：渐变蓝底 + 白色键帽 + 「鹤」字 + 小鹤双拼"""
import sys

from PIL import Image, ImageDraw, ImageFont

S = 256


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def font(path_fallbacks, size):
    for p in path_fallbacks:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    print("no font found", file=sys.stderr)
    sys.exit(1)


img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# 渐变背景（圆角方形）
grad = Image.new("RGBA", (S, S))
gd = ImageDraw.Draw(grad)
c_top, c_bot = (96, 165, 250), (21, 93, 214)
for y in range(S):
    gd.line([(0, y), (S, y)], fill=lerp(c_top, c_bot, y / S) + (255,))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([8, 8, S - 8, S - 8], radius=58, fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)

# 键帽（带投影 + 高光描边）
cap = [56, 40, 200, 176]
d.rounded_rectangle([cap[0] + 7, cap[1] + 12, cap[2] + 7, cap[3] + 12],
                    radius=30, fill=(10, 42, 96, 170))
d.rounded_rectangle(cap, radius=30, fill=(255, 255, 255, 255))
d.rounded_rectangle([cap[0] + 9, cap[1] + 9, cap[2] - 9, cap[3] - 30],
                    radius=24, outline=(214, 224, 238, 255), width=2)

# 「鹤」字
f_hanzi = font([r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                r"C:\Windows\Fonts\simhei.ttf"], 92)
d.text(((cap[0] + cap[2]) / 2, (cap[1] + cap[3]) / 2 - 4), "鹤",
       font=f_hanzi, fill=(28, 46, 70, 255), anchor="mm")

# 键帽右下角 V 键角标（小鹤双拼 zh 的键位）
f_key = font([r"C:\Windows\Fonts\consolab.ttf", r"C:\Windows\Fonts\msyhbd.ttc"], 26)
d.rounded_rectangle([158, 128, 194, 164], radius=9, fill=(255, 184, 0, 255))
d.text((176, 146), "V", font=f_key, fill=(255, 255, 255, 255), anchor="mm")

# 底部名称
f_name = font([r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"], 30)
d.text((128, 226), "小鹤双拼", font=f_name, fill=(255, 255, 255, 255), anchor="mm")

img.save(r"D:\projects\bxht\xiaohe-shuangpin\app.ico",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                (128, 128), (256, 256)])
img.save(r"D:\projects\bxht\xiaohe-shuangpin\_icon_preview.png")
print("icon saved")
