# CUA 基座模型方法论

> 综合 Mobile-Agent-v3.5、Mano、EvoCUA、UI-TARS-2、AgentCPM、Computer-RL (AutoGLM-OS) 的技术方案
> 目标：全平台 (Win/macOS/Linux) Desktop GUI 基座模型，Qwen 2B–300B

---

## 一、核心认知

1. **数据闭环 > 模型架构**。UI-TARS-2 的 data flywheel、Computer-RL 的 Entropulse 数据回收、Mano 的闭环循环——数据管线的迭代效率决定最终性能。EvoCUA 用 5K 轨迹 + 多轮 RFT 做到 51 分，迭代质量 > 一次性堆量。Computer-RL 仅 180K 步即完成可用 cold-start。

2. **RL 是性能跃迁的关键，但瓶颈在环境和 Verifier**。所有 SOTA（UI-TARS-2/Computer-RL/EvoCUA/Mano/Mobile-Agent-v3.5）均在 SFT 后做 RL。EvoCUA 需 2000-4000 并发环境。Computer-RL 配备 ~8000 个可编程 Verifier。桌面端 Verifier 构建难度高于 Web/Mobile。

3. **统一动作空间未被充分解决**。Mobile/Web/Desktop 的 action space 仍割裂。Computer-RL 的 API-GUI Paradigm（Python 代码统一 GUI primitive + application-specific API）是当前最优方案。

4. **Grounding 是基础瓶颈**。AgentCPM 投入 12M grounding 预训练样本。Mobile-Agent-v3.5 做 hard grounding synthesis + infeasible 负样本。ScreenSpot-Pro SOTA 仅 18.9%。桌面端元素更密更小，grounding 难度高于 mobile。

5. **Verifier 质量决定 RL 上限**。Computer-RL: 8K 可编程 Verifier。UI-TARS-2: JS 脚本 + LLM-as-Judge + Generative ORM 分层设计。EvoCUA: verifier 全部模型生成。

---

## 二、环境

### 2.1 各阶段环境需求

| 阶段 | 并发规模 | 用途 |
|------|---------|------|
| 数据采集 | 50-100 VM | OS-Genesis 逆向探索、教程回放、人工录制 |
| SFT | 同上 | 数据采集持续进行 |
| Online RL | 2000-4000 并发 | GRPO/PPO rollout + Verifier 验证 |

参考：Computer-RL 数千并发 VM；EvoCUA 2000-4000 环境。

### 2.2 环境分层

**Layer 1: 采集环境 (~50-100 台)**
- Windows 11 VM × 30, macOS VM × 10, Ubuntu 24.04 GNOME VM × 10
- 工具链：截图 + A11y 提取 + 动作录制/回放

**Layer 2: RL 沙盒 (~2000-4000 并发)**
- Docker/VM 快照池，预配置应用 + 任务初始状态
- 快速重置 <10s
- Verifier 执行框架，每个任务绑定验证脚本
- 分布式环境管理器（参考 Computer-RL）

**Layer 3: 虚拟渲染环境（参考 Mobile-Agent-v3.5）**
- Web 渲染的虚拟桌面应用（文档编辑器、表格等）
- 状态完全可控，Verifier 天然精确
- 适用 Office 类任务、表单填写、设置

### 2.3 跨平台 A11y 工具链

| 平台 | 工具 | 成熟度 |
|------|------|--------|
| Windows | `pywinauto` + UIA API | 高 |
| macOS | `macapptree` + AX API + `Screen2AX` | 中 |
| Linux | `pyatspi2` + AT-SPI | 中低 |

Mano 经验：A11y Tree + OmniParse 混合最稳健。Computer-RL 经验：纯视觉（移除 A11y）也可行，减少 Token 消耗。
策略：训练时混合有/无 A11y 数据，推理时按需选择。

### 2.4 Verifier 体系

**Tier 1: Rule-based**（精确，范围窄）
- 文件系统状态、应用窗口状态、文档结构解析、系统配置读取
- 参考 Computer-RL ~8000 个可编程 Verifier

**Tier 2: Screenshot-diff**（中等精度）
- 前后截图关键区域比对 + OCR 验证

