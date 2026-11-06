# 小鹤双拼练习

<p align="center"><img src="app.ico" width="96" alt="icon"></p>

跨平台桌面练习工具（Python 标准库 tkinter，**无任何第三方运行依赖**），帮助你快速掌握小鹤双拼的键位映射。
屏幕给出**汉字 + 全拼**，你输入对应的**小鹤双拼两键编码**，真实键盘图实时高亮两个目标键位。

支持 **Windows**（独立 exe）与 **macOS**（dmg，Apple Silicon / Intel 两个版本）。

## 下载

| 平台 | 包 | 说明 |
|---|---|---|
| Windows | [Releases 页](https://github.com/chengzhipcx/xiaohe-shuangpin/releases) 的 `.exe` | 单文件、免安装、免 Python 环境 |
| macOS（Apple Silicon / M 系列） | `XiaoheShuangpin-*-macOS-arm64.dmg` | M1/M2/M3/M4 |
| macOS（Intel） | `XiaoheShuangpin-*-macOS-Intel.dmg` | Intel 处理器的 Mac |

源码运行：`python xiaohe_app.py`（Python 3.8+，仅标准库）

## 功能

- **真实键盘布局**：数字行 + Tab/Caps/Shift/Enter/空格等修饰键齐全、圆角键帽、按真实键距错位排布；
  蓝键 = 声母位，橙键 = 韵母位，两键相同时为紫色；U/I/V 键上红色标出 sh/ch/zh；可勾选关闭
- **主题三态**：跟随系统 / 浅色 / 深色。跟随系统时实时响应 Windows 深色模式切换，标题栏颜色同步（DWM），设置自动保存
- **显示拼音**：可关闭拼音进入"盲打挑战"模式（答错后会自动揭示）
- **经典文本打字**：除常用字随机练习外，内置《道德经》全文与四书五经选篇——
  大学、中庸、论语、孟子、诗经、尚书、礼记、周易、左传，逐段打字；
  顶部两行显示整句上下文（当前字高亮、已打置灰、自动滚动），
  显示进度（第 x/y 段），每个字带校正过的文读拼音与双拼码，进度自动记忆
- **错字重练**：常用字模式中答错的字会按概率重新出现，答对后移出错字表
- **词库范围**：前 300 / 600 / 1000 / 1500 / 全部 2000 字（按词频从高到低）
- **统计**：对错、连对、正确率、速度（字/分）、累计练习记录
- **快捷键**：`空格` / `回车` = 跳过或继续；经典模式 `Ctrl+←` / `Ctrl+→` = 上/下一段（可跨章）
- **窗口自适应**：拖动窗口边缘，汉字、编码、键盘图随窗口自动缩放（55%–220%）；快速连打不丢键（两键缓冲）

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

## 安装与使用

### Windows

1. 到 [Releases](https://github.com/chengzhipcx/xiaohe-shuangpin/releases) 下载最新 `.exe`，双击即可运行（免 Python 环境）
2. 或克隆仓库：`python xiaohe_app.py` / 双击 `启动练习.bat`
3. 练习进度保存在 exe 同目录的 `stats.json`

### macOS

1. 到 [Releases](https://github.com/chengzhipcx/xiaohe-shuangpin/releases) 下载对应架构的 `.dmg`（见上表），
   拖入「应用程序」
2. **首次打开**（未签名应用会提示"无法验证开发者"）：
   - 右键应用 →「打开」，再点一次「打开」；或
   - 终端执行 `xattr -cr /Applications/小鹤双拼练习.app` 后正常双击
3. 选错架构会显示禁止符号（提示应用不可用）——Apple Silicon 用 `-arm64`，Intel 用 `-Intel`
4. 界面字体自动切换为苹方 / Menlo；练习进度存于 `~/.xiaohe-shuangpin/stats.json`

## 自行构建

### Windows exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=app.ico --name 小鹤双拼练习 ^
  --add-data "xiaohe_data.json;." --add-data "texts.json;." --add-data "app.ico;." xiaohe_app.py
```

生成的 exe 在 `dist/`。图标由 `gen_icon.py` 生成（`app.ico` / `app.icns`，各尺寸独立绘制）。

### macOS dmg

- **本地**（需在 mac 上）：
  ```bash
  pip install pyinstaller
  pyinstaller --windowed --name 小鹤双拼练习 --icon app.icns \
    --add-data "xiaohe_data.json:." --add-data "texts.json:." xiaohe_app.py
  hdiutil create -volname 小鹤双拼练习 -srcfolder dist/小鹤双拼练习.app -ov -format UDZO dist/小鹤双拼练习.dmg
  ```
- **CI**：仓库内置 GitHub Actions（`.github/workflows/build-macos.yml`），
  推送 tag（如 `v1.1.0`）即在 macOS 上自动打包 **arm64 与 Intel 两个 dmg** 并发布到 Releases；
  也可在 Actions 页面手动 Run workflow 下载 artifact。

## 技术要点

- **零依赖**：仅 Python 标准库（tkinter / ctypes / winreg / json），单文件主程序 `xiaohe_app.py`
- **主题**：Windows 注册表轮询跟随系统深浅色；标题栏经 DWM `DWMWA_CAPTION_COLOR` 同步应用主题色
- **键盘高亮**：Canvas 绘制真实 ANSI 布局；逐字改为**增量重着色**（仅新旧目标键变色），非全量重绘
- **文本数据**：`texts.json` 与正文逐位对齐的拼音/双拼码数组（`pyl`），支持同字异读与古文文读校正
- **稳健性**：`stats.json` 原子写（临时文件 + `os.replace`）；答对锁定期间缓存两键，快速连打不丢键
- **图标**：16–1024 多尺寸各自独立绘制（小尺寸自动省略细描边、放大主字形），非母版缩放

## License

[MIT](LICENSE)
