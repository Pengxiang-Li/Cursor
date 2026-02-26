# 桌面应用分析：环境搭建选型

> 评估维度：用户常用性、A11y Tree 可获取性、程序化 API 可用性、Code 自动化能力
> 目标：确定各 OS 上值得纳入训练环境的应用

---

## 一、Linux (Ubuntu 24.04 GNOME)

### 1.1 A11y 基础设施

- **协议**: AT-SPI2 (D-Bus 协议)
- **Python 接口**: `pyatspi2`
- **支持范围**: GTK 应用原生支持；Qt 应用通过 ATK bridge 支持；Electron 应用需 `--force-renderer-accessibility`；Java/Swing 支持
- **系统工具**: `xdotool` (X11 键鼠模拟)、`xdg-open` (打开文件)、`gsettings`/`dconf` (GNOME 设置读写)
- **局限**: Wayland 下 `xdotool` 不可用，需 `ydotool` 或 `wtype` 替代；部分非 GTK 应用 A11y Tree 不完整

### 1.2 应用分析表

| 应用 | 类别 | 用户常用性 | A11y Tree | 程序化 API | Code 自动化方式 | 推荐度 |
|------|------|-----------|-----------|-----------|----------------|--------|
| **Files (Nautilus)** | 文件管理 | 高 | ✅ GTK 原生 | D-Bus 接口有限 | CLI: `mv`/`cp`/`mkdir`/`find` 可替代全部操作 | ★★★★★ |
| **Firefox** | 浏览器 | 高 | ✅ AT-SPI 支持 | Selenium / Playwright / CDP | 完整 browser automation 栈 | ★★★★★ |
| **LibreOffice Writer** | 文档编辑 | 高 | ✅ AT-SPI 支持 | **UNO API (Python)** 完整 | `from scriptforge import CreateScriptService`，可控制文档所有操作 | ★★★★★ |
| **LibreOffice Calc** | 电子表格 | 高 | ✅ AT-SPI 支持 | **UNO API (Python)** 完整 | 同 Writer，cell/sheet/chart 全可程序化 | ★★★★★ |
| **LibreOffice Impress** | 演示文稿 | 中 | ✅ AT-SPI 支持 | **UNO API (Python)** 完整 | 同上 | ★★★★ |
| **Terminal (GNOME Console)** | 终端 | 高 | ✅ GTK 原生 | 终端本身就是 code 接口 | 任意 shell 命令 | ★★★★★ |
| **Text Editor (gedit/GNOME Text Editor)** | 文本编辑 | 高 | ✅ GTK 原生 | D-Bus 有限；CLI 可替代 | `sed`/`awk`/`vim` CLI 替代 | ★★★★ |
| **VS Code** | IDE | 高 | ⚠️ Electron，需 `--force-renderer-accessibility` | Extension API + CLI (`code --goto`, `code --diff`) | CLI 丰富；Extension API 需写扩展 | ★★★★★ |
| **GIMP** | 图像编辑 | 中 | ⚠️ GTK，部分支持 | **Python-Fu / Script-Fu** 完整 | `gimp -i -b '(script-fu-...)'` 批处理；Python-Fu console | ★★★★ |
| **Settings (GNOME Settings)** | 系统设置 | 高 | ✅ GTK 原生 | **`gsettings` / `dconf`** 完整 | `gsettings set org.gnome.desktop.interface color-scheme prefer-dark` | ★★★★★ |
| **Thunderbird** | 邮件 | 中 | ⚠️ Mozilla，AT-SPI 部分支持 | 无直接 API | GUI 为主 | ★★★ |
| **Calculator** | 计算器 | 中 | ✅ GTK 原生 | 无直接 API | GUI 为主；`bc`/`python` CLI 替代 | ★★★ |
| **Archive Manager** | 压缩 | 中 | ✅ GTK 原生 | 无直接 API | `tar`/`zip`/`unzip` CLI 完全替代 | ★★★ |
| **Evince (Document Viewer)** | PDF 阅读 | 中 | ✅ GTK 原生 | D-Bus 接口有限 | GUI 为主 | ★★★ |
| **Rhythmbox / Videos (Totem)** | 媒体播放 | 低 | ✅ GTK 原生 | D-Bus (MPRIS) | `playerctl` CLI 控制播放 | ★★ |
| **Chromium** | 浏览器 | 中 | ⚠️ 需 `--force-renderer-accessibility` | Selenium / Playwright / CDP | 同 Firefox | ★★★★ |
| **Inkscape** | 矢量编辑 | 低 | ✅ GTK | CLI batch mode + Python extension | `inkscape --export-type=png input.svg` | ★★★ |

