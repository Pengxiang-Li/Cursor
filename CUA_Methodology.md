# CUA 基座模型方法论

> 基于 Mobile-Agent-v3.5、Mano、EvoCUA、UI-TARS-2、AgentCPM、Computer-RL (AutoGLM-OS) 等前沿工作的系统性综合分析
> 最终目标：服务于全平台 Desktop GUI 基座模型的构建

---

## 一、目标：我们到底要做什么

### 1.1 终局画像

构建一个 **全平台 (Win/macOS/Linux) 桌面 GUI 基座模型**，使其能够：
- 看懂任意桌面截图中的 UI 元素（感知）
- 精准定位到指令所指元素（Grounding）
- 在给定任务目标下规划多步操作序列（规划）
- 在真实桌面环境中通过键鼠/代码/API 完成复杂任务（执行）
- 在失败时自主识别错误并纠正（自纠正）

### 1.2 从相关工作中提炼的核心认知

**认知一：数据飞轮是核心竞争力，不是模型架构**

UI-TARS-2 把"数据飞轮"作为核心——模型既是学习者也是数据生产者。EvoCUA 用 5000 条 query + verifier 做了多轮 RFT 到 51 分，说明在数据规模受限时，**迭代质量远比一次性堆量重要**。Computer-RL 仅 180K 步就 cold-start 到能跑 RL 的水平。结论：数据管线（采集 → 过滤 → 训练 → 回收 → 再训练）的闭环效率才是壁垒。

**认知二：RL 是从"能用"到"好用"的关键跃迁，但 RL 的基础设施成本极高**

所有 SOTA 方案（UI-TARS-2、Computer-RL、EvoCUA、Mano、Mobile-Agent-v3.5）都在 SFT 之后做了 RL。Computer-RL 的 Entropulse（RL→SFT restore entropy→RL）表明 RL 训练本身不稳定，需要精细工程。EvoCUA 用 2000-4000 并行环境。这意味着：**没有大规模沙盒环境 + 可编程 Verifier，RL 就无法有效 scale**。

**认知三：统一动作空间是尚未被充分解决的核心问题**

Mobile-Agent-v3.5 在 CoT level 做了些尝试，但 mobile/web/desktop 的 action space 仍然割裂。Computer-RL 的 API-GUI Paradigm（输出 Python 代码统一 GUI primitive 和 application-specific API）是目前最优雅的方案。对于全平台基座模型，**统一且可扩展的动作空间设计是架构层面最重要的决策**。

**认知四：Grounding 是地基，地基不牢，一切白搭**

从 AgentCPM 的 12M grounding 预训练样本，到 Mobile-Agent-v3.5 的 hard grounding synthesis + infeasible 负样本，所有工作都在 grounding 上投入大量精力。ScreenSpot-Pro 上最好的模型也只有 18.9%。**桌面端因为元素更小更密（工具栏、属性面板等），grounding 的难度远高于 mobile**。

**认知五：Verifier/Reward 的质量决定 RL 的上限**

Computer-RL 的 8000 个任务全部配备了可编程 Verifier。UI-TARS-2 用 JS 脚本验证游戏状态、LLM-as-Judge 验证浏览任务、自训练 Generative ORM 验证开放任务。EvoCUA 强调 verifier 全部模型生成。核心问题：**桌面环境的 Verifier 如何构建？** 这比 Web/Mobile 困难得多。

### 1.3 我们的战略选择

```
Phase 1 (0-3月): 地基——Grounding + 感知能力
  用开源数据 + 自建 A11y 数据快速建立视觉感知基础
  目标：ScreenSpot-Pro 达到 top-3 水平

Phase 2 (2-5月): 冷启动——SFT on 轨迹数据
  开源轨迹 + 自动化采集 + 少量人工
  目标：OSWorld 基础可用（>15% SR）

Phase 3 (4-8月): 飞轮——RL + 数据回收迭代
  大规模沙盒 + Verifier + Online RL
  目标：OSWorld >30% SR

Phase 4 (6-10月): Scale——多尺寸模型 + 跨平台泛化
  2B→300B 全系列 + 知识蒸馏 + 参数插值
```

---

## 二、环境基础设施

### 2.1 核心需求分析

从相关工作看环境需求：

| 工作 | 环境规模 | 环境类型 |
|------|---------|---------|
| Computer-RL | 数千并发 VM | 分布式虚拟桌面 |
| EvoCUA | 2000-4000 并发环境 | 沙盒 |
| UI-TARS-2 | 大规模（未披露） | 真实 PC + 游戏 + 浏览器 |
| Mobile-Agent-v3.5 | 真实设备 + 虚拟环境 | 真机 + Web 渲染虚拟环境 |
| Mano | DFS 探索用环境 | 真实 + Chrome 插件 |

**关键结论**：SFT 阶段对环境要求低（几十台即可），但 Online RL 阶段需要**千级并发**环境来保证 Sample Efficiency。

### 2.2 分层环境架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    环境基础设施分层架构                           │
│                                                                 │
│  Layer 1: 轻量采集环境 (数据采集阶段, ~50-100 台)                │
│  ├── Windows 11 VM × 30 (Azure/AWS)                            │
│  ├── macOS VM × 10 (AWS Mac / Orka)                            │
│  ├── Linux (Ubuntu 24.04 GNOME) VM × 10                        │
│  ├── 用途：OS-Genesis 逆向探索、教程回放、人工录制               │
│  └── 工具链：截图 + A11y 提取 + 动作录制/回放                   │
│                                                                 │
│  Layer 2: 虚拟沙盒环境 (RL 阶段, ~2000-4000 并发)               │
│  ├── Docker/VM 快照池（预配置应用 + 任务初始状态）               │
│  ├── 快速重置能力：任务失败后 <10s 恢复到初始状态                │
│  ├── Verifier 执行框架（每个任务绑定验证脚本）                   │
│  ├── 分布式环境管理器（参考 Computer-RL 架构）                   │
│  └── 资源估算：RL 阶段 ~500-1000 GPU + 2000+ VM               │
│                                                                 │
│  Layer 3: 虚拟渲染环境 (参考 Mobile-Agent-v3.5)                 │
│  ├── Web 渲染的虚拟桌面应用（文档编辑器、表格等）                │
│  ├── 优势：状态完全可控、无验证码干扰、可精确验证                │
│  ├── 适用：Office 类任务、表单填写、设置类任务                   │
│  └── 构建成本低，Verifier 天然精确                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 跨平台 A11y 提取工具链

