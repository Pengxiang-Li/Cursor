# Desktop GUI 基础模型训练方案

> 基座: Qwen 2B–300B | 平台: Windows / macOS / Linux | 分辨率: 1080p
> 能力: 感知 → Grounding → 动作预测 → 端到端任务完成
> 输入: 截图 + A11y Tree + DOM/UI Hierarchy (混合)
> 动作空间: 像素坐标 + 元素级 + 代码级 (PyAutoGUI) + API 调用 (混合)

---

## 一、开源数据分配

### Stage 1: 视觉感知预训练 (~20M 样本)

| 数据集 | 数据量 | 用法 | 处理 |
|--------|--------|------|------|
| OS-ATLAS (桌面部分) | ~8M | 截图 → 元素列表+坐标 | 按 OS 均衡采样 |
| GroundCUA | 56K 截图 / 3.56M 标注 | 截图-元素对 | 直接可用 |
| Jedi | 4M 合成 | 数据增强 | 与真实数据混合 |
| Rico | 66K screens / 3M elements | mobile → desktop 迁移 | resize 到 1080p |
| GUICourse | 多阶段 | OCR + 基础 grounding | curriculum learning 早期 |
| 自建 A11y 标注 | ~3M | A11y 自动提取 | 见自建管线 |

### Stage 2: GUI Grounding (~10M 样本)

| 数据集 | 用法 | 备注 |
|--------|------|------|
| OS-ATLAS 桌面部分 | 核心 grounding | 过滤 Win/Linux/macOS |
| GroundCUA | 高质量 grounding 对 | 直接可用 |
| Jedi | 合成增强 | 与真实数据混合 |
| 自建数据 | A11y tree → grounding 对 | 百万级 |

### Stage 3: 动作预测 & 轨迹 (~5M 步)

| 数据集 | 数据量 | 用法 | 备注 |
|--------|--------|------|------|
| OpenCUA/AgentNet | 22,625 轨迹, 3 OS, 200+ 应用 | 跨平台桌面轨迹核心 | 需格式对齐 (EvoCUA: pattern 与 Qwen 差异大) |
| GUI-360° | 1.2M 步 | Windows 桌面轨迹 | 仅 Windows |
| ScaleCUA | 大规模, 6 OS | 跨平台轨迹 | 提取桌面部分 |
| OmniACT | 中等 | 代码级动作 (PyAutoGUI) | |
| Mind2Web | 2K+ tasks | 浏览器操作 | 与桌面通用 |
| GUIAct | 127K-1.26M 行 | GUI 交互动作 | |
| AITW | 715K episodes | 交互模式迁移 | 需去重 (~40%, AgentCPM) |
| 自建轨迹 | 百万级目标 | 跨平台桌面 | 见自建管线 |

### Stage 4: 端到端 Agent 微调 (~1M 轨迹)

| 数据集 | 用法 | 备注 |
|--------|------|------|
| 自建高质量轨迹 (50%) | 完整多步执行 + CoT | 核心 |
| GUI-360° (20%) | 含 reasoning trace | |
| OpenCUA/AgentNet (10%) | 跨平台多步轨迹 | 清洗后使用 |
| NatureGAIA (10%) | 自纠正轨迹 | |
| DPO/GRPO 偏好对 (20%) | 成功 vs 失败 / 高效 vs 冗余 | |

### Evaluation

| Benchmark | 评测内容 |
|-----------|---------|
| OSWorld (369 tasks, 跨 OS) | 主评测 |
| Windows Agent Arena (154+ tasks) | Windows |
| ScreenSpot-Pro (1.59K) | Grounding |
| UI-Vision (83 apps) | 感知 |
| MMBench-GUI | 综合 |
| AssistGUI (100 tasks) | 专业软件 |

---

## 二、自建数据管线

设计原则：大模型 API 充足 + 人工有限 → 模型驱动 + 自动化 + 少量人工质检。

### 2.1 环境

