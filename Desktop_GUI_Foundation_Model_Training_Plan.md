# Desktop GUI 基础模型训练完整方案

> 目标：基于 Qwen 系列（2B → 300B）训练全平台（Windows / macOS / Linux）Desktop GUI 基础模型
> 能力要求：GUI 感知 → Grounding → 动作预测 → 端到端任务完成
> 输入模态：截图 + Accessibility Tree + DOM/UI Hierarchy（混合）
> 动作空间：像素坐标 + 元素级 + 代码级（PyAutoGUI）+ API 调用（混合）
> 分辨率：1080p

---

## 第一部分：开源数据集使用方案

### 1.1 数据分配总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                    训练数据分层架构                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Stage 1: 视觉感知预训练 (UI Understanding)                          │
│  ├── OS-ATLAS (13M+ GUI elements, 跨平台)           ★★★★★ 核心      │
│  ├── Rico (66K screens, 3M elements)                 ★★★★  辅助      │
│  ├── GroundCUA (3.56M annotations)                   ★★★★★ 核心      │
│  ├── Jedi (4M synthetic samples)                     ★★★★  辅助      │
│  └── GUICourse (多阶段 OCR/grounding)                ★★★   辅助      │
│      预期数据量：~20M+ 样本                                          │
│                                                                     │
│  Stage 2: GUI Grounding 训练                                        │
│  ├── OS-ATLAS 桌面子集                               ★★★★★ 核心      │
│  ├── GroundCUA                                       ★★★★★ 核心      │
│  ├── Jedi                                            ★★★★  辅助      │
│  ├── ScreenSpot / ScreenSpot-Pro (eval only)         ★★★   评测      │
│  └── 自建跨平台 Grounding 数据                       ★★★★★ 核心      │
│      预期数据量：~10M+ 样本                                          │
│                                                                     │
│  Stage 3: 动作预测 & 轨迹训练                                        │
│  ├── GUI-360° (1.2M action steps, Windows)           ★★★★★ 核心      │
│  ├── ScaleCUA (6 OS, large-scale)                    ★★★★★ 核心      │
│  ├── OmniACT (截图 → PyAutoGUI)                     ★★★★  辅助      │
│  ├── Mind2Web (2K+ web tasks)                        ★★★   辅助      │
│  ├── AITW (715K episodes, 跨平台迁移)                ★★★   辅助      │
│  ├── GUIAct (127K~1.26M rows)                        ★★★★  辅助      │
│  └── 自建桌面轨迹数据                                ★★★★★ 核心      │
│      预期数据量：~5M+ 轨迹步骤                                       │
│                                                                     │
│  Stage 4: 端到端指令跟随 & Agent 微调                                │
│  ├── GUI-360° (含 reasoning trace)                   ★★★★  核心      │
│  ├── AgentTrek (教程 → 轨迹)                         ★★★★  方法论    │
│  ├── OS-Genesis (逆向任务合成)                        ★★★★★ 方法论    │
│  ├── NatureGAIA (自纠正轨迹)                         ★★★   辅助      │
│  └── 自建高质量指令跟随数据                          ★★★★★ 核心      │
│      预期数据量：~1M+ 完整轨迹                                       │
│                                                                     │
│  Evaluation Benchmarks                                              │
│  ├── OSWorld (369 tasks, 跨 OS)                      ← 主评测        │
│  ├── Windows Agent Arena (154+ tasks)                ← Windows 评测  │
│  ├── ScreenSpot-Pro (1.59K, 专业应用)                ← Grounding 评测│
│  ├── UI-Vision (83 apps)                             ← 感知评测      │
│  ├── MMBench-GUI (层次化跨平台)                      ← 综合评测      │
│  └── AssistGUI (100 tasks, 专业软件)                 ← 专业软件评测  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 各数据集详细使用方式

#### Stage 1: 视觉感知预训练

**目标**：让模型理解 UI 截图的结构——识别元素类型、读取文字、理解布局。