| 平台 | 核心工具 | 提取内容 | 成熟度 |
|------|---------|---------|--------|
| Windows | `pywinauto` + UIA API | 角色、名称、边界框、状态、控件模式 | 高 |
| macOS | `macapptree` + AX API + `Screen2AX` | 层级、角色、标题、边界框、动作 | 中 |
| Linux | `pyatspi2` + AT-SPI + `Accerciser` | 角色、名称、边界框、状态、文本 | 中低 |

**实际建议**：
- Mano 的经验表明 A11y Tree + OmniParse 的混合方法最稳健
- Computer-RL 的经验表明**纯视觉（不依赖 A11y Tree）也可行**——他们移除了 A11y 以减少 Token 消耗
- 我们的策略：**训练时混合有/无 A11y 的数据，推理时按需选择**——有 A11y 用 A11y（更准），没有就纯视觉（更通用）

### 2.4 Verifier 体系设计

这是 RL 阶段的核心基建。参考各家方案后的分层设计：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Verifier 分层体系                             │
│                                                                 │
│  Tier 1: Rule-based Verifier (最精确，适用范围窄)                │
│  ├── 文件系统类：检查目标文件是否存在/内容是否匹配               │
│  ├── 应用状态类：检查应用窗口状态（标题、大小、位置）            │
│  ├── 文档类：解析文档内容验证（表格行列数、文字格式等）          │
│  ├── 设置类：读取系统/应用配置验证                               │
│  ├── 参考: Computer-RL 的 ~8000 个可编程 Verifier               │
│  └── 覆盖率目标：核心任务 100%                                  │
│                                                                 │
│  Tier 2: Screenshot-diff Verifier (中等精度)                    │
│  ├── 比对任务完成前后的截图关键区域                              │
│  ├── 结合 OCR 验证特定文字是否出现/消失                         │
│  ├── 适用：UI 状态变化明显的任务                                │
│  └── 覆盖率目标：补充 Tier 1 不覆盖的场景                      │
│                                                                 │
│  Tier 3: LLM-as-Judge (最灵活，精度依赖 prompt 质量)            │
│  ├── 参考 UI-TARS-2: LLM-as-Judge 匹配 Ground-truth            │
│  ├── 输入：任务指令 + 初始截图 + 最终截图 + 操作历史            │
│  ├── 输出：成功/失败 + 评分(0-5) + 理由                        │
│  ├── 适用：开放式任务、创意性任务                                │
│  └── 注意：EvoCUA 声称 verifier 全部模型生成无人工参与           │
│                                                                 │
│  Tier 4: Generative ORM (参考 UI-TARS-2)                       │
│  ├── 训练专门的 Outcome Reward Model                            │
│  ├── 输入：历史文本 + 最近 5 帧截图                             │
│  ├── 输出：标量评分                                             │
│  ├── 适用：最泛化的场景，用于 RL reward                         │
│  └── 需要在 RL 进行到一定阶段后才可靠                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Verifier 构建的优先级**：

先为 **桌面高频应用** 构建 Rule-based Verifier：

| 应用类型 | 代表应用 | Verifier 思路 | 难度 |
|---------|---------|--------------|------|
| 文件管理 | Explorer/Finder/Files | 检查文件系统状态 | 低 |
| 文本编辑 | Notepad/TextEdit/gedit | 读取文件内容 | 低 |
| 终端 | CMD/Terminal/Bash | 检查命令输出/文件变化 | 低 |
| 浏览器 | Chrome/Edge/Firefox | URL + DOM 状态 | 中 |
| Office | Word/Excel/PPT/LibreOffice | 解析文档结构 (参考 Computer-RL: SpreadsheetBench, PPTC) | 中 |
| 设置 | Settings | 读取注册表/plist/gsettings | 中 |
| IDE | VS Code | Extension API / 工作区状态 | 中高 |
| 图像编辑 | Paint/GIMP | 像素级比对 | 高 |

---

## 三、训练数据 Scaling

### 3.1 数据飞轮模型

综合 UI-TARS-2 的 Data Flywheel、Computer-RL 的 Entropulse 数据回收、Mano 的闭环数据循环：

```
                         数据飞轮 (Data Flywheel)
                         
         ┌──────────────────────────────────────────┐
         │                                          │
         ▼                                          │
    ┌─────────┐     ┌──────────┐     ┌──────────┐  │
    │ 数据采集  │────▶│ 模型训练  │────▶│ 模型部署  │  │
    │          │     │ (SFT/RL) │     │ (Rollout) │  │
    └─────────┘     └──────────┘     └──────────┘  │
         ▲                                │         │
         │                                ▼         │
    ┌─────────┐     ┌──────────┐     ┌──────────┐  │
    │ 质量过滤  │◀────│ 数据回收  │◀────│ Verifier  │──┘
    │ & 路由   │     │          │     │ 验证      │
    └─────────┘     └──────────┘     └──────────┘
         │
         ├── 高质量成功轨迹 ──────▶ SFT 数据集
         ├── 低质量/失败轨迹 ──────▶ CT 数据集 (UI-TARS-2 做法)
         ├── 成功但中间有错 ──────▶ LLM 修正 → SFT (Mano 做法)
         └── 成功 Rollout ──────▶ Entropy 恢复 SFT (Computer-RL 做法)
```

