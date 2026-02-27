# CUA 调研汇报 —— 逐页 Slide 文本内容

---

## Slide 1 — 标题页

**标题**：CUA 调研：从已有工作看方法论

**副标题**：数据工程 · 训练范式 · 环境基建

**信息栏**：[姓名] · [日期] · [团队]

---

## Slide 2 — CUA 工作时间线

**标题**：2024-2025：CUA 密集爆发期

**时间线节点**（从左到右）：

- 2024 Q2 — AgentCPM（面壁智能）
- 2024 Q3 — UI-TARS 1.0（字节）
- 2024 Q4 — OSWorld / Windows Agent Arena 评测基准发布
- 2025 Q1 — Computer-RL / AutoGLM-OS（智谱）
- 2025 Q1 — Mano Tech Report
- 2025 Q1 — Mobile-Agent-v3.5（阿里）
- 2025 Q2 — UI-TARS-2（字节）
- 2025 Q2 — EvoCUA
- 2025 Q2 — DART-GUI

**底部注释**：同期产业动态：OpenAI Operator · Anthropic Computer Use · Google Mariner

---

## Slide 3 — 调研范围总览

**标题**：调研范围

**左列 — 核心工作（7 个）**：
- UI-TARS-2
- Computer-RL (AutoGLM-OS)
- Mobile-Agent-v3.5
- Mano
- EvoCUA
- AgentCPM
- DART-GUI

**中列 — 数据集（33 个）**：
- Grounding：OS-ATLAS / GroundCUA / Jedi / ScreenSpot-Pro
- 轨迹：OpenCUA / GUI-360° / ScaleCUA / AITW
- 评测：OSWorld / WAA / AssistGUI / MMBench-GUI

**右列 — 分析维度**：
- 数据构造方法论
- 训练流水线对比
- RL 算法与 Reward 设计
- 环境与基建架构
- 跨平台 Action Space

**底部一句话**：核心发现——CUA 的胜负手不在模型架构，而在数据闭环 × 环境规模 × Verifier 质量的系统工程。

---

## Slide 4 — 7 个核心工作纵览

**标题**：核心工作一览

**表格**：

| 工作 | 基座模型 | 目标平台 | 核心亮点 |
|------|---------|---------|---------|
| UI-TARS-2 | Seed-thinking-1.6 | 全平台 | Data Flywheel + 参数插值 + Generative ORM |
| Computer-RL | GLM-4V | Desktop | Entropulse + API-GUI Paradigm |
| Mobile-Agent-v3.5 | — | 全平台 | DAG 探索 + Hard Grounding + MRPO |
| Mano | UI-TARS-1.5-7B | Desktop/Web | Action Desp (+2.8) + 闭环数据循环 |
| EvoCUA | OpenCUA / Qwen3VL | Desktop | 关键步骤训练 + 5K traj → OSW 51 |
| AgentCPM | MiniCPM-V 8B | Mobile | 12M Grounding 预训练 + 真机录制 |
| DART-GUI | UI-TARS-1.5-7B | Desktop | 四个自适应策略 + 解耦异步架构 |

---

## Slide 5 — 五维对比雷达图

**标题**：七项工作多维对比

**五个维度**（雷达图轴）：
1. 数据规模
2. 训练深度（阶段数）
3. 平台覆盖
4. RL 规模（环境并发）
5. 开源程度

**建议**：用雷达图或气泡图展示，每个工作一种颜色。各工作参考定位：
- UI-TARS-2：训练深度最深（4 阶段 + 参数插值），平台最广
- Computer-RL：RL 规模大（数千并发），动作空间最统一
- EvoCUA：数据规模小但效率最高
- AgentCPM：Grounding 数据最多（12M）

---

## Slide 6 — 章节封面：数据工程

**标题**：Part I — 数据工程方法论

**副标题**：Grounding · 轨迹采集 · 数据闭环

**引言**："CUA 工作 80% 的篇幅在讲数据，这不是巧合。"

---

## Slide 7 — Grounding：桌面端的基础瓶颈

**标题**：Grounding 是 CUA 的基础瓶颈

**三栏布局**：

**左栏 — 现状数据**：
- ScreenSpot-Pro SOTA：仅 18.9%
- 桌面端难于移动端

**中栏 — 为什么难**：
1. 元素更密集（专业软件工具栏可达 100+ 按钮）
2. 分辨率更高（1080p-4K，小元素 <10px）
3. 多窗口重叠遮挡
4. 专业软件 UI 非标准化

**右栏 — 数据量参考**：
- AgentCPM：12M 样本（含 50% 通用数据正则化）
- OS-ATLAS：13M+ 元素
- GroundCUA：3.56M 标注