### 1.3 Linux 总结

**核心环境应用 (必装)**：Files, Firefox, LibreOffice (Writer/Calc/Impress), Terminal, VS Code, Settings, Text Editor

**关键优势**：
- GTK 应用 A11y 支持最好，pyatspi2 可直接遍历
- LibreOffice UNO API 是所有 OS 上最完整的 Office 程序化接口
- `gsettings`/`dconf` 可完全程序化控制 GNOME 设置
- 文件/系统操作全部有 CLI 替代

**主要问题**：
- Wayland 下键鼠模拟工具受限
- Electron 应用 (VS Code) 需额外配置才能暴露 A11y Tree
- 非 GTK 应用的 A11y 覆盖不完整

---

## 二、Windows

### 2.1 A11y 基础设施

- **协议**: Microsoft UI Automation (UIA)
- **Python 接口**: `pywinauto` (支持 UIA 和 Win32 双后端)
- **支持范围**: WinForms, WPF, UWP/Store Apps, Win32, Qt (需 `QT_USE_NATIVE_WINDOWS=1`)
- **系统工具**: `pywinauto`、`Accessibility Insights`、`Inspect.exe`、PowerShell
- **局限**: Chrome/Edge 需 `--force-renderer-accessibility`；部分老旧 Win32 应用 UIA 支持不完整

### 2.2 应用分析表

| 应用 | 类别 | 用户常用性 | A11y Tree | 程序化 API | Code 自动化方式 | 推荐度 |
|------|------|-----------|-----------|-----------|----------------|--------|
| **File Explorer** | 文件管理 | 高 | ✅ UIA 原生 | COM Shell.Application | COM + PowerShell; CLI: `cmd`/`robocopy`/`xcopy` | ★★★★★ |
| **Chrome / Edge** | 浏览器 | 高 | ⚠️ 需 `--force-renderer-accessibility` | Selenium / Playwright / CDP | 完整 browser automation | ★★★★★ |
| **Microsoft Word** | 文档编辑 | 高 | ✅ UIA 支持好 | **COM Automation** 完整 | `win32com.client.Dispatch("Word.Application")` 全功能 | ★★★★★ |
| **Microsoft Excel** | 电子表格 | 高 | ✅ UIA 支持好 | **COM Automation** 完整 | `win32com.client.Dispatch("Excel.Application")` 全功能 | ★★★★★ |
| **Microsoft PowerPoint** | 演示 | 中 | ✅ UIA 支持好 | **COM Automation** 完整 | `win32com.client.Dispatch("PowerPoint.Application")` | ★★★★★ |
| **Microsoft Outlook** | 邮件 | 高 | ✅ UIA 支持好 | **COM Automation** 完整 | `win32com.client.Dispatch("Outlook.Application")` | ★★★★ |
| **Notepad** | 文本编辑 | 高 | ✅ UIA 原生 (Win11 新版) | 无直接 API | pywinauto GUI 操作；CLI 文本工具替代 | ★★★★ |
| **VS Code** | IDE | 高 | ⚠️ Electron，需配置 | Extension API + CLI | 同 Linux | ★★★★★ |
| **Windows Terminal / CMD** | 终端 | 高 | ✅ UIA 支持 | 终端本身是 code 接口 | PowerShell / CMD 命令 | ★★★★★ |
| **Settings** | 系统设置 | 高 | ✅ UIA 原生 (UWP) | PowerShell + 注册表 | `Set-ItemProperty`, `reg add`, `netsh` 等 | ★★★★★ |
| **Calculator** | 计算器 | 中 | ✅ UIA 原生 (UWP) | 无直接 API | pywinauto 有官方示例 | ★★★★ |
| **Paint** | 图像编辑 | 中 | ✅ UIA 支持 (Win11 新版) | 无直接 API | GUI 为主 | ★★★ |
| **Photos** | 图片查看 | 中 | ✅ UIA (UWP) | 无直接 API | GUI 为主 | ★★ |
| **Microsoft Teams** | 通信 | 中 | ⚠️ Electron/Web | 有 Graph API (云端) | Graph API 可做部分操作 | ★★★ |
| **Slack (Desktop)** | 通信 | 中 | ⚠️ Electron，需配置 | Slack Web API | REST API 可替代大部分操作 | ★★★ |
| **Task Manager** | 系统监控 | 中 | ✅ UIA 支持 | PowerShell `Get-Process` | CLI 完全替代 | ★★★ |
| **LibreOffice** (可装) | Office 套件 | 中 | ✅ UIA 支持 | **UNO API** 完整 | 同 Linux | ★★★★ |
| **7-Zip** (可装) | 压缩 | 中 | ✅ Win32 UIA | CLI 接口 | `7z a/x` 完整 CLI | ★★★ |
| **WinRAR** (可装) | 压缩 | 中 | ✅ Win32 | CLI 接口 | CLI 替代 | ★★ |