### 3.2 各阶段数据规模参考

从相关工作提取的数据规模基线：

| 阶段 | AgentCPM | Computer-RL | EvoCUA | UI-TARS-2 | 我们的目标 |
|------|---------|-------------|--------|-----------|-----------|
| Grounding 预训练 | 12M (含50%通用) | - | - | 未披露 | **15-20M** |
| SFT 轨迹 | 55K轨迹/470K步 | 180K步 | 5K轨迹(冷启动) | 大规模(未披露) | **500K轨迹/5M步** |
| SFT 通用数据混合 | 50% | 0% | 50% | 少量 | **30-40%** |
| RL Query/Task 数 | - | ~8000 | ~3000-5000 | 未披露 | **10,000+** |
| RL 环境并发 | - | 数千 | 2000-4000 | 未披露 | **2000-4000** |

### 3.3 数据 Scaling 的关键洞察

**洞察一：冷启动数据量可以很少，但质量必须高**

Computer-RL 用 180K 步就完成了 cold-start BC。EvoCUA 用 5K 条轨迹冷启动。关键不在于量，而在于：
- 轨迹必须 **全部通过 Verifier 验证** (Computer-RL)
- 需要多个强模型作为 Teacher 并取最优 (Computer-RL 的 Model Pool)
- 按难度分层采集 (Computer-RL: Easy/Medium/Hard 分层策略)

**洞察二：每个 Query 多条轨迹比更多 Query 更有效**

EvoCUA 明确指出"一个 query 多个轨迹有效"。这与 RL 的探索多样性需求一致——同一任务的不同解法给模型提供了更好的 policy space 覆盖。

**洞察三：通用数据混合是防止 mode collapse 的必要手段**

AgentCPM 在 Grounding 阶段混合 50% 通用多模态数据，SFT 阶段也混合 50%。这不是为了效果——而是为了**防止模型遗忘通用视觉能力**。对于基于 Qwen-VL 微调的方案，这个比例很关键。

**洞察四：RL 数据的 Scaling 瓶颈在环境和 Verifier，不在 GPU**

EvoCUA 强调"最重视 Scaling，沙盒还有 Verifier"。这意味着数据 scaling 的真正瓶颈不是算力，而是：
1. 能并行运行多少个沙盒环境
2. 有多少任务配备了可靠的 Verifier
3. 环境重置速度（决定了采样效率）

---

## 四、开源数据使用策略

### 4.1 按训练阶段分配

#### Grounding 预训练阶段

| 数据集 | 数据量 | 用法 | 优先级 |
|--------|--------|------|--------|
| OS-ATLAS | 13M+ 元素 | 桌面部分直接用于 element grounding | P0 |
| GroundCUA | 3.56M 标注 | 直接用于 grounding 训练 | P0 |
| Jedi | 4M 合成 | 数据增强 | P1 |
| GUICourse | 多阶段 | 早期 OCR 训练 | P1 |
| Rico | 3M 元素 | Mobile → Desktop 迁移预训练 | P2 |
| 通用 VLM 数据 | ~50% 混入 | 防止视觉模块退化 (AgentCPM 策略) | P0 |

**参考 Mobile-Agent-v3.5 的增强策略**：
- Hard Grounding Synthesis：用 MLLM 渲染生成高难度专业软件截图，多窗口场景
- Infeasible 负样本：图像和 Query 随机组合 + 多模型共识过滤 → "该指令在此截图中不可行"
- 从探索轨迹中用 Critic 模型挖掘 grounding 数据（不浪费任何数据）

#### SFT 轨迹阶段

| 数据集 | 数据量 | 用法 | 优先级 |
|--------|--------|------|--------|
| GUI-360° | 1.2M 步 | Windows 桌面轨迹 (核心) | P0 |
| ScaleCUA | 大规模 | 跨平台轨迹 | P0 |
| OmniACT | 中等 | 代码级动作训练 (PyAutoGUI) | P1 |
| Mind2Web | 2K+ tasks | 浏览器操作 | P1 |
| GUIAct | 127K-1.26M | GUI 交互动作 | P1 |
| AITW | 715K ep | 交互模式迁移 | P2 |
| 通用对话/VQA | ~30-40% 混入 | 防止 mode collapse (AgentCPM 策略) | P0 |

**参考 Mano 的数据清洗和组织**：
- 需要对开源数据做格式统一（参考 Mano 洗 OpenCUA 的经验）
- EvoCUA 提到 OpenCUA 和 Qwen3VL 的 pattern 很不一样，需要工程对齐（如 RoPE）
- 保留前 2 帧历史截图 + 全部历史摘要 (Mano 实验证明最优)

#### RL Verifier 构建参考

| 来源 | 可复用部分 |
|------|-----------|
| Computer-RL | SpreadsheetBench, PPTC 的 verifier 设计思路 |
| OSWorld | 369 个任务的评估框架 |
| Windows Agent Arena | 154 个任务的评估逻辑 |
| AssistGUI | 100 个专业软件任务 |

### 4.2 开源数据的已知问题

| 问题 | 涉及数据集 | 解决方案 |
|------|-----------|---------|
| 平台偏向 | GUI-360° 仅 Windows | 自建 macOS/Linux 数据补齐 |
| 动作空间不统一 | 各数据集格式各异 | 定义统一 schema 做格式转换 |
| 质量参差 | AITW 冗余高 | 参考 AgentCPM 的 ResNet-50 去重 (保留约 40%) |
| Pattern 不兼容 | OpenCUA vs Qwen 的分布差异 | 格式对齐 + 混合比例调优 (EvoCUA 经验) |
| A11y 缺失 | 多数数据集仅有截图 | 能补就补，不能补就作为纯视觉样本 |