---

## Slide 8 — 四种 Grounding 数据构造范式

**标题**：Grounding 数据四大范式

**四象限布局**：

**范式 1：大规模自动标注** [AgentCPM]
- A11y Tree + View Hierarchy 自动提取
- 构造为 OCR（Text→Point）和 Widget 定位任务
- 规模：12M（混合 50% 通用数据防过拟合）

**范式 2：高难度合成** [Mobile-Agent-v3.5]
- MLLM 结合真实 UI 元素 + 参考界面渲染专业软件截图
- 单窗口数据集重组 → 高分辨率多窗口场景
- 规模：数十万级

**范式 3：负样本增强** [Mobile-Agent-v3.5]
- 图像-Query 随机组合 + 多模型共识过滤
- 生成大量"不可行"（Infeasible）样本
- 正:负 ≈ 1:10，增强拒答 / 纠错能力

**范式 4：探索副产物** [Mobile-Agent-v3.5]
- 从 OS-Genesis 探索轨迹中用 Critic 模型挖掘 grounding 对
- 零额外成本，百万级产出

---

## Slide 9 — Hard Grounding Synthesis 流程

**标题**：Hard Grounding Synthesis 流程（Mobile-Agent-v3.5）

**流程图（从左到右）**：

```
真实 UI 元素库  ──→  MLLM 渲染引擎  ──→  高难度专业软件截图
                        ↑
                   参考界面模板

单窗口数据集 ──→ 随机重组拼接 ──→ 多窗口重叠场景（无遮挡）

输出：(截图, 元素名, 坐标) 三元组
```

**右侧要点**：
- 可控制难度等级（简单 → 专业软件）
- 自动化程度高，无需人工标注
- 与负样本管线配合使用效果最佳

---

## Slide 10 — 开源 Grounding 数据集

**标题**：可用的开源 Grounding 数据

**表格**：

| 数据集 | 规模 | 平台 | 特点 |
|--------|------|------|------|
| OS-ATLAS | 13M+ 元素 | 跨平台 (5 OS) | 最大开源 GUI grounding 语料 |
| GroundCUA | 3.56M 标注, 56K 截图 | 跨平台 | 人工验证，87 个应用 |
| Jedi | 4M 合成样本 | 跨平台 | 多视角任务解耦合成 |
| GUICourse | 多阶段 | 跨平台 | OCR + 基础 grounding |
| ScreenSpot-Pro | 1,590 样本 | Desktop (3 OS) | 评测基准，23 个专业应用 |

**底部结论**：Grounding 预训练数据相对充足（>20M 可组合），核心缺口在高难度桌面场景 + 负样本。

---

## Slide 11 — 轨迹数据：四种采集范式

**标题**：轨迹数据四大采集范式

**2×2 矩阵图**：

```
             自动化程度 →
    低 ──────────────── 高
高  │ 人机协作         │ DAG 自动探索
质  │ (UI-TARS-2)      │ (Mobile-Agent-v3.5)
量  │ In-policy 标注   │ Checkpoint 验证
    │ 成本最高         │ 可靠但需预定义
    │──────────────────│──────────────────
低  │ 人工标注         │ DFS 自由探索
    │ (兜底)           │ (Mano Explorer)
    │ 传统方式         │ Claude 质检
    │                  │ 规模最大（70%）
```

**右侧要点**：
- 第五种（隐含）：虚拟环境生成（Mobile-Agent-v3.5）→ RPA 精准长轨迹

---

## Slide 12 — DAG 自动化探索详解

**标题**：DAG 自动化探索（Mobile-Agent-v3.5）

**流程图**：

```
人工定义 DAG              Agent 执行                  数据产出
┌─────────┐          ┌──────────────┐          ┌──────────────┐
│ 应用状态图│          │ 按 DAG 路径  │          │ 完整成功轨迹 │
│ 状态 → 转移│  ──→    │ 在真实设备执行│  ──→    │              │
│ 原子任务  │          │              │          └──────────────┘
└─────────┘          │   ↓ 失败？    │
                     │ Checkpoint 验证│          ┌──────────────┐
                     │   ↓ 是        │          │ 截断到最后   │
                     │ 截断到最后正确 │  ──→    │ 正确 step    │
                     │ 动态重写指令   │          │ + 重写指令   │
                     └──────────────┘          └──────────────┘
```

**关键创新**："部分成功"的轨迹不丢弃——截断 + 重写 = 干净训练数据

---

## Slide 13 — Mano Explorer 管线

**标题**：Mano Explorer：DFS 驱动的自动采集

**五步流程（纵向）**：