**Tier 3: LLM-as-Judge**（灵活，精度依赖 prompt）
- 输入：任务指令 + 初始/最终截图 + 操作历史 → 成功/失败 + 评分
- EvoCUA: verifier 全部模型生成

**Tier 4: Generative ORM**（参考 UI-TARS-2）
- 自训练 Outcome Reward Model，输入历史文本 + 最近 5 帧截图 → 标量评分

构建优先级：文件管理(低) > 文本编辑(低) > 终端(低) > 浏览器(中) > Office(中, 参考 Computer-RL SpreadsheetBench/PPTC) > 设置(中) > IDE(中高) > 图像编辑(高)

---

## 三、训练数据 Scaling

### 3.1 数据闭环

```
采集 → 训练(SFT/RL) → Rollout → Verifier 验证 → 数据回收 → 质量过滤 → 路由
                                                                    │
  高质量成功轨迹 ──────────▶ SFT 数据集
  低质量/失败轨迹 ──────────▶ CT 数据集              (UI-TARS-2)
  成功但中间有错 ───────────▶ LLM 修正 → SFT         (Mano)
  成功 Rollout 集合 ────────▶ Entropy 恢复 SFT       (Computer-RL)
```

### 3.2 数据规模参考

| 阶段 | AgentCPM | Computer-RL | EvoCUA | 我们目标 |
|------|---------|-------------|--------|---------|
| Grounding 预训练 | 12M (含50%通用) | - | - | **15-20M** |
| SFT 轨迹 | 55K轨迹/470K步 | 180K步 | 5K轨迹(冷启动) | **500K轨迹/5M步** |
| SFT 通用数据混合 | 50% | 0% | 50% | **25-30%** |
| RL Task 数 | - | ~8000 | ~3000-5000 | **10,000+** |
| RL 环境并发 | - | 数千 | 2000-4000 | **2000-4000** |

### 3.3 关键洞察

- **冷启动质量 > 数量**。Computer-RL 180K 步 cold-start。EvoCUA 5K 轨迹。条件：全部通过 Verifier 验证；多个强模型作为 Teacher 取最优（Computer-RL Model Pool）；按难度分层采集。
- **每个 Query 多条轨迹 > 更多 Query**。EvoCUA 实验确认。同一任务不同解法提供更好的 policy space 覆盖。
- **通用数据混合防止 mode collapse**。AgentCPM Grounding 阶段混 50% 通用多模态数据，SFT 阶段也混 50%。Qwen-VL 基座能力强，可降至 25-30%。
- **RL 的 scaling 瓶颈在环境和 Verifier**。EvoCUA: "最重视 scaling，沙盒还有 verifier"。

---

## 四、开源数据

### 4.1 Grounding 预训练

| 数据集 | 数据量 | 用法 | 优先级 |
|--------|--------|------|--------|
| OS-ATLAS | 13M+ 元素，跨平台 | 桌面部分 element grounding | P0 |
| GroundCUA | 3.56M 标注，56K 截图 | grounding 训练 | P0 |
| Jedi | 4M 合成 | 数据增强 | P1 |
| GUICourse | 多阶段 | OCR 训练 | P1 |
| Rico | 3M 元素 | mobile → desktop 迁移 | P2 |
| 通用 VLM 数据 | 占总量 30-50% | 防止视觉模块退化 | P0 |

自建增强（参考 Mobile-Agent-v3.5）：
- Hard Grounding Synthesis：MLLM 渲染高难度专业软件截图 + 多窗口场景
- Infeasible 负样本：(截图, Query) 随机组合 + 多模型共识过滤，正负比 ~1:10
- 从探索轨迹用 Critic 模型挖掘 grounding 对（零额外成本）

### 4.2 SFT 轨迹