| 数据集 | 使用方式 | 数据量 | 处理建议 |
|--------|---------|--------|---------|
| OS-ATLAS | 提取桌面部分（Win/Linux/macOS），构建"截图 → 元素列表+坐标"对 | ~数百万 | 按 OS 均衡采样 |
| Rico | 虽是 mobile，但 UI 元素类型（按钮/文本/图标）通用；作为补充预训练数据 | 66K screens | 需 resize 到 1080p 尺度 |
| GroundCUA | 密集标注的截图-元素对，直接用于视觉感知 | 56K screenshots | 高质量，优先使用 |
| Jedi | 合成 grounding 数据，增强数据多样性 | 4M | 作为数据增强 |
| GUICourse | OCR 阶段数据 + 基础 grounding | 按课程分阶段 | 用于 curriculum learning 的最早期 |

**训练任务设计**：
```
Task 1: UI Element Recognition
  Input:  <screenshot>
  Output: [{"type": "button", "text": "Save", "bbox": [x1,y1,x2,y2]}, ...]

Task 2: OCR on Screenshots
  Input:  <screenshot> 请识别截图中的所有文字及其位置
  Output: [{"text": "File", "bbox": [10,5,40,20]}, {"text": "Edit", "bbox": [45,5,75,20]}, ...]

Task 3: Layout Understanding
  Input:  <screenshot> 描述这个界面的整体布局结构
  Output: "这是一个典型的桌面IDE界面：顶部是菜单栏(File/Edit/View...)，
           左侧是文件资源管理器面板，中央是代码编辑区域(多标签页)，
           底部是终端/输出面板，右侧是大纲视图。"

Task 4: Element Attribute Extraction
  Input:  <screenshot> + <a11y_tree>
  Output: 结构化的元素属性表（role, name, state, bounds）
```

#### Stage 2: GUI Grounding 训练

**目标**：给定自然语言指令，精准定位到 UI 截图中的目标元素坐标。

| 数据集 | 使用方式 | 注意事项 |
|--------|---------|---------|
| OS-ATLAS (桌面部分) | 核心 grounding 训练数据，含元素坐标 + 文本描述 | 需过滤出 Win/Linux/macOS |
| GroundCUA | 密集标注，高质量 grounding 对 | 直接可用 |
| Jedi | 合成增强 | 与真实数据混合使用 |
| 自建数据 | 基于 a11y tree 自动生成 grounding 对 | 见第二部分 |

**训练任务设计**：
```
Task 1: Text-based Grounding
  Input:  <screenshot> 点击"保存"按钮
  Output: {"action": "click", "coordinate": [523, 47]}

Task 2: Icon/Widget Grounding
  Input:  <screenshot> 点击搜索图标
  Output: {"action": "click", "coordinate": [892, 35]}

Task 3: Descriptive Grounding
  Input:  <screenshot> 点击左上角的文件菜单
  Output: {"action": "click", "coordinate": [25, 12]}

Task 4: Multi-modal Grounding (Screenshot + A11y Tree)
  Input:  <screenshot> + <a11y_tree> 找到名为"New File"的菜单项
  Output: {"element_id": "menu_item_3", "coordinate": [120, 85], "role": "MenuItem"}
```

#### Stage 3: 动作预测 & 轨迹训练

**目标**：给定当前截图和任务目标，预测下一步操作。

| 数据集 | 使用方式 | 数据量 | 处理建议 |
|--------|---------|--------|---------|
| GUI-360° | 核心桌面轨迹数据，含完整推理链 | 1.2M steps | 直接使用，需关注 Windows 偏向 |
| ScaleCUA | 跨平台轨迹 | 大规模 | 提取桌面 OS 部分 |
| OmniACT | 截图 → PyAutoGUI 脚本映射 | 中等 | 训练代码级动作输出 |
| Mind2Web | Web 交互轨迹 | 2K+ tasks | 浏览器操作部分与桌面通用 |
| AITW | Mobile 轨迹（大规模） | 715K | 交互模式可迁移，需格式转换 |
| GUIAct | GUI 交互动作标注 | 127K~1.26M | 直接可用 |
| 自建数据 | 跨平台桌面轨迹 | 目标：百万级 | 见第二部分 |