---

## 五、L0.5 — 感知与 Grounding 地基

### 5.1 定义

L0.5 是模型的"眼睛"——看懂界面、定位元素。这是所有上层能力的基础。

### 5.2 训练目标

```
L0.5 能力层级：

L0.5a - 基础视觉感知
  ├── OCR：识别截图中所有文字及位置
  ├── 元素检测：识别可交互元素 (button, menu, input, etc.)
  ├── 布局理解：理解界面结构 (toolbar, sidebar, main area, etc.)
  └── 截图描述：生成界面内容摘要

L0.5b - 精准 Grounding
  ├── Text Grounding：  "点击保存按钮" → 坐标
  ├── Icon Grounding：  "点击搜索图标" → 坐标
  ├── Desc Grounding：  "左上角第三个菜单项" → 坐标
  ├── Negative Sample：  "该界面中没有这个元素" → 拒答
  └── Multi-modal：     截图 + A11y Tree → 元素定位

L0.5c - 高难度 Grounding (参考 Mobile-Agent-v3.5)
  ├── 多窗口重叠场景：准确定位被遮挡/小尺寸元素
  ├── 专业软件 UI：CAD/视频编辑/IDE 等复杂工具栏
  ├── 高分辨率小元素：4K 屏下的微小按钮/图标
  └── 动态/模糊场景：加载中/半透明/disabled 状态
```

### 5.3 数据构造策略

**直接复用 Mobile-Agent-v3.5 的方法论**（非常契合我们"API 充足、人工少"的特点）：

```
策略 1: Hard Grounding Synthesis
  ├── 用 MLLM 结合真实 UI 元素和参考界面 → 渲染生成高难度截图
  ├── 将单窗口数据重组为多窗口场景 → 增加定位难度
  └── 产出：数十万级 hard grounding 样本

策略 2: 从探索轨迹挖掘
  ├── 在 OS-Genesis 逆向探索过程中，顺便提取 grounding 对
  ├── 用 Critic 模型清洗
  └── 产出：百万级（探索轨迹的副产品，几乎零额外成本）

策略 3: Infeasible 负样本生成
  ├── 随机组合 (截图, Query) → 大部分自然是 infeasible 的
  ├── 多模型共识过滤 → 确认确实 infeasible
  └── 产出：与正样本 ~1:10 混合

策略 4: A11y 自动标注
  ├── 在 VM 上遍历应用 → 自动截图 + 提取 A11y Tree
  ├── 从 A11y Tree 自动生成 grounding 指令
  └── 产出：百万级跨平台 grounding 对
```

### 5.4 训练配置

```
数据规模：15-20M 样本
混合比例：
  GUI Grounding 数据       50%
  通用多模态数据 (防退化)   30%    ← AgentCPM 经验：必须混入
  OCR 数据                 10%
  布局理解数据              10%

训练配置 (7B)：
  LR: 2e-5, cosine decay
  Epochs: 2-3
  Global BS: 256
  Image: 动态分辨率 (Qwen2-VL Native)
```

---

## 六、L1 — 任务分解与任务重组

### 6.1 定义

L1 是将自然语言指令分解为可执行步骤序列的能力，也是将简单原子任务重组为复杂工作流的能力。

### 6.2 任务分解层级

```
L1a - 原子任务理解
  输入: "点击文件菜单"
  输出: {"action": "click", "target": "File menu", "coordinate": [25, 12]}
  → 单步、无歧义

L1b - 简单多步任务分解
  输入: "保存文件为 PDF 格式"
  输出: [
    "点击 File 菜单",
    "选择 Export as PDF",
    "在对话框中确认设置",
    "点击 Save"
  ]
  → 线性步骤、一个应用内

L1c - 条件分支任务
  输入: "如果文件未保存则先保存，然后关闭应用"
  输出: 需要检查状态 → 根据条件选择路径
  → 包含状态判断和分支

L1d - 跨应用复杂工作流
  输入: "从邮件中提取附件的数据，整理到 Excel 表格中，然后将结果截图发到 Slack"
  输出: 跨 3+ 应用的协调操作序列
  → 多应用、信息流转、长序列
```

### 6.3 任务分解的训练数据构造

**参考 Mobile-Agent-v3.5 的 DAG 方法**（非常适合桌面端）：

```
方法 1: DAG 定义 + 自动化探索
  ├── 人工为每个应用构建 DAG (状态 → 转移 → 原子任务)
  │   例如 LibreOffice Writer:
  │   ├── State: 空白文档 → 有内容文档 → 有格式文档 → 有表格文档
  │   ├── Transition: 输入文字 / 设置格式 / 插入表格 / 保存
  │   └── Atomic Tasks: 每个 transition 是一个原子任务
  ├── Agent 按 DAG 路径执行
  ├── Checkpoint 验证：在 DAG 节点处验证状态是否正确
  ├── 失败处理：截断到最后一个正确 checkpoint → 动态重写指令
  └── 产出：大量有 checkpoint 验证的分步轨迹

方法 2: LLM 指令复杂化 (参考 UI-TARS-2)
  ├── Multi-Condition Obfuscation：给简单任务附加混淆条件
  │   "打开文件" → "打开那个昨天修改过的、名字里包含'report'的 Excel 文件"
  ├── Multi-Hop Chain-Like Conditions：多跳链式条件
  │   "找到上周五邮件中提到的那个客户的联系方式，复制到通讯录"
  └── 产出：复杂度可控的指令变体

方法 3: 任务重组 (简单 → 复杂)
  ├── 从 DAG 原子任务中随机拼接 3-8 步
  ├── 用 LLM 生成统一的自然语言描述
  ├── 加入跨应用组合
  └── 产出：多样化的复合任务
```