| 数据集 | 数据量 | 用法 | 优先级 |
|--------|--------|------|--------|
| **OpenCUA/AgentNet** | **22,625 轨迹，3 OS (Win/macOS/Ubuntu)，200+ 应用** | **跨平台桌面轨迹核心数据，含截图 + A11y Tree + 键鼠事件 + 多级 CoT** | **P0** |
| GUI-360° | 1.2M 步 | Windows 桌面轨迹 | P0 |
| ScaleCUA | 大规模，6 OS | 跨平台轨迹 | P0 |
| OmniACT | 中等 | 代码级动作 (PyAutoGUI) | P1 |
| Mind2Web | 2K+ tasks | 浏览器操作 | P1 |
| GUIAct | 127K-1.26M 行 | GUI 交互动作 | P1 |
| AITW | 715K episodes | 交互模式迁移 | P2 |
| 通用对话/VQA | 占 25-30% | 防止 mode collapse | P0 |

**OpenCUA/AgentNet 使用说明**：
- 当前桌面端唯一同时覆盖 Windows/macOS/Ubuntu 三平台的大规模轨迹数据集
- 包含 AgentNetTool 采集的录屏、低级键鼠事件、A11y Tree、多级 CoT reasoning
- Mano 使用了 10% OpenCUA 数据（清洗后混入 SFT），EvoCUA 也使用了 OpenCUA
- **已知问题**：EvoCUA 指出 OpenCUA 模型 pattern 与 Qwen 差异大（entropy 高，需要工程对齐如 RoPE），直接使用需做格式转换和对齐

**数据清洗注意**：
- 开源数据格式统一到自定义 schema
- 参考 AgentCPM: ResNet-50 特征 + 余弦相似度去重（AITW 保留约 40%）
- 参考 Mano 洗 OpenCUA 的经验做格式对齐
- 历史帧：保留前 2 帧截图 + 全部历史文本摘要（Mano 实验最优）

### 4.3 RL Verifier 参考

| 来源 | 可复用 |
|------|--------|
| Computer-RL | SpreadsheetBench, PPTC 的 verifier 设计 |
| OSWorld | 369 任务评估框架 |
| Windows Agent Arena | 154 任务评估逻辑 |
| AssistGUI | 100 专业软件任务 |
| OpenCUA/AgentNetBench | 离线评估框架，可做轨迹质量筛选 |

### 4.4 开源数据已知问题

| 问题 | 解决方案 |
|------|---------|
| 平台偏向（GUI-360° 仅 Windows） | OpenCUA 补齐 macOS/Linux + 自建数据 |
| 动作空间不统一 | 定义统一 schema 格式转换 |
| AITW 冗余高 | ResNet-50 去重 (AgentCPM) |
| OpenCUA 与 Qwen pattern 不兼容 | RoPE 对齐 + 混合比例调优 (EvoCUA 经验) |
| 多数数据集无 A11y | 能补就补，不能补作为纯视觉样本 |

---

## 五、L0.5 — 感知与 Grounding

### 5.1 能力定义

```
L0.5a - 基础视觉感知
  OCR / 元素检测 / 布局理解 / 截图描述

L0.5b - 精准 Grounding
  Text Grounding / Icon Grounding / Descriptive Grounding
  Negative Sample (拒答) / Multi-modal (截图 + A11y → 坐标)

L0.5c - 高难度 Grounding
  多窗口重叠 / 专业软件 UI / 高分辨率小元素 / 动态状态
```

### 5.2 数据构造

| 策略 | 方法 | 参考 | 产出量级 |
|------|------|------|---------|
| Hard Grounding Synthesis | MLLM 渲染高难度截图 + 多窗口重组 | Mobile-Agent-v3.5 | 数十万 |
| 探索轨迹挖掘 | OS-Genesis 探索过程中提取 grounding 对 + Critic 清洗 | Mobile-Agent-v3.5 | 百万级 |
| Infeasible 负样本 | (截图, Query) 随机组合 + 多模型共识过滤 | Mobile-Agent-v3.5 | 与正样本 1:10 |
| A11y 自动标注 | VM 遍历应用 → 截图 + A11y Tree → 自动生成 grounding 指令 | 自建 | 百万级 |

### 5.3 训练配置

```
数据规模: 15-20M 样本
配比: GUI Grounding 50% / 通用多模态 30% / OCR 10% / 布局 10%
超参 (7B): LR 2e-5 cosine, Epochs 2-3, Global BS 256, 动态分辨率
```