| 平台 | 配置 | A11y 工具 |
|------|------|----------|
| Windows | Win11 VM × N, 预装 Office/VS Code/Chrome/Edge/Explorer/Settings/Paint | `pywinauto` + UIA API |
| macOS | macOS VM × N (AWS Mac/Orka), 预装 Safari/Finder/Terminal/Pages/Numbers | `macapptree` + AX API + `Screen2AX` |
| Linux | Ubuntu 24.04 GNOME VM × N, 预装 Firefox/Files/Terminal/LibreOffice/VS Code/GIMP | `pyatspi2` + AT-SPI |

共享基础设施：截图服务 (1080p) + A11y 提取服务 + 动作录制/回放引擎 + VM 快照/恢复。

### 2.2 采集策略 (4 条并行管线)

**管线 A: 逆向任务合成 (参考 OS-Genesis)**

1. Agent 在 VM 中自由探索 GUI（随机/启发式）
2. 每步记录 (screenshot_before, a11y_tree_before, action, screenshot_after, a11y_tree_after)
3. 将 (state_before, action, state_after) 三元组发给 LLM API 生成自然语言任务指令
4. 连续单步拼接为多步轨迹
5. LLM API 评分 (0-5)，过滤低分

产出：每 VM 每天 ~1000-5000 步。

**管线 B: 教程驱动合成 (参考 AgentTrek)**

1. 爬取桌面软件教程 (Microsoft Learn, Apple Support, ArchWiki, wikiHow, YouTube 字幕)
2. LLM API 转为结构化步骤
3. VLM Agent 在 VM 中按教程执行，录制轨迹
4. VLM 评估结果与教程预期一致性

产出：取决于教程数量，可爬取数万篇。

**管线 C: 任务模板批量生成**

1. 定义应用-功能矩阵 (~50 应用 × ~10 功能)
2. LLM API 按 (应用, 功能) 对生成 N 个变体任务
3. Agent 在 VM 中执行，录制轨迹
4. 自动验证任务完成

产出：~50 × 10 × 20 = 10,000 基础任务。

**管线 D: 人机协作标注**

1. 人工执行复杂多步任务
2. 录屏 + 动作记录工具自动捕获
3. LLM API 生成 thought/reasoning 标注
4. 人工审核关键节点

目标：~10K 高质量完整轨迹（每条 10-30 步）。

### 2.3 质量控制

| 层级 | 方法 | 过滤率 |
|------|------|--------|
| L1: 规则过滤 | 截图模糊/黑屏/重复、坐标越界、轨迹连续性 | ~30-40% |
| L2: 模型评估 | LLM API 对轨迹打分（完成度/效率/推理质量/一致性, 0-5），保留 ≥3.5 | ~50-60% 保留 |
| L3: 人工抽检 | 按 OS/应用/任务类型分层抽样 5%，通过/修正/拒绝，反馈 L1&L2 | 目标通过率 ≥90% |

### 2.4 统一数据格式

```json
{
  "task_id": "uuid",
  "source": "os-genesis | agenttrek | template | human | opensource:{name}",
  "platform": "windows | macos | linux",
  "app_category": "office | browser | ide | file_manager | terminal | settings | ...",
  "app_name": "LibreOffice Writer",
  "task_instruction": "在文档中创建一个3行4列的表格并设置表头",
  "difficulty": "easy | medium | hard | expert",
  "trajectory": [
    {
      "step": 1,
      "thought": "...",
      "screenshot_before": "path/to/001.png",
      "screenshot_after": "path/to/002.png",
      "a11y_tree_before": {},
      "a11y_tree_after": {},
      "action": {
        "action_type": "click",
        "coordinate": [320, 28],
        "element_id": "menu_table",
        "element_role": "MenuItem",
        "element_name": "Table"
      }
    }
  ],
  "metadata": {
    "resolution": "1920x1080",
    "os_version": "Ubuntu 22.04",
    "language": "en",
    "total_steps": 8,
    "success": true,
    "quality_score": 4.2
  }
}
```

---

## 三、多阶段训练

### 3.1 总览