**训练任务设计（多动作空间统一格式）**：
```
Task 1: Pixel-level Action Prediction
  Input:  <screenshot> + "打开终端" + [history_screenshots]
  Output: {"thought": "需要右键点击桌面空白处打开上下文菜单",
           "action_type": "click",
           "coordinate": [640, 400],
           "button": "right"}

Task 2: Element-level Action Prediction
  Input:  <screenshot> + <a11y_tree> + "在文档中插入表格"
  Output: {"thought": "需要先点击菜单栏中的'插入'选项",
           "action_type": "click",
           "element_id": "menu_insert",
           "element_role": "MenuItem",
           "element_name": "Insert"}

Task 3: Code-level Action Generation
  Input:  <screenshot> + "将窗口移到屏幕右半部分"
  Output: {"thought": "需要使用系统快捷键将窗口 snap 到右侧",
           "action_type": "hotkey",
           "code": "pyautogui.hotkey('win', 'right')"}

Task 4: API-level Action
  Input:  <screenshot> + "打开 VS Code 并新建一个 Python 文件"
  Output: {"thought": "可以通过命令行直接打开 VS Code 并创建文件",
           "action_type": "api_call",
           "command": "code --new-window && code --goto new_file.py"}
```

#### Stage 4: 端到端指令跟随 & Agent 微调

**目标**：完整的 multi-step 任务执行 + 推理 + 自纠正。

**训练任务设计**：
```
Full Trajectory Training:
  Input:  "请在 LibreOffice Writer 中创建一份会议纪要模板，包含标题、日期、参会人员、
           议题列表和行动项表格"
  Output: [
    {"step": 1, "thought": "首先打开 LibreOffice Writer",
     "screenshot_before": <img>, "action": {"type": "click", "target": "LibreOffice Writer icon", "coord": [45, 780]}},
    {"step": 2, "thought": "输入标题 '会议纪要'",
     "screenshot_before": <img>, "action": {"type": "type", "text": "会议纪要\n"}},
    {"step": 3, "thought": "设置标题格式为居中加粗",
     "screenshot_before": <img>, "action": {"type": "hotkey", "keys": ["ctrl", "e"]}},
    ...
    {"step": N, "thought": "任务完成，已创建完整模板",
     "screenshot_before": <img>, "action": {"type": "done"}}
  ]
```

---

## 第二部分：自建数据管线设计

### 2.1 设计原则

鉴于你的资源特点（大模型 API 充足、人工团队有限），数据管线应以 **模型驱动 + 自动化 + 少量人工质检** 为核心策略。

### 2.2 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        自建数据管线架构                                      │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ 环境基础设施  │───▶│ 数据采集引擎  │───▶│ 质量控制系统  │───▶│ 数据仓库   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘  │
│         │                    │                    │                │         │
│    VM 集群管理          自动化采集            模型评估+人工        统一格式存储 │
│    跨 OS 覆盖          多种策略并行          抽样质检             版本管理     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 模块一：跨平台环境基础设施

```
┌─────────────────────────────────────────────────────────────┐
│                    VM / Container Farm                       │
│                                                             │
│  Windows Pool (Azure/AWS)                                   │
│  ├── Windows 11 VMs × N                                     │
│  ├── 预装常用应用：Office, VS Code, Chrome, Edge,            │
│  │   File Explorer, Settings, Paint, Calculator, ...        │
│  └── UI Automation: pywinauto + Windows UIA API             │
│                                                             │
│  macOS Pool (AWS Mac/Orka)                                  │
│  ├── macOS VMs × N                                          │
│  ├── 预装：Safari, Finder, Terminal, Xcode,                  │
│  │   Pages, Numbers, Keynote, Preview, ...                  │
│  └── UI Automation: macapptree + AppleScript + AX API       │
│                                                             │
│  Linux Pool (普通云 VM)                                      │
│  ├── Ubuntu 22.04/24.04 VMs × N (GNOME Desktop)            │
│  ├── 预装：Firefox, Files, Terminal, LibreOffice,            │
│  │   VS Code, GIMP, Thunderbird, ...                        │
│  └── UI Automation: AT-SPI / pyatspi2 + xdotool             │
│                                                             │
│  共享基础设施                                                │
│  ├── 截图服务 (1080p 标准化)                                 │
│  ├── A11y Tree 提取服务                                     │
│  ├── 动作录制 / 回放引擎                                     │
│  └── 状态快照 / 恢复 (VM Snapshot)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**各平台 A11y Tree 提取工具链**：

| 平台 | 工具 | 提取内容 |
|------|------|---------|
| Windows | `pywinauto` + Windows UIA API + Accessibility Insights | 元素角色、名称、边界框、状态、控件模式 |
| macOS | `macapptree` + AX API + `Screen2AX` | 元素层级、角色、标题、边界框、动作列表 |
| Linux | `pyatspi2` + AT-SPI + `Accerciser` | 元素角色、名称、边界框、状态、文本内容 |

### 2.4 模块二：数据采集策略（4 条并行管线）

#### 管线 A：逆向任务合成（参考 OS-Genesis）

这是最适合"API 充足 + 人工少"场景的方法。

```
步骤：
1. 自动探索：Agent 在 VM 中自由探索 GUI（随机/启发式点击+导航）
2. 状态捕获：每一步记录 (screenshot_before, a11y_tree_before, action, screenshot_after, a11y_tree_after)
3. 逆向生成任务：将 (state_before, action, state_after) 三元组发给大模型 API
   Prompt: "Given the before/after screenshots and the action taken,
            generate a natural language task instruction that a user might
            give to achieve this state change."