---

## 六、L1 — 任务分解与重组

### 6.1 能力层级

| 层级 | 描述 | 示例 |
|------|------|------|
| L1a | 原子任务 | "点击文件菜单" → 单步执行 |
| L1b | 线性多步 | "保存文件为 PDF" → 3-5 步，单应用 |
| L1c | 条件分支 | "如果未保存则先保存，再关闭" → 状态判断 |
| L1d | 跨应用工作流 | "从邮件提取数据，整理到 Excel，截图发 Slack" → 长序列 |

### 6.2 数据构造方法

**DAG + 自动化探索（参考 Mobile-Agent-v3.5）**
- 人工为每个应用构建 DAG（状态 → 转移 → 原子任务）
- Agent 按 DAG 路径执行，节点处 checkpoint 验证
- 失败时截断到最后正确 checkpoint，动态重写指令

**LLM 指令复杂化（参考 UI-TARS-2）**
- Multi-Condition Obfuscation: 附加混淆条件
- Multi-Hop Chain-Like Conditions: 多跳链式条件

**任务重组**
- 从 DAG 原子任务中随机拼接 3-8 步 + LLM 生成统一自然语言描述 + 跨应用组合

### 6.3 输出格式

采用 Thought → Action Description → Action 三段式（参考 Mano, +2.8 提升）：

```
<think>
[Observation] 当前界面：LibreOffice Writer，空白文档。
[Memory] 任务要求创建会议纪要模板。
[Progress] Step 1/6：输入标题。
[Thought] 先输入标题文字。
</think>
<summary>Type "会议纪要" at cursor position.</summary>
<action>type(text="会议纪要")</action>
```

Mobile-Agent-v3.5 用五段式 CoT（Observation → Memory → Reflection & Progress → Thought → Conclusion）。
完整 CoT 在 SFT 阶段使用，RL 阶段可精简。2B 小模型可精简为 `<think>..short..</think><action>...</action>`。

---

## 七、训练方式

### 7.1 总流程

```
CT (可选) → SFT → Online RL → [Entropulse → Online RL]* → Offline DPO → 参数插值

CT:          UI-TARS-2, AgentCPM 做了
SFT:         所有工作都做了
Entropulse:  Computer-RL 独创（SFT 恢复 entropy，打破 RL 瓶颈）
参数插值:     UI-TARS-2（分别训练 vertical agents → 加权融合）
```

### 7.2 SFT

**数据配比**

| 来源 | Mano | AgentCPM | 建议 |
|------|------|---------|------|
| 自动采集轨迹 | 70% | - | 50% |
| 开源数据（含 OpenCUA）| 10% | 多个开源集 | 15% |
| 人工标注 | 20% | 真机录制 | 10% |
| 通用对话/VQA | 0% | 50% | 25% |

AgentCPM 混 50% 通用数据因 MiniCPM 基础弱，Qwen-VL 可降至 25%。

**关键技巧**

| 技巧 | 来源 | 要点 |
|------|------|------|
| In-policy 标注 | UI-TARS-2 | 模型 rollout → 人工 accept/override，保持训练-推理分布一致 |
| 历史帧策略 | Mano | 前 2 帧截图 + 全部历史文本摘要 = 最优 |
| CoT Warm-up | AgentCPM | SFT 早期混 ~5% 纯 CoT 推理数据，逐步增加轨迹比例 |
| Action Desp | Mano | Thought 和 Action 之间加一句话摘要 → +2.8 |
| World Model | Mobile-Agent-v3.5 | 训练预测 "动作后界面变化"，提升前瞻性 |

### 7.3 关键步骤训练

EvoCUA 冷启动配比：50% 通用 + 35% 普通步骤 + **15% 关键步骤**。

**关键步骤** = 对任务成败有决定性影响的步骤（不可逆操作、分支决策点、最后一步 submit/save）。

识别方法：
- Verifier 回溯：失败轨迹中第一个偏离正确路径的步骤
- 状态变化分析：前后截图差异大的步骤
- DAG 结构分析：in-degree > 1 或 out-degree > 1 的节点
- 末步强制标记