1. **目标生成** — Claude 为目标应用生成优先级排序的功能目标列表，过滤罕见功能
2. **元素提取** — Web: Chrome 插件 Mano-C（坐标 + DOM + ARIA）/ Desktop: A11y Tree + OmniParse 混合
3. **元素注释** — LLM 生成语义标签、功能描述、交互类别
4. **DFS 探索** — 最大深度 10 层 + Prompt 限制防循环
5. **质量评估** — Claude 评审：完整性 + 意图清晰度 + 连贯性 → 仅保留高分轨迹

**底部数据**：SFT 数据中 70% 来自此管线

---

## Slide 14 — Cold-start：质量 >> 数量

**标题**：Cold-start 的反直觉发现：质量远比数量重要

**对比表**：

| 工作 | Cold-start 数据量 | OSWorld 分数 | 关键条件 |
|------|-------------------|-------------|---------|
| Computer-RL | 180K 步 | — | 全部通过 Verifier 验证 |
| EvoCUA | 5K 轨迹 | 51 分 | 每个 query 平均 4-5 条正确轨迹 |
| AgentCPM | 55K 轨迹 / 470K 步 | — | 真机录制 + GPT-4o CoT 标注 |
| Mano | — | — | 70% 自动 + 20% 人工 + 10% 开源 |

**两个关键 Insight（大字突出）**：

1. 每个 Query 多条轨迹 > 更多 Query
   - EvoCUA 实验确认：同一任务的不同解法提供更好的 policy space 覆盖

2. 通用数据混合防 Mode Collapse
   - AgentCPM: 50%（基座弱） / Qwen 基座: 25-30% 足够

---

## Slide 15 — 开源轨迹数据 + 已知问题

**标题**：开源轨迹数据集与已知 "坑"

**表格**：

| 数据集 | 规模 | 平台 | 状态 |
|--------|------|------|------|
| OpenCUA / AgentNet | 22,625 轨迹 | Win/macOS/Ubuntu | 唯一三平台覆盖 |
| GUI-360° | 1.2M+ 步 | 仅 Windows | 含 reasoning trace |
| ScaleCUA | 大规模 | 6 OS | 跨平台 |
| AITW | 715K episodes | Android | 冗余高 |
| GUIAct | 127K-1.26M 行 | Web | GUI 交互动作 |

**已知问题（红色高亮）**：

| 问题 | 解法 |
|------|------|
| OpenCUA 与 Qwen pattern 差异大（entropy 高）| RoPE 对齐 + 混合比例调优 |
| AITW 冗余率 ~60% | ResNet-50 特征 + 余弦相似度去重 |
| GUI-360° 仅 Windows | OpenCUA 补齐 macOS/Linux |
| 多数数据集无 A11y Tree | 能补就补，否则作纯视觉样本 |

---

## Slide 16 — 数据飞轮

**标题**：数据闭环：模型既是学习者，也是数据生产者

**中心飞轮图**：

```
        ┌──── 训练 (SFT/RL) ────┐
        │                        │
        ↓                        │
    Rollout（环境交互）           │
        │                        │
        ↓                        │
    Verifier 验证                │
        │                        │
        ↓                        │
    数据路由 ──────────────────→ ┘
```

**四条路由分支**：

| 轨迹类型 | 路由目标 | 代表工作 |
|----------|---------|---------|
| 高质量成功轨迹 | → SFT 数据集 | UI-TARS-2, Mano |
| 低质量 / 失败轨迹 | → CT（持续预训练）数据集 | UI-TARS-2 |
| 成功但中间有错 | → LLM 生成草稿 + 人工修正 → SFT | Mano |
| 所有成功 Rollout 集合 | → Entropy 恢复 SFT | Computer-RL |

**底部一句话**：数据闭环的设计质量，决定了模型迭代的加速度。

---

## Slide 17 — 数据回收策略对比

**标题**：三家数据回收策略深度对比

**三列布局**：

**UI-TARS-2 — Data Flywheel**
- 最完整闭环：高质量 → SFT，低质量 → CT
- 路由函数 V(s) 自动分流
- 持续迭代，模型越强数据越好

**Computer-RL — Entropulse 回收**
- 收集 RL 各阶段成功 rollout
- 不同阶段 policy 产出 = 天然多样性
- SFT 一轮恢复 entropy → 继续 RL

**Mano — 修正回注**
- 成功轨迹直接加入 SFT
- 有错轨迹：LLM 草稿 + 人类专家修正
- 离线 RL 专用：挑选 Grounding/规划错误样本

---

## Slide 18 — 章节封面：训练方法论

