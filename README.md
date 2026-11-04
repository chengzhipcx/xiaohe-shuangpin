# 小鹤双拼练习

<p align="center"><img src="app.ico" width="96" alt="icon"></p>

Windows 桌面小程序（Python 标准库 tkinter，无任何第三方运行依赖）。
屏幕给出**汉字 + 全拼**，你输入对应的**小鹤双拼两键编码**，键盘图实时高亮两个目标键位。

## 运行

- 双击 `启动练习.bat`（无黑窗口）
- 或命令行：`python xiaohe_app.py`
- 或直接运行打包好的 `dist/小鹤双拼练习.exe`（免 Python 环境，也可到 [Releases](../../releases) 下载）

## 功能

- **主题可选**：跟随系统 / 浅色 / 深色（跟随系统会实时响应 Windows 深色模式切换，设置自动保存）
- **真实键盘布局**：数字行、Tab/Caps/Shift/Enter/空格等修饰键齐全、圆角键帽，
  蓝键 = 声母位，橙键 = 韵母位，两键相同时为紫色；U/I/V 键上红色标出 sh/ch/zh；可勾选关闭
- **显示拼音**：可关闭拼音，进入"盲打挑战"模式（答错后会揭示）
- **经典文本打字**：除常用字随机练习外，内置《道德经》全文与四书五经选篇——
  大学、中庸、论语、孟子、诗经、尚书、礼记、周易、左传，逐段打字，
  显示当前段与进度（第 x/y 段），每个字带校正过的文读拼音与双拼码，
  进度自动记忆，"重新开始"回到该内容开头
- **词库范围**：前 300 / 600 / 1000 / 1500 / 全部 2000 字（按词频从高到低）
- **统计**：对错、连对、正确率、速度（字/分）、累计练习记录（保存在 `stats.json`）
- **快捷键**：`空格` / `回车` = 跳过或继续
- **窗口可大可小**：拖动窗口边缘，汉字、编码、键盘图会随窗口自动缩放（支持 55%–220%）

## 编码规则（依据 Rime 官方 double_pinyin_flypy 方案）

| 声母 | 键 | 韵母 | 键 |
|---|---|---|---|
| zh | V | iu | Q |
| ch | I | ei | W |
| sh | U | uan / üan | R |
| | | ue / üe | T |
| | | un / ün | Y |
| | | uo | O |
| | | ie | P |
| | | ong / iong | S |
| | | ing / uai | K |
| | | iang / uang | L |
| | | ai | D |
| | | en | F |
| | | eng | G |
| | | ang | H |
| | | an | J |
| | | ou | Z |
| | | ia / ua | X |
| | | iao | N |
| | | ao | C |
| | | ui / ü | V |
| | | in | B |
| | | ian | M |

- 零声母音节（a、ai、an、ang、ao、e、ei、en、eng、o、ou）= **韵母首字母 + 韵母键**，
  如：爱 ai→ad、恩 en→ef、昂 ang→ah；唯一例外 **er→er**。
- y、w 按声母处理，韵母按全拼拼写取：外 wai→wd、万 wan→wj、王 wang→wh、要 yao→yc、
  云 yun→yy、月 yue→yt。
- j/q/x/y 后的 ü 按全拼写法用 u：去 qu→qu、需 xu→xu；n/l 后的 ü 用 v：女 nv→nv、绿 lv→lv。

## 数据来源

- 词库：jieba 词频词典单字，取前 2000 常用字（`gen_data.py` 生成，内含 77 例编码自检）
- 经典文本：`texts_src/` 内置 10 部书的原文数据（道德经全文，其余为名篇选段并已标注"（选）"），
  由 `gen_texts.py` 生成 `texts.json`，逐字附拼音与小鹤编码；
  古文多音字（如「不亦说乎」之「说」yuè、「三岁贯女」之「女」rǔ、「傅说」之「说」yuè）按文读校正。
  重新生成：`uv run --with pypinyin python gen_texts.py`
- 拼音：pypinyin（多音字取最常见读音，界面显示的拼音与期望编码始终一致）

## 打包为独立 exe（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=app.ico --name 小鹤双拼练习 ^
  --add-data "xiaohe_data.json;." --add-data "texts.json;." --add-data "app.ico;." xiaohe_app.py
```

生成的 exe 在 `dist/` 目录，双击即可运行，无需安装 Python。图标由 `gen_icon.py` 生成（`app.ico`）。