训练策略：
- SFT: 关键步骤 upsampling 到 15-20%
- RL: Offline DPO 专门对关键步骤学习（正例：正确执行，负例：错误执行），比全轨迹 DPO 更 sample-efficient（EvoCUA: +4 分）

### 7.4 RL

**算法选择**

| 算法 | 使用者 | 特点 |
|------|-------|------|
| Step-level GRPO | Computer-RL, AgentCPM | 无 Value Network，显存低 |
| PPO | UI-TARS-2 | 更稳定，需额外 Value Model |
| Offline DPO | EvoCUA, Mano | 无需环境交互 |
| MRPO | Mobile-Agent-v3.5 | 解决跨平台梯度冲突 |

**建议路线**

```
Phase 1: Step-level GRPO
  Reward: sparse (成功=1, 失败=0) + format (代码不可解析=0)
  Credit assignment: 成功轨迹上所有格式正确的 step 获得 r=1
  预期: ~100-200 training steps 后触顶

Phase 2: Entropulse (Computer-RL)
  收集 Phase 1 所有成功 rollout → SFT 一轮 → 恢复 entropy
  LR: SFT 的 1/2 (Computer-RL: 5e-6 vs 1e-5)

Phase 3: 继续 GRPO / 切换 PPO
  PPO 时需 Value Pretraining (UI-TARS-2: 先冻结 policy 离线训练 value)
  + Decoupled GAE (UI-TARS-2: 解耦长序列 advantage 计算)

Phase 4: Offline DPO on 关键步骤 (EvoCUA)
```

**Reward 设计**

```
R_total = R_task + R_format + R_efficiency

R_task:       Rule-based Verifier (优先) → Screenshot-diff → LLM-as-Judge → Generative ORM
R_format:     代码可解析 0 / 不可解析 -1 / 坐标越界 -0.5
R_efficiency: -0.01 per step / -0.1 重复动作
```

**Online vs Offline**

| | Online RL (GRPO/PPO) | Offline RL (DPO) |
|-|---------------------|------------------|
| 优势 | 探索新策略 | 无需环境，成本低 |
| 劣势 | 需 2000-4000 并发环境 | 无法探索 |
| 适用 | 主力训练 | 关键步骤专项 |
| 数据回收 | 成功 rollout → SFT 集合 | Mano: SFT 中 grounding/规划错误样本 |

组合：Online GRPO → Entropulse → Online GRPO → Offline DPO

**跨平台梯度冲突**

Mobile-Agent-v3.5: 混合训练导致梯度冲突。MRPO 采用交替多平台优化。

| 方案 | 方法 | 来源 |
|------|------|------|
| A: 交替训练 | Win → macOS → Linux 周期迭代 | MRPO |
| B: 分别训练 + 参数插值 | θ_merge = Σα_k·θ_k | UI-TARS-2 |
| C: 动态加权混合 | batch 内混合，按 loss 动态调比例 | multi-task learning |

建议先做 B（最安全），再对比 A。

### 7.5 Coding 能力利用

**API-GUI Paradigm（Computer-RL）**

模型输出 Python 代码，统一 GUI primitive 和 application-specific API：

```python
# GUI Primitive（跨平台统一）
click(x=520, y=340)
type_text(text="Hello World")
hotkey("ctrl", "s")
scroll(direction="down", amount=3)
drag(start=(100, 200), end=(300, 400))

# Application-Specific API（按活跃窗口动态加载）
spreadsheet.set_cell("A1", "Revenue")    # LibreOffice Calc
terminal.run_command("ls -la")           # Terminal
browser.navigate("https://example.com")  # Chrome
```

Code 输出优于 JSON 的原因：
1. 支持组合操作、条件判断、循环
2. 复用 LLM 预训练代码能力
3. GUI 操作与 API 调用在同一代码块中无缝混合

**动态 API 加载（Computer-RL）**：检测活跃窗口 → 加载对应 API 定义注入 System Prompt → 减少 context 压力和幻觉。

**适合 Coding 的桌面任务**