**标题**：Part II — 训练方法论

**副标题**：多阶段流水线 · SFT 技巧 · RL 创新

**引言**："所有 SOTA 都在 SFT 后做 RL，无一例外。"

---

## Slide 19 — 统一训练流水线

**标题**：CUA 统一训练流水线

**横向箭头流程图**：

```
[CT] ──→ [Grounding 预训练] ──→ [SFT] ──→ [Online RL] ──→ [Entropy 恢复] ──→ [Online RL] ──→ [Offline DPO] ──→ [参数插值]
 可选     可选                    必选      必选            可选               可选            可选              可选
```

**底部标注各工作覆盖范围**：
- UI-TARS-2：CT → Grounding → SFT → Online RL (PPO) → 参数插值
- Computer-RL：SFT (BC) → Online RL (GRPO) → Entropulse → Online RL
- Mobile-Agent-v3.5：Pretrain → SFT → Online RL (MRPO)
- EvoCUA：SFT → Online RL (RFT) → Offline DPO
- AgentCPM：Grounding (12M) → SFT → Online RL (GRPO)

---

## Slide 20 — 训练阶段对比矩阵

**标题**：各工作训练阶段覆盖对比

**表格**（用 ✓ / ✗ 标记，高亮每个工作的独特阶段）：

| 工作 | CT | Grounding | SFT | Online RL | Entropulse | Offline DPO | 参数插值 |
|------|:--:|:---------:|:---:|:---------:|:----------:|:-----------:|:--------:|
| UI-TARS-2 | ✓ | ✓ | ✓ | ✓ PPO | ✗ | ✗ | ✓ |
| Computer-RL | ✗ | ✗ | ✓ BC | ✓ GRPO | ✓ | ✗ | ✗ |
| Mobile-Agent-v3.5 | ✓ | ✓ | ✓ | ✓ MRPO | ✗ | ✗ | ✗ |
| Mano | ✗ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ |
| EvoCUA | ✗ | ✗ | ✓ | ✓ RFT | ✗ | ✓ | ✗ |
| AgentCPM | ✗ | ✓ 12M | ✓ | ✓ GRPO | ✗ | ✗ | ✗ |
| DART-GUI | ✗ | ✗ | (已有) | ✓ GRPO | ✗ | ✗ | ✗ |

**底部观察**：SFT + Online RL 是必选项，其余为差异化竞争点。

---

## Slide 21 — Mano Action Description 示例

**标题**：SFT 技巧 1：Action Description（Mano, +2.8 分）

**核心思路**：在 Thought 和 Action 之间加一句话摘要

**具体示例**：

任务：在 LibreOffice Writer 中选中 "H2O" 中的数字 "2"

```
Thought:
"之前的选择没有准确抓取到数字'2'。为了将'2'设置为
下标，我需要重新执行选择。将鼠标移动到'H2O'中的
数字'2'，点击按住左键，拖动以仅选中'2'..."

Action Desp:
"Move the mouse to the number '2' in 'H2O', click and
hold the left button, drag to precisely select '2'."

Action:
drag(start_box=(689,500), end_box=(709,499))
```

**为什么有效**：摘要充当"意图锚点"，减少 Thought 到 Action 的信息损耗。

---

## Slide 22 — SFT 五大关键技巧

**标题**：SFT 阶段五大关键技巧

**表格**：

| # | 技巧 | 来源 | 效果 | 原理 |
|---|------|------|------|------|
| 1 | Action Description | Mano | +2.8 分 | Thought→Action 间加摘要锚点 |
| 2 | In-policy 标注 | UI-TARS-2 | 分布一致 | 模型 rollout → 人工 accept/override |
| 3 | 历史帧策略 | Mano | 最优平衡 | 保留前 2 帧截图 + 全部历史文本摘要 |
| 4 | CoT Warm-up | AgentCPM | 启动推理 | SFT 早期混入少量纯 CoT 数据 |
| 5 | 世界模型监督 | Mobile-Agent-v3.5 | 提升前瞻性 | 训练预测"动作后界面如何变化" |

---

## Slide 23 — 输出格式对比

**标题**：三种输出格式对比

**三列布局**：

**五段式（Mobile-Agent-v3.5）**
```
Observation: 当前界面状态...
Memory: 之前看到的价格是 ¥199...
Reflection: 任务进度 3/6...
Thought: 下一步应该...
Conclusion: click(520, 340)
```
适用：复杂多步任务，需要记忆和反思

**三段式（Mano）**
```
Thought: 分析当前状态...
Action Desp: 一句话摘要
Action: drag(start, end)
```
适用：通用场景，平衡信息量与简洁