### 2.3 Windows 总结

**核心环境应用 (必装)**：File Explorer, Chrome/Edge, MS Office (Word/Excel/PowerPoint), VS Code, Terminal/CMD, Settings, Notepad, Calculator

**关键优势**：
- UIA 覆盖最广：几乎所有原生 Windows 应用都有完整 A11y Tree
- MS Office COM Automation 是行业标准，Python `win32com` 可完全程序化控制
- UWP 应用 (Calculator, Settings 等) A11y 支持天然好
- PowerShell 可程序化控制大量系统功能

**主要问题**：
- Electron 应用需 `--force-renderer-accessibility` 才暴露完整 A11y
- 部分老旧 Win32 应用 UIA 支持不完整
- 需 Administrator 权限才能完整使用 UIA

---

## 三、macOS

### 3.1 A11y 基础设施

- **协议**: AXUIElement (Accessibility API)
- **Python 接口**: `pyax` (低级 AX API)、`PyXA` (高级 ScriptingBridge 包装)、`PyObjC` (Objective-C bridge)
- **脚本支持**: AppleScript、JXA (JavaScript for Automation)
- **支持范围**: 所有 Cocoa/AppKit 应用原生支持；Electron 应用需手动启用
- **系统工具**: `osascript` (执行 AppleScript)、`defaults` (读写 plist)、`open` (打开应用/文件)
- **局限**: 需用户在 System Preferences > Privacy & Security > Accessibility 中授权；SIP 限制部分系统应用操作

### 3.2 应用分析表

| 应用 | 类别 | 用户常用性 | A11y Tree | AppleScript 可编程 | Code 自动化方式 | 推荐度 |
|------|------|-----------|-----------|-------------------|----------------|--------|
| **Finder** | 文件管理 | 高 | ✅ 原生 | ✅ 完整 scriptable | `osascript -e 'tell app "Finder" to ...'`; CLI: `mv`/`cp`/`mkdir` | ★★★★★ |
| **Safari** | 浏览器 | 高 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 控制导航/标签; Playwright (WebKit) | ★★★★★ |
| **Chrome** | 浏览器 | 高 | ⚠️ 需 `--force-renderer-accessibility` | ⚠️ 有限 | Selenium / Playwright / CDP | ★★★★★ |
| **Pages** | 文档编辑 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 控制文档内容/格式 | ★★★★ |
| **Numbers** | 电子表格 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 控制 cell/sheet/chart | ★★★★ |
| **Keynote** | 演示 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 控制 slide/animation | ★★★★ |
| **TextEdit** | 文本编辑 | 高 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 控制文本内容 | ★★★★ |
| **Terminal** | 终端 | 高 | ✅ 原生 | ✅ scriptable | `osascript -e 'tell app "Terminal" to do script "ls"'` | ★★★★★ |
| **VS Code** | IDE | 高 | ⚠️ Electron，需配置 | ❌ 不 scriptable | Extension API + CLI | ★★★★★ |
| **Mail** | 邮件 | 高 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 收发邮件/搜索 | ★★★★ |
| **Calendar** | 日历 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 创建/查询事件 | ★★★ |
| **Notes** | 笔记 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 创建/编辑笔记 | ★★★ |
| **Preview** | 图片/PDF | 高 | ✅ 原生 | ⚠️ 有限 scriptable | AppleScript 基础操作；CLI: `sips` 图像处理 | ★★★ |
| **System Preferences / Settings** | 系统设置 | 高 | ✅ 原生 | ⚠️ 部分 scriptable | `defaults write/read` (plist); `networksetup`; `systemsetup` | ★★★★★ |
| **Automator** | 自动化 | 低 | ✅ 原生 | ✅ scriptable | 本身就是自动化工具 | ★★★ |
| **Contacts** | 通讯录 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 增删查改 | ★★★ |
| **Reminders** | 提醒 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 创建/完成提醒 | ★★★ |
| **Messages** | 消息 | 中 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 发送消息 | ★★★ |
| **Photos** | 图片管理 | 中 | ✅ 原生 | ✅ scriptable | AppleScript 导入/导出/管理相册 | ★★★ |
| **Music** | 音乐播放 | 低 | ✅ 原生 | ✅ 完整 scriptable | AppleScript 播放控制 | ★★ |
| **Xcode** | IDE | 低 (开发者) | ✅ 原生 | ✅ scriptable | AppleScript + `xcodebuild` CLI | ★★★ |
| **LibreOffice** (可装) | Office 套件 | 中 | ✅ Cocoa | ❌ 不 scriptable (但有 UNO API) | UNO API (Python) 完整 | ★★★★ |