4. 轨迹拼接：将连续的单步合成为多步轨迹
5. 质量评估：用另一个大模型 API 评分轨迹质量（0-5分），过滤低分数据

优势：无需预定义任务列表，天然多样化
预期产出：每个 VM 每天可产出 ~1000-5000 步有效动作
```

#### 管线 B：教程驱动合成（参考 AgentTrek）

```
步骤：
1. 教程爬取：从互联网爬取桌面软件教程（wikiHow, 官方文档, YouTube 字幕等）
   - Windows: Microsoft Learn, How-To Geek, etc.
   - macOS: Apple Support, 9to5Mac, etc.
   - Linux: ArchWiki, Ubuntu Help, Ask Ubuntu, etc.
2. 教程结构化：用大模型 API 将教程文本转为结构化步骤
   Input:  "How to create a pivot table in LibreOffice Calc: First, select..."
   Output: [{"step": 1, "instruction": "Select data range A1:D50", "app": "LibreOffice Calc"}, ...]
3. 引导回放：VLM Agent 在真实 VM 中按教程步骤操作，录制轨迹
4. 验证：用 VLM 评估回放结果是否与教程预期一致

优势：教程覆盖真实用户需求，任务自然且实用
预期产出：取决于教程数量，可爬取数万篇教程
```

#### 管线 C：任务模板批量生成

```
步骤：
1. 定义应用-功能矩阵：
   ┌─────────────────┬─────────────────────────────────────────────┐
   │ 应用             │ 功能                                       │
   ├─────────────────┼─────────────────────────────────────────────┤
   │ 文件管理器       │ 创建/删除/移动/重命名/搜索/压缩/权限设置      │
   │ 文本编辑器       │ 打开/编辑/查找替换/格式化/保存                │
   │ 浏览器           │ 导航/搜索/书签/下载/设置/多标签               │
   │ 终端             │ 命令执行/目录导航/文件操作/包管理              │
   │ Office 套件      │ 文档编排/表格计算/演示制作/公式/图表          │
   │ IDE              │ 代码编辑/调试/版本控制/重构/搜索              │
   │ 设置面板         │ 系统设置/网络/显示/声音/用户/安全             │
   │ 图像编辑器       │ 裁剪/滤镜/图层/文字/导出                     │
   └─────────────────┴─────────────────────────────────────────────┘

2. 用大模型 API 按每个 (应用, 功能) 对批量生成 N 个变体任务
   Prompt: "Generate 20 diverse, realistic user tasks for [File Manager]
            involving [rename files]. Vary complexity from simple to multi-step."

3. Agent 在 VM 中执行任务，录制轨迹
4. 自动验证任务完成状态

优势：可控性强，覆盖系统化
预期产出：~50 应用 × 10 功能 × 20 变体 = 10,000 基础任务
```

#### 管线 D：人机协作标注（用于高价值数据）

```
步骤：
1. 人工外包团队执行复杂的多步骤真实任务
2. 录屏 + 动作记录工具自动捕获操作序列
3. 大模型 API 自动生成 thought/reasoning 标注
4. 人工审核关键节点的标注质量