**代码式（Computer-RL）**
```
Thought: 需要在 A1 输入 Revenue...
Code:
  spreadsheet.set_cell("A1", "Revenue")
  click(x=520, y=340)
```
适用：可编程应用，复用 LLM 代码能力

---

## Slide 24 — SFT 数据配比经验

**标题**：SFT 数据配比经验

**堆叠条形图数据**：

| 来源 | Mano | AgentCPM | 建议 (Qwen) |
|------|------|----------|-------------|
| 自动采集轨迹 | 70% | — | 50% |
| 开源数据 | 10% (OpenCUA) | 多个开源集 | 15% |
| 人工标注 | 20% | 真机录制 | 10% |
| 通用对话/VQA | 0% | 50% | 25% |

**底部注释**：
- AgentCPM 混 50% 通用 → 因为 MiniCPM 基座能力弱
- Qwen-VL 基座强 → 通用数据可降至 25%，但不能为 0

---

## Slide 25 — 章节封面：RL

**标题**：RL：性能跃迁的关键

**引言（大字）**："RL 的瓶颈从来不是算法，而是你能同时跑多少个环境、你的 Verifier 有多精确。"

---

## Slide 26 — RL 算法选择对比

**标题**：RL 算法选择

**表格**：

| 算法 | 使用者 | 需要 Value Model | 优势 | 劣势 |
|------|--------|:---------:|------|------|
| Step-level GRPO | Computer-RL, AgentCPM, DART-GUI | 否 | 显存低，实现简单 | 长序列 advantage 不稳定 |
| PPO (增强版) | UI-TARS-2 | 是 | 更稳定，长序列友好 | 显存高，需 Value Pretraining |
| MRPO | Mobile-Agent-v3.5 | — | 解决跨平台梯度冲突 | 需按平台交替训练 |
| Offline DPO | EvoCUA, Mano | 否 | 无需环境交互，成本低 | 无法探索新策略 |

**底部建议**：GRPO 入手门槛最低 → 遇到 entropy collapse 时引入 Entropulse → 后期可切 PPO 提升稳定性

---

## Slide 27 — Reward 分层设计

**标题**：Reward 设计：四层体系

**金字塔图（从下到上）**：

**Tier 1 — Rule-based Verifier**（底层，最精确）
- 文件系统状态检查、文档结构解析、系统配置读取
- Computer-RL：~8,000 个可编程 Verifier
- 适用：文件管理、终端、文本编辑、Office

**Tier 2 — JS 脚本 / Runtime 查询**
- 查询应用 runtime 变量获取二元奖励
- UI-TARS-2 游戏场景
- 适用：游戏、Web 应用

**Tier 3 — LLM-as-Judge**
- 输入：指令 + 截图序列 → 成功/失败 + 评分
- UI-TARS-2, EvoCUA
- 适用：开放式任务

**Tier 4 — Generative ORM**（顶层，最灵活）
- 自训练 Outcome Reward Model
- 输入：历史文本 + 最近 5 帧截图 → 标量评分
- UI-TARS-2 独创

---

## Slide 28 — Entropulse：打破 RL 天花板

**标题**：创新 1：Entropulse — 用 SFT 恢复 RL Entropy（Computer-RL）

**左侧 — Entropy 变化曲线示意**：

```
Entropy
  ↑
  │  ╲
  │   ╲  Phase 1: RL (GRPO)
  │    ╲  entropy 持续下降
  │     ╲_____ 触顶！性能瓶颈
  │           │
  │           │ Entropulse: 收集成功 rollout → SFT
  │           │
  │        ╱──┘  Entropy 恢复！
  │       ╱
  │      ╱  Phase 2: 继续 RL
  │     ╱    突破性能天花板
  │    ╱
  └──────────────────→ Training Steps
```

**右侧 — 机制**：
1. RL Phase 1 训练 ~180 steps → entropy collapse，性能触顶
2. 收集 Phase 1 所有成功 rollout（不同阶段 policy 生成 = 天然多样性）
3. 用这些数据做一轮 SFT（LR = 5e-6，原 LR 的一半）
4. Entropy 恢复 → 继续 RL → 突破天花板

**底部本质**：用"数据多样性"对抗"策略坍缩"

---

## Slide 29 — 关键步骤训练

**标题**：创新 2：关键步骤训练（EvoCUA, +4 分）

**左侧 — 什么是关键步骤**：
- 不可逆操作（删除文件、提交表单）
- 分支决策点（选择哪个菜单路径）
- 最终提交 / 保存
- 第一个偏离正确路径的步骤

**中间 — Cold-start 数据配比（饼图）**：
- 50% 通用数据
- 35% 普通步骤
- 15% 关键步骤