### 3.3 macOS 总结

**核心环境应用 (必装)**：Finder, Safari, Chrome, Pages/Numbers/Keynote (或 LibreOffice), Terminal, VS Code, TextEdit, Mail, Settings

**关键优势**：
- 大量原生应用支持 AppleScript，可通过 `osascript` 直接程序化控制
- AX API 对 Cocoa 应用支持好，`pyax` 可遍历
- `defaults` 命令可直接读写系统/应用配置
- iWork 套件 (Pages/Numbers/Keynote) 全部完整 scriptable

**主要问题**：
- macOS VM 获取成本高（AWS Mac Dedicated Host、Orka）
- 需手动授权 Accessibility 权限（自动化环境中需预配置）
- Electron 应用 (VS Code) A11y 需额外配置
- SIP (System Integrity Protection) 限制部分系统层操作

---

## 四、跨平台对比

### 4.1 同类应用对比

| 功能 | Linux | Windows | macOS | 最佳 Code 自动化 |
|------|-------|---------|-------|------------------|
| 文件管理 | Nautilus | Explorer | Finder | 三平台 CLI 均完整 (`mv`/`cp`/`mkdir`) |
| 浏览器 | Firefox | Chrome/Edge | Safari/Chrome | Playwright/Selenium 跨平台统一 |
| 文档编辑 | LibreOffice Writer | MS Word | Pages / LibreOffice | Win: COM; Linux: UNO; macOS: AppleScript/UNO |
| 电子表格 | LibreOffice Calc | MS Excel | Numbers / LibreOffice | Win: COM (`openpyxl`); Linux: UNO; macOS: AppleScript/UNO |
| 演示 | LibreOffice Impress | MS PowerPoint | Keynote / LibreOffice | 同上 |
| 终端 | GNOME Terminal | Windows Terminal/CMD | Terminal.app | 三平台均天然 code 接口 |
| IDE | VS Code | VS Code | VS Code | CLI + Extension API 跨平台统一 |
| 文本编辑 | gedit/GNOME Text Editor | Notepad | TextEdit | Linux/macOS 有 scriptable; Win 纯 GUI |
| 系统设置 | GNOME Settings | Windows Settings | System Preferences | Linux: `gsettings`; Win: PowerShell/reg; macOS: `defaults` |
| 图像编辑 | GIMP | Paint | Preview | GIMP Python-Fu 最强; 其余 GUI 为主 |
| 邮件 | Thunderbird | Outlook | Mail | Win: COM; macOS: AppleScript; Linux: 弱 |

### 4.2 A11y Tree 可获取性对比

| 应用类型 | Linux (AT-SPI) | Windows (UIA) | macOS (AX API) |
|---------|---------------|--------------|----------------|
| 原生 GTK/Cocoa/WinForms | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| Qt 应用 | ⚠️ ATK bridge | ⚠️ 需配置 | ⚠️ 部分支持 |
| Electron 应用 | ⚠️ 需 flag | ⚠️ 需 flag | ⚠️ 需 flag |
| 浏览器内网页 | ✅ AT-SPI | ⚠️ 需 flag | ⚠️ 需 flag |
| Java/Swing | ✅ 支持 | ✅ 支持 | ⚠️ 有限 |
| 老旧应用 | ❌ 不支持 | ⚠️ Win32 部分 | N/A |