```
Phase 1         Phase 2         Phase 3         Phase 4
UI Pretrain ──▶ Grounding ──▶  Trajectory ──▶  Agent SFT + RL
~20M samples    ~10M samples    ~5M steps       ~1M trajectories
LR: 2e-5       LR: 1e-5       LR: 1e-5        LR: 5e-6 + RL
全参数/LoRA     全参数          全参数           全参数 + DPO/GRPO
```

### 3.2 Phase 1: UI 感知预训练

```
数据配比:
  OS-ATLAS (桌面)      40%    ~8M
  GroundCUA            15%    ~3M
  Jedi (合成)          15%    ~3M
  Rico (mobile迁移)    10%    ~2M
  GUICourse (OCR)       5%    ~1M
  自建 A11y 标注       15%    ~3M

训练任务:
  UI Element Detection  30%
  OCR                   20%
  Layout Description    15%
  Element Counting      10%
  Screen Summary        15%
  A11y Tree Prediction  10%

平台分布: Win 40% / macOS 30% / Linux 30%
超参 (7B): LR 2e-5 cosine, BS 256, Epochs 2-3, 动态分辨率, Warmup 5%
```

### 3.3 Phase 2: GUI Grounding

```
数据配比:
  OS-ATLAS 桌面         35%    ~3.5M
  GroundCUA             25%    ~2.5M
  Jedi (合成)           20%    ~2M
  自建 grounding        20%    ~2M

训练任务:
  Point Grounding       40%    指令 → 坐标
  Box Grounding         30%    指令 → bbox
  Referring Expression  20%    指令 → 描述 + 坐标
  Multi-modal Grounding 10%    截图 + a11y → 坐标

关键:
  - 坐标归一化 [0, 1000]
  - 混入 ~10% 负样本 (无匹配元素 → 拒答)
  - Grounding-specific loss: L1 on coordinates + CE on text
```

### 3.4 Phase 3: 动作预测 & 轨迹

```
数据配比:
  GUI-360° (Windows)     25%    ~1.25M steps
  OpenCUA/AgentNet       15%    跨平台轨迹
  ScaleCUA (跨平台)      20%    ~1M steps
  自建轨迹               25%    ~1.25M steps
  OmniACT (代码级)        5%    ~0.25M steps
  Mind2Web + GUIAct      10%    ~0.5M steps

训练任务:
  Next Action Prediction           40%
  Action + Thought Prediction      30%
  Multi-step Planning (3-5步)      20%
  Code Generation (PyAutoGUI)      10%

动作空间统一 schema:
  {
    "thought": str,
    "action_type": "click|double_click|right_click|type|hotkey|scroll|drag|api_call|code|done|wait",
    "coordinate": [x, y] | null,
    "element_id": str | null,
    "text": str | null,
    "keys": [str] | null,
    "code": str | null,
    "api": str | null
  }
```

### 3.5 Phase 4: Agent 微调

```
数据:
  自建高质量轨迹         50%    ~500K
  GUI-360° (reasoning)   15%    ~150K
  OpenCUA/AgentNet       10%    ~100K
  NatureGAIA (自纠正)     5%    ~50K
  DPO/GRPO 偏好对        20%    ~200K pairs

训练:
  Step 1: SFT on successful trajectories (含 CoT)
  Step 2: DPO/GRPO alignment
    - 成功 vs 失败轨迹
    - 高效 vs 冗余轨迹
    - 自纠正能力 (识别错误 → 回退 → 重试)

偏好对来源:
  - GUI-360° success/fail 对
  - 同任务短/长轨迹对
  - RL rollout 收集
```

---

## 四、模型尺寸策略

| 尺寸 | 定位 | 训练策略 | 数据量 |
|------|------|---------|--------|
| 2B | 端侧部署, 低延迟 | Phase 1-2 全量, Phase 3 精简 (单步为主), Phase 4 聚焦高频简单任务, 知识蒸馏 from 72B | P1 5M + P2 3M + P3 1M + P4 100K |
| 7B | 标准部署, 性价比最优 | 四阶段完整训练, 全量数据 | P1 20M + P2 10M + P3 5M + P4 1M |
| 72B | 服务端高性能 | Phase 1-2 LoRA, Phase 3-4 全参数, 增加复杂任务 + 跨应用工作流比例 | 同 7B, 复杂任务 40% |
| 300B MoE | 旗舰 | 全量 + 3D/Expert 并行, 大量混入通用 VLM 数据防遗忘, Phase 4 强化开放域/多轮/自纠正/跨 OS | 每阶段 2-3x 于 7B |