**右侧 — 训练策略**：

SFT 阶段：
- 关键步骤上采样至 15-20%

Offline DPO 阶段：
- 正例：正确执行关键步骤
- 负例：错误执行关键步骤
- 效果：单此一项 +4 分（比全轨迹 DPO 更高效）

**底部 Insight**：数据有限时，将训练信号集中在最关键处。

---

## Slide 30 — 跨平台梯度冲突

**标题**：创新 3：跨平台梯度冲突解决

**问题描述**：
手机/PC/Web 轨迹混合训练 → 动作空间和界面逻辑差异 → 梯度 Tug-of-war

**两种方案对比**：

| | 方案 A：MRPO 交替训练 | 方案 B：参数插值 |
|--|----------------------|-----------------|
| 来源 | Mobile-Agent-v3.5 | UI-TARS-2 |
| 做法 | Win → macOS → Linux 周期迭代，每阶段专注单一平台 | 分别训练 Vertical Agents → 加权插值 |
| 公式 | — | θ_merge = Σ α_k · θ_k |
| 理论基础 | 避免梯度干扰 | 模型在参数空间内线性连接（Mode-connected）|
| 优势 | 实现简单 | 各领域保持峰值性能 |
| 风险 | 遗忘问题 | 需搜索最优 α_k |

**MRPO 额外细节**：Token-ID Transport — 直接打包回传推理时的 Token IDs → 避免 Tokenizer 多义性导致的 log-prob 错位

---

## Slide 31 — DART-GUI 自适应策略

**标题**：工程亮点：DART-GUI 四个自适应策略

**四个卡片**：

**1. Dynamic Rollout Number**
- 成功率高的任务 → 减少采样数
- 省下算力给困难任务
- 效果：相同算力预算下效率提升

**2. Dynamic Trajectory Length**
- 每个任务的最大步数基于历史成功轨迹长度动态设定
- 非全局固定（避免简单任务浪费步数）

**3. High-Entropy Step Selection**
- 只对高熵 step 计算 loss
- 跳过模型已确定的 trivial step
- 效果：训练信号更集中

**4. Distribution Alignment**
- 截断重要性采样修正 rollout policy 与 train policy 的分布偏移
- 保证 near on-policy 训练

**底部架构**：四模块解耦异步 — Env Cluster (K8s) / Rollout (vLLM) / Data Manager (MySQL) / Trainer (FSDP verl)

---

## Slide 32 — 章节封面：环境与基建

**标题**：Part III — 环境与基建

**引言（大字）**："2,000-4,000 并发环境是做 RL 的入场门票。"

---

## Slide 33 — 环境规模与三层架构

**标题**：环境需求与三层架构

**上半部分 — 规模需求**：

| 阶段 | 并发规模 | 参考 |
|------|---------|------|
| 数据采集 | 50-100 VM | 各工作标配 |
| Online RL | 2,000-4,000 并发 | EvoCUA, Computer-RL |

**下半部分 — 三层架构图**：

Layer 1 — 真实 VM 采集环境
- Win11 VM × 30 / macOS VM × 10 / Ubuntu VM × 10
- 截图 + A11y 提取 + 动作录制

Layer 2 — RL 沙盒（Docker/VM 快照池）
- 快速重置 < 10 秒
- 每个任务绑定 Verifier 脚本
- 分布式环境管理器

Layer 3 — 虚拟渲染环境
- Web 渲染的虚拟桌面应用（Mobile-Agent-v3.5）
- 状态完全可控，Verifier 天然精确
- 适用 Office 类 / 表单 / 设置

---

## Slide 34 — API-GUI Paradigm

**标题**：统一动作空间：API-GUI Paradigm（Computer-RL）

**核心思路**：模型输出 Python 代码，统一 GUI 操作与 API 调用

**代码示例**：

```python
# GUI Primitive（跨平台统一）
click(x=520, y=340)
type_text(text="Hello World")
hotkey("ctrl", "s")
scroll(direction="down", amount=3)
drag(start=(100, 200), end=(300, 400))

# Application-Specific API（按活跃窗口动态加载）
spreadsheet.set_cell("A1", "Revenue")
terminal.run_command("ls -la")
browser.navigate("https://example.com")
```

**三大优势**：
1. 支持组合操作、条件判断、循环
2. 复用 LLM 预训练的代码生成能力
3. GUI 与 API 在同一代码块中无缝混合

**动态加载机制**：检测活跃窗口 → 加载对应 API 定义注入 System Prompt → 减少 context 压力

---

## Slide 35 — A11y 对比 + Verifier 难度