用途：补充 Stage 4 端到端微调所需的高质量轨迹
目标量：~10K 条高质量完整轨迹（每条 10-30 步）
```

### 2.5 模块三：质量控制系统

```
┌─────────────────────────────────────────────────────────────┐
│                    三层质量控制                               │
│                                                             │
│  Layer 1: 自动规则过滤                                       │
│  ├── 截图模糊/黑屏/重复检测                                  │
│  ├── 动作有效性验证（坐标在屏幕范围内、元素存在）              │
│  ├── 轨迹连续性检查（前后截图状态变化合理）                    │
│  └── 过滤率预期：~30-40%                                    │
│                                                             │
│  Layer 2: 模型评估（Trajectory Reward Model）                │
│  ├── 用大模型 API 对轨迹打分（参考 OS-Genesis）              │
│  │   评分维度：                                              │
│  │   - 任务完成度 (0-5)                                     │
│  │   - 动作效率 (0-5)                                       │
│  │   - 推理质量 (0-5)                                       │
│  │   - 指令-轨迹一致性 (0-5)                                │
│  ├── 保留得分 ≥ 3.5 的数据                                  │
│  └── 保留率预期：~50-60%                                    │
│                                                             │
│  Layer 3: 人工抽样审核                                       │
│  ├── 按 OS / 应用 / 任务类型 分层抽样 5%                     │
│  ├── 标注质量标签（通过/修正/拒绝）                           │
│  ├── 反馈到 Layer 1&2 的规则和 prompt 迭代                   │
│  └── 目标：抽检通过率 ≥ 90%                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.6 模块四：统一数据格式

所有数据（开源 + 自建）统一为以下格式：

```json
{
  "task_id": "uuid",
  "source": "os-genesis | agenttrek | template | human | opensource:gui360",
  "platform": "windows | macos | linux",
  "app_category": "office | browser | ide | file_manager | terminal | settings | ...",
  "app_name": "LibreOffice Writer",
  "task_instruction": "在文档中创建一个3行4列的表格并设置表头",
  "difficulty": "easy | medium | hard | expert",
  "trajectory": [
    {
      "step": 1,
      "thought": "首先需要点击菜单栏的'表格'选项",
      "screenshot_before": "path/to/screenshot_001.png",
      "screenshot_after": "path/to/screenshot_002.png",
      "a11y_tree_before": { ... },
      "a11y_tree_after": { ... },
      "action": {
        "action_type": "click",
        "coordinate": [320, 28],
        "element_id": "menu_table",
        "element_role": "MenuItem",
        "element_name": "Table"
      }
    },
    {
      "step": 2,
      "thought": "在下拉菜单中选择'插入表格'",
      "screenshot_before": "path/to/screenshot_002.png",
      "screenshot_after": "path/to/screenshot_003.png",
      "a11y_tree_before": { ... },
      "a11y_tree_after": { ... },
      "action": {
        "action_type": "click",
        "coordinate": [350, 95],
        "element_id": "menu_item_insert_table",
        "element_role": "MenuItem",
        "element_name": "Insert Table..."
      }
    }
  ],
  "metadata": {
    "resolution": "1920x1080",
    "os_version": "Ubuntu 22.04",
    "language": "en",
    "total_steps": 8,
    "success": true,
    "quality_score": 4.2,
    "collection_timestamp": "2026-03-01T10:30:00Z"
  }
}
```

---

## 第三部分：多阶段训练方案

### 3.1 训练阶段总览

```
                    训练阶段流水线
                    
时间 ──────────────────────────────────────────────────▶

Phase 0          Phase 1          Phase 2          Phase 3          Phase 4
Qwen Base ──▶  UI Pre-train ──▶  Grounding  ──▶  Trajectory  ──▶  Agent SFT
(frozen)        (大规模)          (中规模)         (中规模)         (精调)

数据量:         ~20M samples      ~10M samples     ~5M steps        ~1M trajectories
学习率:         较高              中等             中等             较低
训练方式:       全参数/LoRA        全参数           全参数           全参数+DPO/GRPO
```