| 适合度 | 任务类型 |
|--------|---------|
| 高 | 文件批量操作、文本处理、数据处理(pandas)、系统配置、安装部署 |
| 中 | Office(API+GUI 混合)、浏览器(Playwright+视觉)、IDE(命令面板+GUI) |
| 低 | 图像编辑、拖拽排版、探索式浏览 |

---

## 八、执行计划

### 8.1 资源现状

| 资源 | 状态 | 行动 |
|------|------|------|
| 基座模型 | Qwen 2B-300B | 先测 zero-shot baseline |
| 大模型 API | 充足 | 用于数据合成/CoT 标注/质量评估 |
| 计算 | 充足 | GPU 和 VM 分配规划 |
| 人工 | 有限 | 最大化模型驱动，人工仅做 in-policy 标注和质检 |

### 8.2 Timeline

**Month 1-2: 基建**

- 部署 Win/macOS/Linux VM 集群（各 20-30 台）
- A11y 提取工具链调通（pywinauto / macapptree / pyatspi2）
- 截图 + 动作录制管线
- 统一数据格式转换管线
- 下载清洗 OS-ATLAS, GroundCUA, Jedi, GUI-360°, OpenCUA/AgentNet
- 格式统一化 + 去重（ResNet-50, AgentCPM 方法）
- Qwen2.5-VL 各尺寸 zero-shot baseline（ScreenSpot-Pro, OSWorld）
- 设计统一动作空间（GUI Primitive + Application API + 输出格式）

**Month 2-4: L0.5 Grounding**

- A11y 自动标注管线上线
- Hard Grounding Synthesis + Infeasible 负样本
- 目标：自建 2-5M grounding 样本
- Phase 1 训练：开源 grounding + 自建 + 30% 通用 VLM, ~15-20M 样本
- 先训 7B 验证流程，再扩展
- 评测目标：ScreenSpot-Pro top-3

**Month 3-5: SFT**

- OS-Genesis 逆向合成管线上线（macOS/Linux 重点）
- 教程驱动合成管线上线
- DAG 定义（高频应用 top 20）
- 目标：自建 300K-500K 轨迹
- Phase 2 训练：开源轨迹（含 OpenCUA/AgentNet）+ 自建 + 25% 通用
- Cold-start 先用高质量子集 100K-200K 步
- 评测目标：OSWorld >15% SR

**Month 4-7: RL**

- 构建 Rule-based Verifier（高频应用优先）+ LLM-as-Judge 模板
- 目标：5000-10000 个有 Verifier 的任务
- Docker/VM 快照池 + 分布式环境管理器，目标并发 2000-4000
- Phase 3: Online GRPO → Entropulse → GRPO → Offline DPO
- 数据飞轮启动：成功 rollout 回收到 SFT 集合
- 评测目标：OSWorld >30% SR

**Month 6-10: Scale + 融合**

- 多尺寸：2B (全参数+蒸馏), 7B (完整四阶段), 72B (LoRA+全参数), 300B MoE (3D+Expert 并行)
- 跨平台融合：先做方案 B（vertical agents → 参数插值），对比方案 A（MRPO）
- 持续飞轮：RL 成功→SFT / 失败→LLM 修正→SFT / 低质量→CT

### 8.3 风险

| 风险 | 对策 |
|------|------|
| macOS VM 成本高 | AWS Mac 预留 + Tart/Anka 虚拟化 |
| A11y 跨 OS 覆盖率不一致 | 混合有/无 A11y 训练，推理时降级 |
| 桌面 Verifier 构建困难 | 优先可编程应用 + LLM-as-Judge 兜底 |
| RL entropy collapse | Entropulse + entropy 监控 |
| OpenCUA 与 Qwen pattern 不兼容 | RoPE 对齐 + 混合比例调优 |
| 统一动作空间设计风险 | 早期验证 Code Action 可行性 |
| 人工瓶颈 | LLM 驱动为主，人工仅 in-policy 标注+质检 |

### 8.4 立即启动

1. 搭建跨平台 A11y + 截图管线
2. 下载清洗 OS-ATLAS + GroundCUA + OpenCUA/AgentNet → 训练 Grounding baseline
3. 设计统一动作空间（API-GUI Paradigm）