**标题**：跨平台 A11y 与 Verifier 构建

**左侧 — A11y 工具链**：

| 平台 | 协议 | Python 工具 | 成熟度 |
|------|------|------------|--------|
| Windows | UIA | pywinauto | 高 |
| macOS | AXUIElement | macapptree + PyXA | 中 |
| Linux | AT-SPI2 | pyatspi2 | 中低 |

经验：Mano 用 A11y + OmniParse 混合最稳健 / Computer-RL 证明纯视觉也可行

**右侧 — Verifier 构建难度**：

| 应用类型 | 难度 | 方式 |
|---------|------|------|
| 文件管理 | 低 | 文件系统状态检查 |
| 终端 | 低 | 命令输出 / 文件变化 |
| 文本编辑 | 低 | 读取文件内容 |
| 浏览器 | 中 | URL + DOM 状态 |
| Office | 中 | 文档结构解析 |
| 系统设置 | 中 | 读取配置值 |
| 图像编辑 | 高 | 像素比对 |

---

## Slide 36 — 开源数据集全景

**标题**：开源数据集全景（33 个）

**四列分类表**：

| 用途 | 数据集 | 规模 | 可用性 |
|------|--------|------|--------|
| **Grounding** | OS-ATLAS | 13M+ | 充足 |
| | GroundCUA | 3.56M | 充足 |
| | Jedi | 4M | 充足 |
| **轨迹 SFT** | OpenCUA | 22K traj, 3 OS | 核心 |
| | GUI-360° | 1.2M steps | Win only |
| | ScaleCUA | 大规模, 6 OS | 核心 |
| **Benchmark** | OSWorld | 369 tasks, 3 OS | 主评测 |
| | ScreenSpot-Pro | 1,590 | Grounding 评测 |
| | WAA | 154 tasks | Windows 评测 |
| **Mobile** | AITW | 715K ep | 需去重迁移 |
| | Rico | 66K screens | 经典 |

---

## Slide 37 — 跨平台数据缺口

**标题**：跨平台数据缺口热力图

**热力图矩阵**（绿=充足，黄=中等，红=稀缺，深红=极缺）：

|  | Windows | macOS | Linux | Web | Mobile |
|--|---------|-------|-------|-----|--------|
| Grounding | 充足 | 中等 | 稀缺 | 充足 | 充足 |
| 轨迹 | 充足 | 稀缺 | 稀缺 | 充足 | 充足 |
| A11y 标注 | 稀缺 | 稀缺 | 极缺 | 中等 | 充足 |
| 代码级动作 | 稀缺 | 极缺 | 极缺 | 稀缺 | 极缺 |
| 端到端 | 中等 | 极缺 | 极缺 | 中等 | 充足 |

**底部结论**：核心缺口 = macOS/Linux 轨迹 + 代码级动作 + A11y 标注 + 失败/自纠正轨迹

---

## Slide 38 — 章节封面：核心发现

**标题**：Part IV — 五大核心发现

**副标题**：从 7 个工作中提炼的方法论

---

## Slide 39 — 发现 1

**标题（大字）**：发现 1：数据闭环 > 模型架构

**一句话**：飞轮效率决定迭代速度。模型既是学习者，也是数据的生产者。

**支撑证据**：
- UI-TARS-2：高质量 → SFT / 低质量 → CT 的自动路由
- Computer-RL：Entropulse 回收成功 rollout 打破性能天花板
- Mano：RL 成功轨迹 + LLM 修正有错轨迹 → 回注 SFT

---

## Slide 40 — 发现 2

**标题（大字）**：发现 2：RL 瓶颈在环境和 Verifier，不在算法

**一句话**：GRPO / PPO / MRPO 差异不大。真正决定 RL 上限的是基建规模。

**支撑证据**：
- 环境并发：EvoCUA 2,000-4,000 / Computer-RL 数千
- Verifier 数量：Computer-RL ~8,000 个可编程 Verifier
- EvoCUA："最重视 scaling，沙盒还有 verifier"

---

## Slide 41 — 发现 3

**标题（大字）**：发现 3：Cold-start 质量 >> 数量

**一句话**：180K 步或 5K 轨迹即可完成有效 cold-start，前提是每条都经过验证。

**支撑证据**：
- Computer-RL：180K 步，全部通过 Rule-based Verifier
- EvoCUA：5K 轨迹，每个 query 4-5 条正确轨迹 → OSWorld 51 分
- Computer-RL Model Pool：多个强模型作 Teacher，按难度分层采集

---

## Slide 42 — 发现 4

**标题（大字）**：发现 4：训练信号应集中在关键步骤