### 6.4 从相关工作提取的关键洞察

**Mano 的 Action Description 模块**（+2.8 性能提升）：

在 Thought 和 Action 之间加入一句话摘要，这实质上是在训练模型做**微观层面的任务分解**——把思考转化为一个明确的下一步意图描述，再执行。

```
Thought: "之前的选择没有准确抓取到标题中的数字'2'..."
Action Desp: "Move the mouse to the number '2' in the title 'H2O', click and hold..."
Action: drag(start_box=(689,500), end_box=(709,499))
```

**建议**：我们的输出格式也应采用 `Thought → Action Description → Action` 三段式。

**Mobile-Agent-v3.5 的统一 CoT 合成**：

对每一步标注 Observation（看到什么）→ Memory（记住什么）→ Reflection & Task Progress（反思 + 进度）→ Thought（思考）→ Conclusion（结论/动作）。

**建议**：完整 CoT 在 SFT 阶段使用，RL 阶段可精简为 `Thought → Action Desp → Action`。

---

## 七、训练方式

### 7.1 训练总流程

综合所有相关工作，最优训练范式为：

```
┌────────────────────────────────────────────────────────────────────┐
│                        训练总流程                                  │
│                                                                    │
│  Stage 0           Stage 1           Stage 2          Stage 3      │
│  CT (可选)    ──▶  SFT          ──▶  Online RL   ──▶  融合         │
│  持续预训练         监督微调           强化学习          参数插值     │
│                                                                    │
│  UI-TARS-2 做了    所有工作都做了     所有 SOTA 都做了  UI-TARS-2    │
│  AgentCPM 做了                                         EvoCUA      │
│                                                                    │
│                    ┌─ Entropulse ─┐                                │
│                    │ SFT恢复熵    │   ← Computer-RL 独创           │
│                    └──────────────┘                                │
│                                                                    │
│  RL 内部可能有多轮迭代 (RL → SFT恢复 → RL → ...)                  │
│  成功数据回收到 SFT 集合形成飞轮                                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 7.2 SFT 阶段详解

#### 数据配比

综合各家经验：

| 来源 | Mano 配比 | AgentCPM 配比 | 建议配比 |
|------|----------|--------------|---------|
| 自动采集轨迹 | 70% | - | 50% |
| 开源数据 (清洗) | 10% | 多个开源集 | 15% |
| 人工标注 | 20% | 真机录制 | 10% |
| 通用对话/VQA | 0% | 50%(!) | 25% |

**关键经验**：
- AgentCPM 混入 50% 通用数据，是因为 MiniCPM 的基础能力弱，需要大量正则化
- 对于 Qwen-VL 基座（本身就很强），通用数据混合可以降到 25-30%
- Mano 的 70% 自动采集占比说明自动化管线是 SFT 数据的主力

#### SFT 输出格式设计

综合 Mano（三段式）、Mobile-Agent-v3.5（五段式 CoT）、Computer-RL（Thought + Code）：

```
推荐格式（兼顾推理质量和推理效率）:

<think>
[Observation] 当前界面是 LibreOffice Writer，显示一篇空白文档。
[Memory] 用户要求创建一个包含标题和表格的会议纪要。
[Progress] 第 1 步/预计 6 步：需要先输入标题。
[Thought] 我应该先输入会议纪要的标题文字。
</think>

<summary>
Type the title "会议纪要" at the current cursor position.
</summary>

<action>
type(text="会议纪要")
</action>
```

**对于 2B 小模型**，可以精简为 `<think>..short..</think><action>...</action>`。

#### SFT 的关键训练技巧

**1. In-policy 标注（来自 UI-TARS-2）**

```
核心思想：SFT 数据应该尽量 on-policy
├── 传统方式：人工从头标注全部轨迹 → off-policy
├── In-policy 方式：模型 rollout → 人工选择 accept/override → on-policy
└── 效果：训练-推理分布一致，减少 compounding error
```

建议：先用开源数据 + 自动化数据做第一轮 SFT，然后用训练出的模型做 rollout，人工只需 accept/override，效率远高于从头标注。

**2. 历史帧策略（来自 Mano）**

```
实验结论：保留前 2 帧历史截图 + 全部历史文本摘要 = 最优
├── 0 帧：模型缺少上下文，频繁重复操作
├── 2 帧：最佳平衡点
├── 5+ 帧：显存爆炸，收益递减
└── 历史文本摘要比历史截图更 token-efficient
```

**3. CoT Warm-up（来自 AgentCPM）**

AgentCPM 发现 MiniCPM 不做 warm-up 甚至无法输出 thought 格式。对于 Qwen-VL 可能不需要这么极端，但建议：
- SFT 早期混入少量（~5%）纯 CoT 推理数据（不含 action，只练推理格式）
- 逐步增加带 action 的轨迹数据比例

### 7.3 关键步骤训练

#### "关键步骤"概念

EvoCUA 的冷启动数据配比：50% 通用 + 35% 普通步骤 + **15% 关键步骤**。

什么是关键步骤？

```
关键步骤 = 对任务成败有决定性影响的步骤

例如：任务 "在 Excel 中创建数据透视表"
├── 普通步骤：打开 Excel、选择数据区域 → 错了可以容易恢复
├── 关键步骤：正确点击"插入数据透视表" → 这一步不对，后面全错
└── 关键步骤：选择正确的字段拖到行/列 → 直接决定结果

又如：任务完成的最后一步（确认/保存/提交）
├── 如果最后一步错了 → 整个任务白做
└── 所以最后一步也是关键步骤
```

#### 关键步骤的识别方法

```
方法 1: 基于 Verifier 的回溯分析
  ├── 对于失败轨迹，找到第一个偏离正确路径的步骤
  └── 这个步骤就是关键步骤