### 3.2 Phase 0: 基座准备

基于 Qwen2.5-VL 系列（已支持动态分辨率 + M-ROPE），选择合适的模型尺寸：

| 模型尺寸 | 用途 | 训练策略 |
|---------|------|---------|
| 2B | 端侧/嵌入式部署，快速推理 | 全参数训练，知识蒸馏 from 大模型 |
| 7B | 性价比最优，日常部署 | 全参数训练 |
| 32B (72B) | 高性能需求场景 | 全参数/LoRA + DeepSpeed ZeRO-3 |
| 300B (MoE) | 旗舰模型，对标 SOTA | 全参数 + 3D并行 + Expert并行 |

### 3.3 Phase 1: UI 视觉感知预训练

**目标**：让模型具备 UI 截图的基础理解能力。

```
数据混合配比:
  OS-ATLAS (桌面部分)     40%    ~8M samples
  GroundCUA               15%    ~3M samples
  Jedi (合成)             15%    ~3M samples
  Rico (mobile迁移)       10%    ~2M samples
  GUICourse (OCR)          5%    ~1M samples
  自建 A11y 标注数据      15%    ~3M samples
  ─────────────────────────────────────
  总计                    100%   ~20M samples

训练任务（Multi-task）:
  - UI Element Detection (30%): 识别截图中所有可交互元素
  - OCR (20%): 识别截图中所有文字及位置
  - Layout Description (15%): 生成界面布局的结构化描述
  - Element Counting (10%): 统计特定类型元素的数量
  - Screen Summary (15%): 生成截图内容的自然语言摘要
  - A11y Tree Prediction (10%): 从截图预测 Accessibility Tree 结构

平台分布:
  Windows   40%
  macOS     30%
  Linux     30%

超参数建议 (7B):
  Learning Rate:  2e-5 (cosine decay)
  Batch Size:     256 (global)
  Epochs:         2-3
  Image Resolution: 1080p (动态分辨率)
  Warmup:         5%
```

### 3.4 Phase 2: GUI Grounding 训练

**目标**：给定指令，精准定位到 UI 元素。

```
数据混合配比:
  OS-ATLAS 桌面 grounding   35%    ~3.5M
  GroundCUA                  25%    ~2.5M
  Jedi (合成增强)            20%    ~2M
  自建 grounding 数据        20%    ~2M
  ─────────────────────────────────────
  总计                      100%   ~10M samples

训练任务:
  - Point Grounding (40%): 指令 → 点击坐标
  - Box Grounding (30%): 指令 → 元素边界框
  - Referring Expression (20%): 指令 → 元素描述 + 坐标
  - Multi-modal Grounding (10%): 截图 + a11y tree → 坐标

关键技巧:
  - 坐标归一化到 [0, 1000] 范围（不同分辨率统一）
  - 训练数据中混入"无匹配元素"的负样本（~10%），防止模型总是强行输出坐标
  - 使用 grounding-specific loss (L1 loss on coordinates + CE loss on text)
```

### 3.5 Phase 3: 动作预测 & 轨迹训练

**目标**：理解上下文，预测正确的下一步操作。

```
数据混合配比:
  GUI-360° (Windows 桌面)    30%    ~1.5M steps
  ScaleCUA (跨平台)          25%    ~1.25M steps
  自建轨迹数据               25%    ~1.25M steps
  OmniACT (代码级动作)       10%    ~0.5M steps
  Mind2Web + GUIAct (Web)     10%    ~0.5M steps
  ─────────────────────────────────────
  总计                       100%   ~5M steps

训练任务:
  - Next Action Prediction (40%):
    给定 [截图, 任务, 历史] → 预测下一步 action
  - Action + Thought Prediction (30%):
    给定 [截图, 任务, 历史] → 预测 thought + action
  - Multi-step Planning (20%):
    给定 [截图, 任务] → 预测接下来 3-5 步的计划
  - Code Generation (10%):
    给定 [截图, 任务] → 生成 PyAutoGUI 代码

动作空间统一编码:
  所有动作类型编码到统一的 action schema:
  {
    "thought": str,
    "action_type": "click|double_click|right_click|type|hotkey|scroll|drag|api_call|code|done|wait",
    "coordinate": [x, y] | null,         // 像素级
    "element_id": str | null,             // 元素级
    "text": str | null,                   // 输入文本
    "keys": [str] | null,                 // 快捷键
    "code": str | null,                   // PyAutoGUI 代码
    "api": str | null                     // API 调用
  }
```