**一句话**：不是所有步骤同等重要。关键步骤 DPO 比全轨迹 DPO 更高效。

**支撑证据**：
- EvoCUA：Offline DPO 对关键步骤学习 → 单此一项 +4 分
- EvoCUA 冷启动：50% 通用 + 35% 普通 + 15% 关键步骤
- DART-GUI：High-Entropy Step Selection，只对高熵步骤算 loss

---

## Slide 43 — 发现 5

**标题（大字）**：发现 5：统一动作空间是待解决的根本问题

**一句话**：Mobile/Web/Desktop 的 action space 仍然割裂，这限制了跨平台泛化。

**支撑证据**：
- Computer-RL 的 API-GUI Paradigm 是当前最优解（Python 代码统一）
- Mobile-Agent-v3.5 在 CoT 层面做了统一尝试
- 但更根本的统一动作空间设计仍未出现

---

## Slide 44 — 章节封面：我们的方案

**标题**：Part V — 我们的技术路线

**副标题**：基于调研结论推导

---

## Slide 45 — 训练路线

**标题**：我们的训练路线

**流程图**：

```
Grounding 预训练 ──→ SFT ──→ Online GRPO ──→ Entropulse ──→ GRPO ──→ Offline DPO ──→ 参数插值
   15-20M             500K traj    ↑                                                    ↑
                                   │                                                    │
                             2000-4000 并发                                     Vertical Agents
                             5000-10000 Verifier                               Win/macOS/Linux
```

**关键决策**：
- 基座：Qwen 系列 (7B 先行验证 → 72B / 300B MoE)
- 动作空间：API-GUI Paradigm（Python 代码输出）
- RL 算法：GRPO → Entropulse → GRPO → DPO

---

## Slide 46 — 四条数据管线

**标题**：四条并行数据管线

**四列卡片**：

**管线 A：逆向合成（OS-Genesis）**
- Agent 在 VM 中自由探索
- 记录 (截图, A11y, 动作) 三元组
- LLM 反向生成任务指令
- 产出：~1,000-5,000 步/VM/天

**管线 B：教程驱动（AgentTrek）**
- 爬取软件教程（Microsoft Learn, ArchWiki, YouTube）
- LLM 转为结构化步骤
- VLM Agent 按教程执行 + 录制
- 产出：取决于教程量，可爬数万篇

**管线 C：任务模板**
- 50 应用 × 10 功能 × 20 变体 = 10,000 基础任务
- LLM 生成变体 + Agent 执行
- 自动验证任务完成

**管线 D：人机协作**
- 人工执行复杂多步任务
- LLM 生成 thought/reasoning
- 目标：~10K 高质量轨迹（兜底长尾）

---

## Slide 47 — Timeline

**标题**：执行 Timeline

**甘特图数据**：

| 阶段 | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| 基建 (VM + 工具链 + 数据清洗) | ██ | ██ | | | | | | | | |
| Grounding 预训练 | | ██ | ██ | ██ | | | | | | |
| SFT (数据采集 + 训练) | | | ██ | ██ | ██ | | | | | |
| RL (环境 + Verifier + 训练) | | | | ██ | ██ | ██ | ██ | | | |
| Scale + 融合 | | | | | | ██ | ██ | ██ | ██ | ██ |

**里程碑**：
- M2：Zero-shot baseline
- M4：ScreenSpot-Pro Top-3
- M5：OSWorld >15% SR
- M7：OSWorld >30% SR

---

## Slide 48 — 风险与对策

**标题**：风险矩阵

**表格**：

| 风险 | 影响 | 对策 |
|------|------|------|
| macOS VM 成本高 | 高 | AWS Mac 预留 + 虚拟渲染降级 |
| 桌面 Verifier 构建困难 | 高 | 优先可编程应用 + LLM-as-Judge 兜底 |
| RL entropy collapse | 中 | Entropulse + entropy 实时监控 |
| OpenCUA 与 Qwen 不兼容 | 中 | RoPE 对齐 + 混合比例调优 |
| A11y 跨 OS 不一致 | 中 | 混合有/无 A11y 训练 |
| 统一动作空间设计 | 中 | 早期小规模验证 Code Action |
| 人工资源有限 | 低 | LLM 驱动为主，人工仅做质检 |

---

## Slide 49 — 结束页

**标题**：Thank You

**副标题**：Q&A & 开放讨论

**预备讨论方向**：
1. GUI/Vision-based vs API-based 的边界在哪里？
2. Verifier 如何 scale 到万级？
3. macOS 虚拟化的工程可行性？
4. 除 Entropulse 外还有哪些解决 entropy collapse 的方案？