---

## 五、数据缺口与自建优先级

### 开源数据覆盖

| | Win | macOS | Linux | Web | Mobile |
|-|-----|-------|-------|-----|--------|
| 感知/OCR | 充足 | 中等 | 稀缺 | 充足 | 充足 |
| Grounding | 充足 | 中等 | 稀缺 | 充足 | 充足 |
| 轨迹 | 充足 | 稀缺 | 稀缺 | 充足 | 充足 |
| 端到端 | 中等 | 极缺 | 极缺 | 中等 | 充足 |
| A11y Tree | 稀缺 | 稀缺 | 极缺 | 中等 | 充足 |
| 代码级动作 | 稀缺 | 极缺 | 极缺 | 稀缺 | 极缺 |

核心缺口：macOS/Linux 轨迹、代码级动作、跨应用工作流、A11y 标注、失败/自纠正轨迹。
OpenCUA/AgentNet 部分缓解了 macOS/Linux 轨迹缺口 (22,625 轨迹覆盖 3 OS)，但量级仍不足。

### 自建优先级

| 优先级 | 数据类型 | 目标量 | 方式 |
|--------|---------|--------|------|
| P0 | macOS 桌面轨迹 | 500K steps | OS-Genesis + 教程驱动 |
| P0 | Linux 桌面轨迹 | 500K steps | OS-Genesis + 教程驱动 |
| P0 | 跨平台 A11y + 截图对 | 2M pairs | 自动化 A11y 提取 |
| P1 | 代码级动作数据 | 200K | 模板生成 + LLM API 扩写 |
| P1 | 跨应用工作流 | 100K trajectories | 人工设计 + Agent 执行 |
| P1 | Windows 补充轨迹 | 500K steps | OS-Genesis |
| P2 | 失败 + 自纠正轨迹 | 200K | Agent 执行 + 自动收集 |
| P2 | 多语言 UI 数据 | 500K | 切换系统语言采集 |

---

## 六、评测

| 阶段 | Benchmark | 指标 |
|------|-----------|------|
| Phase 1 | 自建 UI 测试集 | Element F1, OCR Acc, Layout Acc |
| Phase 2 | ScreenSpot, ScreenSpot-Pro | Grounding Acc (text/icon/widget) |
| Phase 3 | 自建动作预测测试集 | Action Type Acc, Coord L1 Error, Step SR |
| Phase 4 | OSWorld, WAA, AssistGUI | Task SR, Step Efficiency, Avg Steps |
| 综合 | MMBench-GUI, UI-Vision | 多层级综合 |

持续评测：
- 每 checkpoint: ScreenSpot-Pro (~1.5h) + OSWorld subset 50 tasks (~4h) + 自建 smoke test 100 tasks × 3 OS (~2h)
- 每阶段结束: 全量 OSWorld (369) + WAA (154) + AssistGUI (100) + MMBench-GUI

---

## 附录：工具与资源

| 工具 | 用途 | Link |
|------|------|------|
| OS-Genesis | 逆向任务合成 | https://github.com/os-copilot/os-genesis |
| AgentTrek | 教程驱动轨迹合成 | https://github.com/xlang-ai/AgentTrek |
| OpenCUA | 跨平台数据集 + 模型 | https://github.com/xlang-ai/OpenCUA |
| pywinauto | Windows UI 自动化 | https://github.com/pywinauto/pywinauto |
| macapptree | macOS A11y 提取 | https://github.com/MacPaw/macapptree |
| Screen2AX | macOS 截图 → A11y | https://github.com/MacPaw/Screen2AX |
| pyatspi2 | Linux AT-SPI | https://github.com/GNOME/pyatspi2 |
| OSWorld | 跨 OS 评测 | https://github.com/xlang-ai/OSWorld |