### 3.6 Phase 4: 端到端 Agent 微调

**目标**：完整的指令跟随 + 多步推理 + 自纠正。

```
数据:
  自建高质量完整轨迹           50%    ~500K trajectories
  GUI-360° (含 reasoning)      20%    ~200K trajectories
  NatureGAIA (自纠正)          10%    ~100K trajectories
  合成 DPO/GRPO 偏好对         20%    ~200K pairs
  ─────────────────────────────────────
  总计                         100%   ~1M samples

训练方法 (分两步):
  Step 1: SFT on successful trajectories
    - 完整轨迹的序列建模
    - 含 thought chain 的推理过程

  Step 2: RLHF / DPO / GRPO alignment
    - 对比成功 vs 失败轨迹
    - 对比高效 vs 冗余轨迹
    - 训练自纠正能力（识别错误 → 回退 → 重试）

偏好对构造方法:
  - 同一任务的成功 vs 失败轨迹（来自 GUI-360° 的 success/fail 对）
  - 同一任务的短轨迹 vs 长轨迹（效率偏好）
  - 模型自生成 + 人工评分
```

---

## 第四部分：不同模型尺寸的差异化策略

### 4.1 2B 小模型策略

```
定位：端侧部署、低延迟推理、基础 GUI 操作
重点能力：GUI Grounding + 单步动作预测
训练策略：
  - Phase 1-2 全量训练
  - Phase 3 用精简版轨迹数据（单步为主）
  - Phase 4 大幅精简，聚焦高频简单任务
  - 知识蒸馏：用 72B 模型的输出作为 soft target
数据量：Phase1 ~5M + Phase2 ~3M + Phase3 ~1M + Phase4 ~100K
```

### 4.2 7B 中等模型策略

```
定位：标准部署、性价比最优
重点能力：全链路（感知 → grounding → 动作 → 端到端）
训练策略：
  - 四阶段完整训练
  - 使用全量数据
数据量：Phase1 ~20M + Phase2 ~10M + Phase3 ~5M + Phase4 ~1M
```

### 4.3 72B 大模型策略

```
定位：高性能服务端部署
重点能力：复杂多步任务 + 跨应用工作流 + 强推理
训练策略：
  - Phase 1-2 可能用 LoRA 降低成本
  - Phase 3-4 全参数（复杂推理需要充分训练）
  - 额外加入更多 multi-app 跨应用工作流数据
  - 强化长 horizon 推理和规划
数据量：同 7B，但增加复杂任务比例至 40%
```

### 4.4 300B MoE 旗舰模型策略

```
定位：旗舰模型、对标 Claude Computer Use / GPT-4o 级别
重点能力：全能力 + 开放域泛化 + 自主规划
训练策略：
  - 四阶段全量训练 + 3D并行 + Expert并行
  - 大量混入通用 VLM 数据防止灾难性遗忘
  - Phase 4 重点强化：
    - 开放域任务理解
    - 多轮交互
    - 失败恢复和自纠正
    - 跨 OS 泛化
数据量：每阶段 2-3x 于 7B，且通用数据混合比例更高
```

---

## 第五部分：数据缺口分析 & 自建数据重点

### 5.1 现有开源数据覆盖缺口

```
                    数据覆盖热力图

              Win    macOS   Linux   Web    Mobile
感知/OCR      ██████ ████    ███     █████  ████████
Grounding     ██████ ████    ███     █████  ████████
动作轨迹      ██████ ██      █       █████  ████████
端到端任务    ████   █       █       ████   ██████
A11y Tree     ███    ██      █       ████   ██████
代码级动作    ███    █       █       ██     █

██████ = 充足    ████ = 中等    ██ = 稀缺    █ = 极度稀缺

核心缺口：
1. macOS 和 Linux 桌面场景的轨迹数据极度稀缺
2. 代码级动作（PyAutoGUI/AppleScript/xdotool）数据极少
3. 跨应用多步工作流数据不足
4. A11y Tree 标注的桌面数据较少
5. 失败/自纠正轨迹数据稀缺
```