### 4.3 程序化 API 强度对比

| 应用类型 | Linux | Windows | macOS |
|---------|-------|---------|-------|
| Office 套件 | UNO API (强) | COM Automation (最强) | AppleScript (中) + UNO (强) |
| 浏览器 | Playwright/Selenium | Playwright/Selenium | Playwright/Selenium + AppleScript |
| 系统设置 | `gsettings`/`dconf` (强) | PowerShell + 注册表 (强) | `defaults` + `systemsetup` (中) |
| 文件操作 | CLI (强) | CLI + COM (强) | CLI + AppleScript (强) |
| 图像编辑 | GIMP Python-Fu (强) | Paint 无 API | Preview 有限; GIMP 可装 |

---

## 五、环境搭建建议

### 5.1 各 OS 必装应用清单

**Linux (Ubuntu 24.04 GNOME)**
```
预装即有: Files, Firefox, Terminal, Text Editor, Calculator, Settings, Evince, Archive Manager
需额外安装: LibreOffice, VS Code, GIMP, Chromium, Thunderbird
环境配置: 启用 AT-SPI, 安装 pyatspi2, xdotool
VS Code: 加 --force-renderer-accessibility 启动参数
```

**Windows 11**
```
预装即有: File Explorer, Edge, Notepad, Calculator, Paint, Settings, Terminal, Photos, Task Manager
需额外安装: MS Office (Word/Excel/PowerPoint), VS Code, Chrome, 7-Zip
需额外安装(可选): LibreOffice, Outlook
环境配置: 安装 pywinauto, 管理员权限
Chrome/Edge: 加 --force-renderer-accessibility
VS Code: 加 --force-renderer-accessibility
```

**macOS**
```
预装即有: Finder, Safari, TextEdit, Terminal, Preview, Mail, Calendar, Notes, Contacts,
          Reminders, Messages, Photos, Music, Pages, Numbers, Keynote, Settings
需额外安装: Chrome, VS Code, LibreOffice (可选)
环境配置: 安装 pyax/PyXA/PyObjC, 授权 Accessibility 权限
Chrome: 加 --force-renderer-accessibility
VS Code: 加 --force-renderer-accessibility
```

### 5.2 Verifier 构建难度

| 应用 | Verifier 方式 | 难度 | 三平台一致性 |
|------|-------------|------|-------------|
| 文件管理 | 检查文件系统状态 | 低 | 高 (三平台 CLI 统一) |
| 终端 | 检查命令输出/文件变化 | 低 | 高 |
| 文本编辑 | 读取文件内容 | 低 | 高 |
| 浏览器 | URL + DOM 状态 (Playwright) | 中 | 高 (Playwright 跨平台) |
| 系统设置 | 读取配置值 | 中 | 低 (各 OS 完全不同) |
| Office/文档 | 解析文档结构 | 中 | 中 (UNO 跨平台; COM 仅 Win) |
| 图像编辑 | 像素比对 | 高 | 低 |
| 邮件 | 检查发送/收件箱状态 | 高 | 低 |

### 5.3 优先级排序

综合用户常用性 × A11y 可获取性 × Code 自动化能力 × Verifier 可构建性：

| 优先级 | 应用 | 理由 |
|--------|------|------|
| P0 | 文件管理器 (三平台) | 高频 + CLI 完全替代 + Verifier 简单 |
| P0 | 浏览器 (三平台) | 高频 + Playwright 跨平台统一 + Verifier 中等 |
| P0 | 终端 (三平台) | 高频 + 天然 code 接口 + Verifier 简单 |
| P0 | Office 套件 (三平台) | 高频 + COM/UNO/AppleScript + Verifier 中等 |
| P0 | VS Code (三平台) | 高频 + CLI + Extension API |
| P1 | 系统设置 (三平台) | 高频 + 各有 CLI 工具 + Verifier 可做 |
| P1 | 文本编辑器 (三平台) | 高频 + Verifier 简单 |
| P2 | 图像编辑 (GIMP/Paint/Preview) | 中频 + GIMP 有 API + Verifier 难 |
| P2 | 邮件 (Thunderbird/Outlook/Mail) | 中频 + Verifier 难 |
| P3 | 媒体/日历/通讯录等 | 低频 |