方法 2: 基于状态变化的分析
  ├── 计算每一步 screenshot_before 和 screenshot_after 的差异
  ├── 差异大的步骤 = 状态转变关键节点
  └── 如：打开新对话框、切换应用、提交表单

方法 3: 基于 DAG 的结构分析 (Mobile-Agent-v3.5)
  ├── DAG 中 in-degree > 1 或 out-degree > 1 的节点
  └── 这些是分支/汇合点 = 关键决策步骤

方法 4: 最后一步总是关键步骤
  └── 任务的 final action (done/submit/save) 应该加权
```

#### 关键步骤的训练策略

```
SFT 阶段：
  └── 关键步骤数据 upsampling 到 15-20% (参考 EvoCUA)

RL 阶段（参考 EvoCUA）：
  └── Offline DPO 专门对关键步骤进行学习
      ├── 正样本：关键步骤正确执行
      ├── 负样本：关键步骤执行错误
      └── 这比全轨迹 DPO 更 sample-efficient
```

### 7.4 RL 阶段详解

#### 算法选择

| 算法 | 使用者 | 优缺点 | 适用场景 |
|------|-------|--------|---------|
| GRPO | Computer-RL, AgentCPM | 无需 Value Network, 显存低 | 资源受限、初期 |
| PPO | UI-TARS-2 | 更稳定，但需要额外 Value Model | 大规模、后期精调 |
| DPO (offline) | EvoCUA, Mano | 无需环境交互 | 关键步骤专项优化 |
| MRPO | Mobile-Agent-v3.5 | 解决跨平台梯度冲突 | 多平台联合训练 |

**建议路线**：

```
Phase 1: Step-level GRPO (参考 Computer-RL)
  ├── 优点：实现简单、显存友好
  ├── Reward: 稀疏 (任务成功=1, 失败=0) + Format Reward (代码不可执行=0)
  ├── Credit Assignment: 成功轨迹上所有格式正确的 step 获得 r=1
  └── 预期：训练 ~100-200 steps 后触顶

Phase 2: Entropulse (参考 Computer-RL)
  ├── 收集 Phase 1 所有成功 Rollout
  ├── 用这些数据做一轮 SFT → 恢复 Entropy
  ├── LR 降为 SFT 的 1/2 (Computer-RL 用 5e-6 vs SFT 的 1e-5)
  └── 效果：打破性能瓶颈

Phase 3: 继续 GRPO (或切换 PPO)
  ├── 加载 Phase 2 权重继续 RL
  ├── 如果 GRPO 仍不稳定，考虑切换 PPO
  │   ├── Value Pretraining (UI-TARS-2: 先冻结 policy，离线训练 value 至收敛)
  │   └── Decoupled GAE (UI-TARS-2: 解耦长序列的 advantage 计算)
  └── 预期：突破 Phase 1 的天花板

Phase 4: Offline DPO on 关键步骤 (参考 EvoCUA)
  ├── 从 RL 过程中收集 (成功关键步骤, 失败关键步骤) 对
  └── 预期：在关键步骤上的准确率进一步提升
```

#### Reward 设计

```
┌──────────────────────────────────────────────────────┐
│              Reward 设计（分层）                       │
│                                                      │
│  R_total = R_task + R_format + R_efficiency           │
│                                                      │
│  R_task (任务完成奖励):                               │
│  ├── Rule-based: Verifier 返回 0/1           (最优先) │
│  ├── Screenshot-diff: 前后截图对比           (其次)   │
│  ├── LLM-as-Judge: 模型评估                 (兜底)   │
│  └── Generative ORM: 自训练的 reward model   (后期)   │
│                                                      │
│  R_format (格式合规奖励):                             │
│  ├── 代码可解析: +0                                  │
│  ├── 代码不可解析: -1 (惩罚)                         │
│  └── 坐标越界: -0.5                                 │
│                                                      │
│  R_efficiency (效率奖励, 可选):                       │
│  ├── 步数奖励: -0.01 per step (鼓励简洁)             │
│  └── 重复动作惩罚: -0.1 if same action repeated       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### Online vs Offline RL

```
Online RL (GRPO/PPO):
  ├── 优势：探索新策略、适应环境动态
  ├── 劣势：需要大规模并行环境 (2000-4000)
  ├── 适用：主力训练方法
  └── 数据回收：成功 rollout → SFT 数据集（飞轮核心）

Offline RL (DPO):
  ├── 优势：无需环境交互，计算成本低
  ├── 劣势：无法探索新策略
  ├── 适用：关键步骤专项优化、EvoCUA +4 分
  ├── 数据来源：
  │   ├── Online RL 过程中的 (成功, 失败) 轨迹对
  │   ├── 同一任务的 (高效, 冗余) 轨迹对
  │   └── Mano: SFT 中 grounding 和规划错误的样本
  └── 时机：在 Online RL 之后做 "精修"

建议组合：Online GRPO → Entropulse → Online GRPO → Offline DPO
```

#### 跨平台 RL 的梯度冲突问题

Mobile-Agent-v3.5 发现 mobile/PC/web 混合训练导致梯度冲突 (Tug-of-war)，MRPO 采用"交替多平台优化"。

**对我们的启示**：

```
方案 A: 交替训练 (参考 MRPO)
  ├── Epoch 1: Windows 专项 RL
  ├── Epoch 2: macOS 专项 RL
  ├── Epoch 3: Linux 专项 RL
  └── 循环迭代

方案 B: 分别训练 + 参数插值 (参考 UI-TARS-2)
  ├── 分别训练 Windows / macOS / Linux 三个 vertical agent
  ├── 参数插值: θ_merge = α_w·θ_win + α_m·θ_mac + α_l·θ_linux
  └── 利用参数空间的线性连接特性

方案 C: 混合训练但动态加权
  ├── 在一个 batch 中混合三个平台的数据
  ├── 但根据各平台的 loss 动态调整采样比例
  └── 类似于 multi-task learning 的 uncertainty weighting

建议：先尝试方案 B（最安全），如果资源允许再对比方案 A。
```