### 5.2 自建数据优先级

| 优先级 | 数据类型 | 目标量 | 采集方式 |
|--------|---------|--------|---------|
| P0 | macOS 桌面轨迹 | 500K steps | OS-Genesis 逆向合成 + 教程驱动 |
| P0 | Linux 桌面轨迹 | 500K steps | OS-Genesis 逆向合成 + 教程驱动 |
| P0 | 跨平台 A11y Tree + 截图对 | 2M pairs | 自动化 A11y 提取 |
| P1 | 代码级动作数据 | 200K | 模板生成 + 大模型 API 扩写 |
| P1 | 跨应用工作流 | 100K trajectories | 人工设计任务 + Agent 执行 |
| P1 | Windows 补充轨迹 | 500K steps | OS-Genesis 逆向合成 |
| P2 | 失败 + 自纠正轨迹 | 200K | Agent 执行 + 自动收集失败 case |
| P2 | 多语言 UI 数据 | 500K | 切换系统语言后采集 |

### 5.3 预估数据采集时间线

```
Month 1-2: 基础设施搭建
  - VM 集群部署（Windows/macOS/Linux 各 20+ 台）
  - A11y 提取工具链调通
  - 截图 + 动作录制管线就绪
  - 统一数据格式 + 存储管线

Month 2-4: 大规模自动采集 (P0)
  - OS-Genesis 逆向合成管线上线
  - 教程爬取 + 结构化管线上线
  - 预期产出：~2M+ steps / month（跨 3 OS）
  - 同步进行质量控制迭代

Month 4-5: 补充数据 (P1)
  - 代码级动作数据生成
  - 跨应用工作流数据
  - 补充 Windows 轨迹

Month 5-6: 高质量数据 (P2) + 训练准备
  - 失败/自纠正轨迹
  - 多语言数据
  - 数据清洗、去重、质量终审
  - 开始 Phase 1 训练
```

---

## 第六部分：评测体系

### 6.1 各阶段评测指标

| 阶段 | 评测基准 | 核心指标 |
|------|---------|---------|
| Phase 1 | 自建 UI 理解测试集 | Element F1, OCR Accuracy, Layout Acc |
| Phase 2 | ScreenSpot, ScreenSpot-Pro | Grounding Accuracy (text/icon/widget) |
| Phase 3 | 自建动作预测测试集 | Action Type Acc, Coordinate L1 Error, Step Success Rate |
| Phase 4 | OSWorld, WAA, AssistGUI | Task Success Rate, Step Efficiency, Avg Steps |
| 综合 | MMBench-GUI, UI-Vision | 各层级综合得分 |

### 6.2 内部持续评测

```
每个 checkpoint 自动运行:
  - ScreenSpot-Pro (grounding, ~1.5h)
  - OSWorld subset (50 tasks, ~4h)
  - 自建 smoke test (100 tasks × 3 OS, ~2h)

每个阶段结束运行:
  - 全量 OSWorld (369 tasks)
  - Windows Agent Arena (154 tasks)
  - AssistGUI (100 tasks)
  - MMBench-GUI (全层级)
```

---

## 附录：关键开源工具和资源

| 工具/资源 | 用途 | Link |
|----------|------|------|
| OS-Genesis | 逆向任务合成管线 | https://github.com/os-copilot/os-genesis |
| AgentTrek | 教程驱动轨迹合成 | https://github.com/xlang-ai/AgentTrek |
| pywinauto | Windows UI 自动化 | https://github.com/pywinauto/pywinauto |
| macapptree | macOS A11y Tree 提取 | https://github.com/MacPaw/macapptree |
| Screen2AX | macOS 截图 → A11y | https://github.com/MacPaw/Screen2AX |
| pyatspi2 | Linux AT-SPI 接口 | https://github.com/GNOME/pyatspi2 |
| Accessibility Insights | Windows A11y 检查 | https://accessibilityinsights.io/ |
| OSWorld | 跨 OS 评测环境 | https://github.com/xlang-ai/OSWorld |