### 7.5 Coding 能力的利用

#### API-GUI Paradigm（来自 Computer-RL，最重要的架构决策之一）

Computer-RL 的核心设计：模型输出 **Python 代码**而非 JSON，统一了 GUI 操作和 API 调用。

```python
# GUI Primitive — 跨平台统一
click(x=520, y=340)
double_click(x=520, y=340)
right_click(x=520, y=340)
type_text(text="Hello World")
hotkey("ctrl", "s")
scroll(direction="down", amount=3)
drag(start=(100, 200), end=(300, 400))
wait(seconds=2)

# Application-Specific API — 按当前窗口动态加载
# 当检测到活跃窗口是 LibreOffice Calc:
spreadsheet.set_cell("A1", "Revenue")
spreadsheet.insert_row(after=5)
spreadsheet.create_chart(range="A1:D10", type="bar")

# 当检测到活跃窗口是 Terminal:
terminal.run_command("ls -la")
terminal.run_command("python script.py")

# 当检测到活跃窗口是 Chrome:
browser.navigate("https://example.com")
browser.search("GUI agent papers")
```

#### 为什么 Code 优于 JSON

```
优势 1: 自然支持组合操作
  JSON: {"actions": [{"type": "click", ...}, {"type": "type", ...}]} → 平铺
  Code: click(x=100, y=200); type_text("hello")                     → 可组合、有逻辑

优势 2: 自然支持条件判断
  Code: if window_title == "Save As": click(x=300, y=400)
  JSON: 无法表达条件逻辑

优势 3: 自然支持循环和变量
  Code: for i in range(5): click(x=100, y=200+i*30)
  JSON: 需要重复 5 个 action

优势 4: 复用 LLM 的代码能力
  Qwen 系列本身代码能力强 → Code Action 天然受益于预训练知识

优势 5: 与 API 调用无缝衔接
  同一个代码块里可以混合 GUI 操作和 API 调用
```

#### 哪些桌面任务适合 Coding 解决

```
高 Coding 适合度 (直接生成脚本比 GUI 操作更高效):
  ├── 文件批量操作：重命名、移动、整理
  │   → Python os/shutil 比逐个点击快 100x
  ├── 文本处理：批量查找替换、格式转换
  │   → regex / sed 一行搞定
  ├── 数据处理：Excel/CSV 数据清洗
  │   → pandas 代码 vs 逐行点击
  ├── 系统配置：批量设置修改
  │   → registry/plist/gsettings 命令
  └── 安装部署：软件安装、环境配置
      → 包管理器命令

中 Coding 适合度 (GUI + API 混合):
  ├── Office 操作：用 API 操作文档结构 + GUI 操作排版
  ├── 浏览器操作：Playwright/Selenium API + 视觉导航
  └── IDE 操作：命令面板 + GUI 交互

低 Coding 适合度 (必须 GUI 操作):
  ├── 图像编辑：像素级操作无法纯代码化
  ├── 拖拽排版：空间操作需要视觉反馈
  └── 探索式浏览：目标不明确时需要视觉理解
```

#### 动态 API 加载（参考 Computer-RL）

```
实现方式：
  1. 检测当前活跃窗口 (Active Window Title / Process Name)
  2. 根据窗口匹配应用 → 加载对应的 API 定义
  3. 将 API 定义注入 System Prompt
  4. 模型在生成代码时可以调用这些 API

好处：
  ├── 减少 Context Window 压力 (不需要加载所有 API)
  ├── 减少模型幻觉 (只看到相关 API)
  └── 可扩展 (新应用只需添加 API 定义)

System Prompt 示例：
  "You are operating a Linux desktop. Current active window: LibreOffice Calc.
   Available APIs:
   - spreadsheet.set_cell(cell: str, value: str)
   - spreadsheet.get_cell(cell: str) -> str
   - spreadsheet.insert_row(after: int)
   ...
   You can also use GUI primitives: click(), type_text(), hotkey(), etc."
```

---

## 八、我们的已有基础 & 执行建议

### 8.1 已有资源评估

| 资源 | 状态 | 优势 | 补充需求 |
|------|------|------|---------|
| **基座模型** | Qwen 系列 2B-300B | 强视觉理解 + 强代码能力 | 需要验证 GUI 任务的 zero-shot 基线 |
| **大模型 API** | 充足 | 数据合成、CoT 标注、质量评估全覆盖 | 需要控制调用成本，设计高效 prompt |
| **计算资源** | 充足 | 支持全参数训练 + 大规模 RL | 需要规划 GPU vs VM 的分配 |
| **人工团队** | 有限 | - | 核心瓶颈，需要最大化模型驱动 |
| **录屏工具** | 曾开发过（合作方未开源） | 有经验 | 需要重新开发或采购 |
| **数据集调研** | 完成 | 知道哪些数据可用 | 需要实际下载、清洗、格式转换 |

### 8.2 分阶段执行计划

```
═══════════════════════════════════════════════════════════════════
 Month 1-2: 基建期
═══════════════════════════════════════════════════════════════════

[ ] 环境搭建
    ├── 部署 Windows/macOS/Linux VM 集群 (各 20-30 台)
    ├── 搭建 A11y 提取工具链 (pywinauto/macapptree/pyatspi2)
    ├── 搭建截图 + 动作录制管线
    └── 搭建统一数据格式转换管线

[ ] 开源数据准备
    ├── 下载并清洗 OS-ATLAS, GroundCUA, Jedi, GUI-360° 等
    ├── 格式统一化 (统一到我们定义的 schema)
    ├── 去重 (参考 AgentCPM 的 ResNet-50 方法)
    └── 按平台/应用/任务类型建立索引

[ ] Baseline 评测
    ├── Qwen2.5-VL 各尺寸在 ScreenSpot-Pro, OSWorld 上的 zero-shot 表现
    └── 确定各阶段训练的起点

[ ] 统一动作空间定义
    ├── 设计 GUI Primitive 集合 (跨平台统一)
    ├── 设计 Application-Specific API 模板 (参考 Computer-RL)
    └── 设计输出格式 (Thought → Action Desp → Code)

═══════════════════════════════════════════════════════════════════
 Month 2-4: L0.5 感知 + Grounding 训练
═══════════════════════════════════════════════════════════════════

[ ] Grounding 数据自建
    ├── A11y 自动标注管线上线 (每 VM ~50K 截图/月)
    ├── Hard Grounding Synthesis (参考 Mobile-Agent-v3.5)
    ├── Infeasible 负样本生成
    └── 目标：自建 2-5M grounding 样本

[ ] Phase 1 训练: L0.5
    ├── 数据：开源 grounding + 自建 + 30% 通用 VLM 数据
    ├── 规模：~15-20M 样本
    ├── 先训 7B，验证流程后扩展到其他尺寸
    └── 评测：ScreenSpot-Pro 目标 top-3

═══════════════════════════════════════════════════════════════════
 Month 3-5: SFT 轨迹训练
═══════════════════════════════════════════════════════════════════

[ ] 轨迹数据自建
    ├── OS-Genesis 逆向合成管线上线 (macOS/Linux 重点)
    ├── 教程驱动合成管线上线
    ├── DAG 定义 (高频应用 top 20)
    └── 目标：自建 300K-500K 轨迹

[ ] Phase 2 训练: SFT
    ├── 数据：开源轨迹 + 自建轨迹 + 25% 通用数据
    ├── Cold-start: 先用高质量子集 (100K-200K 步) 冷启动
    ├── 格式：Thought → Action Desp → Code
    ├── 历史：前 2 帧截图 + 全部历史文本摘要
    └── 评测：OSWorld 目标 >15% SR

═══════════════════════════════════════════════════════════════════
 Month 4-7: Verifier + RL
═══════════════════════════════════════════════════════════════════

[ ] Verifier 构建
    ├── 高频应用 Rule-based Verifier (文件管理/文本/终端/浏览器)
    ├── Office 应用 Verifier (参考 Computer-RL 的 SpreadsheetBench)
    ├── LLM-as-Judge 模板
    ├── 目标：5000-10000 个有 Verifier 的任务
    └── 同步开始训练 Generative ORM

[ ] RL 沙盒环境
    ├── Docker/VM 快照池 (快速重置)
    ├── 分布式环境管理器
    └── 目标并发：2000-4000

[ ] Phase 3 训练: RL
    ├── Step 1: Online GRPO (~100-200 training steps)
    ├── Step 2: Entropulse (收集成功 rollout → SFT 恢复 entropy)
    ├── Step 3: 继续 GRPO (突破天花板)
    ├── Step 4: Offline DPO (关键步骤专项)
    ├── 数据飞轮：成功 rollout → 回收到 SFT 集合
    └── 评测：OSWorld 目标 >30% SR

═══════════════════════════════════════════════════════════════════
 Month 6-10: Scale + 跨平台融合
═══════════════════════════════════════════════════════════════════

[ ] 多尺寸模型训练
    ├── 2B: 全参数训练 + 知识蒸馏 from 72B
    ├── 7B: 主力模型，完整四阶段
    ├── 72B: LoRA + 全参数混合
    └── 300B MoE: 3D 并行 + Expert 并行

[ ] 跨平台融合
    ├── 方案 B 优先：分别训练 Win/Mac/Linux vertical agents
    ├── 参数插值融合
    ├── 对比方案 A (交替训练 MRPO) 的效果
    └── 评测：全平台 OSWorld + WAA + 自建 benchmark

[ ] 持续飞轮
    ├── RL 成功数据 → SFT
    ├── 失败数据 → LLM 修正 → SFT (Mano 策略)
    ├── 低质量数据 → CT (UI-TARS-2 策略)
    └── 模型持续迭代
```

### 8.3 风险点与对策

| 风险 | 严重度 | 对策 |
|------|-------|------|
| macOS VM 获取困难/成本高 | 高 | AWS Mac 实例预留 + 尝试 Tart/Anka 虚拟化 |
| A11y Tree 在不同 OS/应用上的覆盖率不一致 | 中 | 混合训练有/无 A11y 的数据，推理时自动降级 |
| 桌面端 Verifier 构建困难 | 高 | 优先覆盖可编程验证的应用，配合 LLM-as-Judge 兜底 |
| RL 训练不稳定 (entropy collapse) | 中 | Entropulse 机制 + 密切监控 entropy 指标 |
| 开源数据与 Qwen 的 pattern 不兼容 | 中 | EvoCUA 经验：工程对齐 (RoPE 等) + 混合比例调优 |
| 统一动作空间的设计影响全局 | 高 | 早期充分验证 Code Action 的可行性，预留 fallback |
| 人工团队瓶颈 | 高 | 最大化 LLM 驱动，人工仅用于 in-policy 标注和质检 |

### 8.4 最优先启动的 3 件事

```
1. 搭建跨平台 A11y 提取 + 截图管线
   → 这是所有数据自建的基础，应该立即开始

2. 下载并清洗 OS-ATLAS + GroundCUA → 训练 Grounding baseline
   → 用开源数据最快出第一版 Grounding 模型，建立信心

3. 设计并实现统一动作空间 (API-GUI Paradigm)
   → 这是架构层面的决策，越早确定越好，所有后续数据都依赖这个定义
```
