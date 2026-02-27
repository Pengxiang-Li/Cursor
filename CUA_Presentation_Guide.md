# CUA 调研汇报：讲解流程与 PPT 制作指南

> **听众画像**：资深 CUA 研究员，对大模型训练有深厚理解
> **核心目标**：分析现有工作，提炼方法论——"他们怎么做的，为什么这么做，我们该怎么做"
> **建议时长**：60–90 分钟（含讨论）

---

## 整体叙事主线

```
问题定义 → 技术全景 → 三大支柱深度拆解（数据 / 训练 / 基建）→ 方法论提炼 → 我们的方案
```

核心论点：**CUA 的竞争本质上是"数据闭环 × 环境规模 × Verifier 质量"的系统工程竞争，而非单一模型架构创新。**

---

## 第一部分：开场与问题定义（5 分钟）

### 讲什么
- CUA 的定义与当前产业位置：从 ChatBot 到 Computer Use Agent 的范式跃迁
- 为什么现在是关键窗口期：OpenAI Operator、Anthropic Computer Use、字节 UI-TARS-2、Google Mariner 密集发布
- 本次调研的范围与深度：覆盖 7 个核心工作 + 33 个数据集 + 3 个 OS 平台

### 怎么讲
开门见山，不做过多铺垫。一句话点明：**"这次调研的核心发现是——CUA 的胜负手不在模型架构，而在数据工程和环境基建的系统化程度。"** 给听众一个清晰的预期。

### PPT 建议
- **Slide 1**：标题页 "CUA 调研：从已有工作看方法论"
- **Slide 2**：一张时间线图，标出 2024-2025 各主要 CUA 工作的发布节点
- **Slide 3**：调研范围总览表（7 个核心工作 + 关键维度矩阵）

---

## 第二部分：调研工作全景速览（10 分钟）

### 讲什么
快速过一遍 7 个核心工作的定位和亮点，让听众建立全局 mental map，后续深入时不会迷失：

| 工作 | 基座 | 平台 | 最大亮点 |
|------|------|------|----------|
| **UI-TARS-2** | Seed-thinking-1.6 | 全平台 | Data Flywheel + 参数插值融合 + Generative ORM |
| **Computer-RL** | GLM-4V | Desktop | Entropulse（SFT 恢复 entropy）+ API-GUI Paradigm |
| **Mobile-Agent-v3.5** | - | 全平台 | DAG 自动化探索 + Hard Grounding Synthesis + MRPO |
| **Mano** | UI-TARS-1.5-7B | Desktop/Web | Action Desp（+2.8）+ 闭环数据循环 |
| **EvoCUA** | OpenCUA/Qwen3VL | Desktop | 关键步骤训练 + 少数据高效 RL（5K traj → 51分）|
| **AgentCPM** | MiniCPM-V 8B | Mobile | 12M Grounding 预训练 + 真机录制 + 去重管线 |
| **DART-GUI** | UI-TARS-1.5-7B | Desktop | 四个自适应数据策略 + 解耦异步架构 |

### 怎么讲
用一张大表快速过，每个工作只讲一句话定位 + 一个最独特的贡献。**不展开细节**，告诉听众："接下来我会按三大支柱——数据、训练、基建——横向对比这些工作。"

### PPT 建议
- **Slide 4**：7 个工作的一页纵览表（如上表，加颜色标注各自最大亮点）
- **Slide 5**：一张雷达图或矩阵图，展示各工作在"数据规模 / 训练深度 / 平台覆盖 / RL 规模 / 开源程度"五个维度的对比

---

## 第三部分：数据工程方法论（20 分钟）⭐ 核心

这是整个汇报最重要的部分。听众是资深研究员，对"数据怎么搞"最为关注。

### 3.1 Grounding 数据——视觉定位的基础（7 分钟）

#### 讲什么
**核心论点**：Grounding 是 CUA 的基础瓶颈，ScreenSpot-Pro SOTA 仅 18.9%，桌面端比移动端更难。

**方法论提炼**——四种 Grounding 数据构造范式：

| 范式 | 代表工作 | 方法 | 规模 |
|------|----------|------|------|
| **大规模自动标注** | AgentCPM | A11y Tree + View Hierarchy 自动提取 → OCR/Widget 定位任务 | 12M（含 50% 通用数据正则化） |
| **高难度合成** | Mobile-Agent-v3.5 | MLLM 渲染专业软件截图 + 多窗口重组 | 数十万级 |
| **负样本增强** | Mobile-Agent-v3.5 | 图像-Query 随机组合 + 多模型共识过滤 | 正:负 ≈ 1:10 |
| **探索副产物** | Mobile-Agent-v3.5 | 从 OS-Genesis 探索轨迹中用 Critic 模型挖掘 grounding 对 | 百万级（零额外成本）|

**关键洞察**：
- AgentCPM 混合 50% 通用多模态数据防止视觉模块过拟合——这对基座能力较弱的模型尤其重要
- 负样本（Infeasible）训练对拒答和纠错能力至关重要
- 开源数据已有 OS-ATLAS（13M+）、GroundCUA（3.56M）、Jedi（4M），Grounding 预训练数据相对充足

#### 怎么讲
先展示 ScreenSpot-Pro 的现状数据说明"Grounding 还很难"，然后逐个范式讲，每个范式用一张流程图说明。重点对比 AgentCPM 的"大力出奇迹"和 Mobile-Agent-v3.5 的"精巧合成"两条路线。

#### PPT 建议
- **Slide 6**：ScreenSpot-Pro 当前 SOTA 数据 + "桌面端 Grounding 为何更难"的三点说明（元素更密、分辨率更高、专业软件 UI 复杂）
- **Slide 7**：四种 Grounding 数据范式对比表
- **Slide 8**：Mobile-Agent-v3.5 Hard Grounding Synthesis 流程图
- **Slide 9**：开源 Grounding 数据集一览（OS-ATLAS / GroundCUA / Jedi / GUICourse）

---

### 3.2 轨迹数据——Agent 能力的燃料（8 分钟）

#### 讲什么
**核心论点**：轨迹数据的构造有四种范式，它们的 trade-off 是"规模 vs 质量 vs 成本"的三角博弈。

**方法论提炼**——四种轨迹数据采集范式：

| 范式 | 代表工作 | 特点 | 适用阶段 |
|------|----------|------|----------|
| **DAG 自动化探索** | Mobile-Agent-v3.5 | 人工定义状态图 → Agent 执行 → Checkpoint 验证 → 失败截断重写 | Cold-start SFT |
| **DFS 自由探索** | Mano (Explorer) | LLM 生成功能目标 → DFS 深度 10 → Claude 质检 | SFT 主力（70%）|
| **虚拟环境生成** | Mobile-Agent-v3.5 | Web 渲染虚拟桌面应用 → RPA 脚本精准生成长轨迹 | 精确长轨迹 |
| **人机协作（In-policy）** | UI-TARS-2 | 模型 Rollout → 人工 accept/override → On-policy 数据 | 高质量对齐 |

**关键洞察**：
- **Cold-start 质量 > 数量**：Computer-RL 仅 180K 步、EvoCUA 仅 5K 轨迹即完成可用 cold-start，但全部通过 Verifier 验证
- **每个 Query 多条轨迹 > 更多 Query**（EvoCUA 实验确认）：同一任务的不同解法提供更好的 policy space 覆盖
- **通用数据混合防 Mode Collapse**：AgentCPM 混 50%，Qwen 基座可降至 25-30%
- **开源数据的已知坑**：OpenCUA 与 Qwen pattern 差异大（entropy 高，需 RoPE 对齐）；AITW 冗余高需 ResNet-50 去重（保留 ~40%）

#### 怎么讲
用一张 2×2 矩阵（横轴：自动化程度，纵轴：数据质量）定位四种范式。然后重点讲两个反直觉的发现：(1) 少量高质量数据比大量低质量数据更有效，(2) 同一 query 多轨迹比更多 query 更有效。

#### PPT 建议
- **Slide 10**：四种轨迹采集范式的 2×2 矩阵图
- **Slide 11**：Mobile-Agent-v3.5 DAG 探索 + 失败截断重写的流程图
- **Slide 12**：Mano Explorer DFS 管线全流程图
- **Slide 13**：Cold-start 数据量对比表（Computer-RL 180K 步 / EvoCUA 5K 轨迹 / AgentCPM 55K 轨迹）
- **Slide 14**：开源轨迹数据集规模速览 + 已知问题

---

### 3.3 数据闭环——飞轮效应（5 分钟）

#### 讲什么
**核心论点**：顶级工作都在做数据飞轮，模型既是学习者也是数据生产者。

**方法论提炼**——数据回收的四种路由：

```
RL Rollout 产出轨迹
     │
     ├─ 高质量成功轨迹 ────────→ SFT 数据集          (UI-TARS-2, Mano)
     ├─ 低质量/失败轨迹 ────────→ CT 数据集           (UI-TARS-2)
     ├─ 成功但中间有错的轨迹 ───→ LLM 修正 → SFT     (Mano)
     └─ 所有成功 Rollout 集合 ──→ Entropy 恢复 SFT   (Computer-RL)
```

**关键对比**：
- UI-TARS-2 的 Data Flywheel：最完整的闭环，高质量 → SFT，低质量 → CT
- Computer-RL 的 Entropulse 数据回收：收集不同阶段 policy 的成功 rollout → SFT 恢复 entropy
- Mano 的闭环：成功但有错 → LLM 草稿 + 人类修正 → 再注入 SFT

#### 怎么讲
画一个飞轮图，展示"训练 → Rollout → 验证 → 数据回收 → 训练"的循环。重点强调："**数据闭环的设计质量，决定了模型迭代的速度。**"

#### PPT 建议
- **Slide 15**：数据飞轮循环图（中心主循环 + 四条分支路由）
- **Slide 16**：三家数据回收策略对比表

---

## 第四部分：训练方法论（20 分钟）⭐ 核心

### 4.1 训练流程全景（5 分钟）

#### 讲什么
**核心论点**：所有顶级工作都遵循"多阶段渐进式训练"范式，但阶段数和细节各有差异。

**方法论提炼**——统一训练流水线：

```
[CT] → [Grounding 预训练] → [SFT] → [Online RL] → [Entropy 恢复] → [Online RL] → [Offline DPO] → [参数插值]
 可选    AgentCPM/UI-TARS-2   所有      所有          Computer-RL      所有          EvoCUA         UI-TARS-2
```

各工作的训练阶段对比：

| 工作 | CT | Grounding | SFT | Online RL | Entropulse | Offline DPO | 参数插值 |
|------|:--:|:---------:|:---:|:---------:|:----------:|:-----------:|:--------:|
| UI-TARS-2 | ✅ | ✅ | ✅ | ✅ PPO | ✗ | ✗ | ✅ |
| Computer-RL | ✗ | ✗ | ✅ BC | ✅ GRPO | ✅ | ✗ | ✗ |
| Mobile-Agent-v3.5 | ✅ | ✅ | ✅ | ✅ MRPO | ✗ | ✗ | ✗ |
| Mano | ✗ | ✗ | ✅ | ✅ | ✗ | ✅ | ✗ |
| EvoCUA | ✗ | ✗ | ✅ | ✅ RFT | ✗ | ✅ | ✗ |
| AgentCPM | ✗ | ✅ 12M | ✅ | ✅ GRPO | ✗ | ✗ | ✗ |
| DART-GUI | ✗ | ✗ | ✗（用已有SFT模型）| ✅ GRPO | ✗ | ✗ | ✗ |

#### 怎么讲
用一张大表横向对比，快速建立全局认知。然后说："接下来我按 SFT 和 RL 两个核心阶段分别深入。"

#### PPT 建议
- **Slide 17**：统一流水线图（横向箭头流程，标注各工作覆盖的阶段）
- **Slide 18**：训练阶段对比矩阵表（如上表）

---

### 4.2 SFT 阶段方法论（5 分钟）

#### 讲什么

**方法论提炼**——SFT 阶段的五个关键技巧：

| 技巧 | 来源 | 效果 | 原理 |
|------|------|------|------|
| **Action Description** | Mano | +2.8分 | Thought 和 Action 之间加一句话摘要，显著引导动作生成 |
| **In-policy 标注** | UI-TARS-2 | 保持分布一致 | 模型 rollout → 人工 accept/override → 训练数据 on-policy |
| **历史帧策略** | Mano | 最优平衡 | 前 2 帧截图 + 全部历史文本摘要 |
| **CoT Warm-up** | AgentCPM | 启动推理能力 | SFT 早期混入少量纯 CoT 数据 |
| **世界模型监督** | Mobile-Agent-v3.5 | 提升前瞻性 | 训练预测"动作后界面如何变化" |

**输出格式对比**：

| 格式 | 工作 | 结构 |
|------|------|------|
| 五段式 | Mobile-Agent-v3.5 | Observation → Memory → Reflection & Progress → Thought → Conclusion |
| 三段式 | Mano | Thought → Action Desp → Action |
| 代码式 | Computer-RL | Thought → Python Code Block |

**数据配比经验**：
- Mano: 70% 自动采集 + 10% 开源 + 20% 人工
- AgentCPM: 50% 轨迹 + 50% 通用（因为基座弱）
- 建议（Qwen 基座）：50% 自动 + 15% 开源 + 10% 人工 + 25% 通用

#### 怎么讲
先讲 Mano 的 Action Description 这个小而美的发现（一句话 +2.8），引起兴趣。然后逐个技巧展开，每个给一个具体例子。最后对比输出格式，讨论 trade-off。

#### PPT 建议
- **Slide 19**：Mano Action Description 具体示例（用 `H2O` 选中数字 `2` 的例子）
- **Slide 20**：五个 SFT 关键技巧对比表
- **Slide 21**：三种输出格式对比 + 各自适用场景
- **Slide 22**：数据配比经验汇总

---

### 4.3 RL 阶段方法论（10 分钟）⭐ 最核心

#### 讲什么
**核心论点**：RL 是性能跃迁的关键，但瓶颈不在算法，在于环境规模和 Verifier 质量。

**4.3.1 算法选择**

| 算法 | 使用者 | 优势 | 劣势 |
|------|--------|------|------|
| **Step-level GRPO** | Computer-RL, AgentCPM, DART-GUI | 无 Value Network，显存低 | 长序列 advantage 估计不稳定 |
| **PPO** | UI-TARS-2 | 更稳定 | 需额外 Value Model，显存高 |
| **MRPO** | Mobile-Agent-v3.5 | 解决跨平台梯度冲突 | 需按平台交替训练 |
| **Offline DPO** | EvoCUA, Mano | 无需环境交互 | 无法探索新策略 |

**4.3.2 Reward 设计——分层体系**

| 层级 | 方法 | 代表工作 | 精度 | 成本 |
|------|------|----------|------|------|
| Tier 1 | Rule-based Verifier | Computer-RL（~8000个）| 最高 | 构建成本高 |
| Tier 2 | JS 脚本查询 runtime | UI-TARS-2（游戏场景）| 高 | 需可编程环境 |
| Tier 3 | LLM-as-Judge | UI-TARS-2, EvoCUA | 中 | 灵活但不够精确 |
| Tier 4 | Generative ORM | UI-TARS-2 | 中 | 需额外训练 ORM 模型 |

**4.3.3 三个关键 RL 创新**

**创新 1：Entropulse（Computer-RL）**
- 问题：RL 训练 ~180 steps 后 entropy collapse，性能触顶
- 方案：收集 RL Phase 1 所有成功 rollout（不同阶段 policy 生成，天然多样）→ SFT 一轮 → 恢复 entropy → 继续 RL
- 效果：突破性能天花板，达到 SOTA
- 本质：用"数据多样性"对抗"策略坍缩"

**创新 2：关键步骤训练（EvoCUA）**
- Cold-start 配比：50% 通用 + 35% 普通步骤 + **15% 关键步骤**
- 关键步骤 = 对任务成败有决定性影响的步骤（不可逆操作、分支决策、最终提交）
- Offline DPO 专门对关键步骤学习：单此一项 +4 分
- 意义：在数据有限时，将训练信号集中在最关键的地方

**创新 3：跨平台梯度冲突解决（Mobile-Agent-v3.5 & UI-TARS-2）**
- 问题：手机/PC/Web 混合训练导致梯度 Tug-of-war
- 方案 A（MRPO）：交替多平台优化，周期性迭代
- 方案 B（UI-TARS-2）：分别训练 Vertical Agents → 参数插值 $\theta^{(merge)} = \sum \alpha_k \theta^{(k)}$
- 方案 B 的理论基础：模型在参数空间内的线性连接特性（Mode-connected）

**4.3.4 DART-GUI 的四个自适应策略**（工程亮点）
1. Dynamic Rollout Number：按任务成功率动态调采样数
2. Dynamic Trajectory Length：按历史成功轨迹长度动态设最大步数
3. High-Entropy Step Selection：只对高熵步骤算 loss
4. Distribution Alignment：截断重要性采样修正分布偏移

#### 怎么讲
这部分最关键，建议：
1. 先用 30 秒给出一个 provocative statement："**RL 的瓶颈从来不是算法，而是你能同时跑多少个环境、你的 Verifier 有多精确。**"
2. 然后按 算法选择 → Reward 分层 → 三大创新 → 工程策略 的顺序讲
3. Entropulse 部分画一个 entropy 变化曲线图（下降 → SFT 恢复 → 再下降 → 性能突破）
4. 关键步骤训练用一个具体例子说明什么是"关键步骤"

#### PPT 建议
- **Slide 23**：RL 算法选择对比表
- **Slide 24**：Reward 分层设计体系图
- **Slide 25**：Entropulse 原理图（entropy 曲线 + 数据流向）—— **这是本汇报最重要的一张图**
- **Slide 26**：关键步骤训练——什么是关键步骤 + EvoCUA 效果数据
- **Slide 27**：跨平台梯度冲突——MRPO vs 参数插值两种方案对比
- **Slide 28**：DART-GUI 四个自适应策略速览

---

## 第五部分：环境与基建方法论（10 分钟）

### 讲什么

**核心论点**：CUA 的工程化程度远超传统 NLP 任务。环境、Verifier、分布式架构是隐性门槛。

**5.1 环境规模对比**

| 阶段 | 需求 | 参考 |
|------|------|------|
| 数据采集 | 50-100 VM | 标配 |
| Online RL | **2000-4000 并发** | EvoCUA, Computer-RL |

**5.2 三层环境架构**
- Layer 1：真实 VM 采集环境（Win/macOS/Linux）
- Layer 2：Docker/VM 快照池 RL 沙盒（快速重置 <10s）
- Layer 3：虚拟渲染环境（Mobile-Agent-v3.5：Web 渲染虚拟桌面应用，Verifier 天然精确）

**5.3 Action Space 设计**
- 当前痛点：Mobile/Web/Desktop 动作空间割裂
- Computer-RL 方案（API-GUI Paradigm）：统一为 Python 代码输出，GUI primitive + Application-specific API 混合
- 优势：复用 LLM 代码能力 + 支持组合操作/条件判断/循环 + GUI 与 API 无缝混合

**5.4 跨平台 A11y 工具链**

| 平台 | 工具 | 成熟度 |
|------|------|--------|
| Windows | pywinauto + UIA | 高 |
| macOS | macapptree + AX API | 中 |
| Linux | pyatspi2 + AT-SPI | 中低 |

重要经验：Mano 用 A11y + OmniParse 混合最稳健；Computer-RL 证明纯视觉也可行。

### 怎么讲
强调一个观点："**你能不能做 RL，取决于你能同时启动多少个环境。2000-4000 并发是门槛。**" 然后快速过环境架构。Action Space 部分可以展示 Computer-RL 的 Python 代码示例，直观有力。

### PPT 建议
- **Slide 29**：环境规模需求对比 + 三层架构图
- **Slide 30**：Computer-RL API-GUI Paradigm 代码示例
- **Slide 31**：跨平台 A11y 对比 + Verifier 构建难度矩阵

---

## 第六部分：数据集全景（5 分钟，可选快速过）

### 讲什么
快速展示开源数据集的全貌，重点标注哪些可用、哪些有坑。

**按用途分类**：

| 用途 | 代表数据集 | 可用性 |
|------|-----------|--------|
| Grounding 预训练 | OS-ATLAS (13M+), GroundCUA (3.56M), Jedi (4M) | 充足 |
| 轨迹 SFT | OpenCUA (22K traj), GUI-360° (1.2M steps), ScaleCUA | 部分充足 |
| Benchmark 评测 | OSWorld (369), ScreenSpot-Pro (1.59K), WAA (154) | 充足 |
| Mobile 参考 | AITW (715K), Rico (66K screens), AMEX (104K) | 充足但需迁移 |

**数据缺口矩阵**：

|  | Win | macOS | Linux |
|--|-----|-------|-------|
| Grounding | 充足 | 中等 | 稀缺 |
| 轨迹 | 充足 | 稀缺 | 稀缺 |
| A11y | 稀缺 | 稀缺 | 极缺 |
| 代码级动作 | 稀缺 | 极缺 | 极缺 |

### 怎么讲
快速过两张表，重点强调 **macOS/Linux 的数据极度匮乏** 和 **代码级动作数据几乎为零**。不需要逐个数据集讲，重点讲结论。

### PPT 建议
- **Slide 32**：开源数据集按用途分类总览表（颜色标注充足/中等/稀缺）
- **Slide 33**：跨平台数据缺口热力图矩阵

---

## 第七部分：方法论总结——五大核心发现（5 分钟）

### 讲什么
将前面所有分析收敛为五条方法论，这是听众带走的核心 takeaway。

**发现 1：数据闭环 > 模型架构**
> 飞轮效率决定迭代速度。UI-TARS-2、Computer-RL、Mano 都在做"模型产出 → 验证 → 回收 → 再训练"。

**发现 2：RL 瓶颈在环境和 Verifier，不在算法**
> GRPO / PPO / MRPO 差异不大。真正决定 RL 上限的是：你能并发跑多少环境（2000-4000）、你的 Verifier 有多精确（Computer-RL 8000 个）。

**发现 3：Cold-start 质量 >> 数量**
> Computer-RL 180K 步、EvoCUA 5K 轨迹即可完成有效 cold-start。条件：Verifier 验证 + 多模型 Teacher + 按难度分层。

**发现 4：训练信号应集中在关键步骤**
> EvoCUA 的关键步骤 DPO (+4分) 说明：不是所有步骤同等重要。对任务成败有决定性影响的步骤值得额外关注。

**发现 5：统一动作空间是待解决的根本问题**
> Mobile/Web/Desktop 仍割裂。Computer-RL 的 API-GUI Paradigm（Python 代码统一）是当前最优解，但远未完善。

### 怎么讲
每条发现用一句话总结 + 一个支撑例子，不展开。可以考虑让每条发现对应一页 slide，制造节奏感。

### PPT 建议
- **Slide 34-38**：每条发现一页，大字标题 + 一行核心论据 + 支撑工作 logo

---

## 第八部分：我们的方案概要（10 分钟，可选）

### 讲什么
基于调研结论，简要勾勒我们的技术路线。

**训练路线**：
```
Grounding 预训练 (15-20M) → SFT (500K traj) → Online GRPO → Entropulse → GRPO → Offline DPO → 参数插值
```

**数据管线**（四条并行）：
1. OS-Genesis 逆向合成（重点补 macOS/Linux）
2. 教程驱动合成（爬取软件教程 → 结构化 → Agent 执行）
3. 任务模板批量生成（50 应用 × 10 功能 × 20 变体）
4. 人机协作标注（兜底长尾）

**关键决策**：
- 基座：Qwen 系列
- 动作空间：API-GUI Paradigm（Python 代码输出）
- Verifier：Rule-based（优先）→ Screenshot-diff → LLM-as-Judge → Generative ORM
- 跨平台融合：先 Vertical Agents + 参数插值，再对比 MRPO

**执行 Timeline**：
- M1-2：基建（VM 集群 + A11y 工具链 + 数据管线）
- M2-4：Grounding 预训练
- M3-5：SFT
- M4-7：RL
- M6-10：Scale + 融合

### 怎么讲
如果时间充裕，展开讲；如果时间紧，简要提一下框架即可。重点是："**我们的方案是基于这些调研结论推导出来的。**" 让听众感受到调研和方案之间的逻辑链条。

### PPT 建议
- **Slide 39**：我们的训练路线全流程图
- **Slide 40**：四条数据管线概览
- **Slide 41**：Timeline 甘特图
- **Slide 42**：风险矩阵（风险 + 对策）

---

## 第九部分：Q&A 与开放讨论（10-15 分钟）

### 预备问题与讨论方向
这些是资深听众可能追问的方向，提前准备好：

1. **"OpenClaw 这种东西出来了，效果还挺惊艳，GUI/vision-based 意义何在？"**
   - 准备回答：纯 API-based 方案覆盖不了无 API 的应用；视觉是通用性的保障；但 API-GUI 混合是趋势

2. **"Verifier 怎么 scale？8000 个 rule-based verifier 的构建成本？"**
   - 准备回答：Computer-RL 选了可编程应用先做；LLM-as-Judge 兜底；长期看 Generative ORM

3. **"macOS 虚拟化成本怎么解？"**
   - 准备回答：AWS Mac Dedicated Host + Tart/Anka + 虚拟渲染环境降级

4. **"Entropy collapse 除了 Entropulse 还有其他解法吗？"**
   - 准备回答：KL 约束、DPO 偏好对、数据多样性注入、model merge（EvoCUA 经验）

---

## PPT 模板结构总览

| 编号 | Slide 内容 | 对应部分 |
|------|-----------|---------|
| 1 | 标题页 | 开场 |
| 2 | CUA 工作时间线 | 第一部分 |
| 3 | 调研范围总览 | 第一部分 |
| 4 | 7 个核心工作纵览表 | 第二部分 |
| 5 | 五维雷达图对比 | 第二部分 |
| 6 | ScreenSpot-Pro 现状 + 桌面 Grounding 挑战 | 第三部分 3.1 |
| 7 | 四种 Grounding 数据范式 | 第三部分 3.1 |
| 8 | Hard Grounding Synthesis 流程图 | 第三部分 3.1 |
| 9 | 开源 Grounding 数据集一览 | 第三部分 3.1 |
| 10 | 四种轨迹采集范式 2×2 矩阵 | 第三部分 3.2 |
| 11 | DAG 探索流程图 | 第三部分 3.2 |
| 12 | Mano Explorer 全流程图 | 第三部分 3.2 |
| 13 | Cold-start 数据量对比 | 第三部分 3.2 |
| 14 | 开源轨迹数据集 + 已知问题 | 第三部分 3.2 |
| 15 | 数据飞轮循环图 | 第三部分 3.3 |
| 16 | 数据回收策略对比 | 第三部分 3.3 |
| 17 | 统一训练流水线图 | 第四部分 4.1 |
| 18 | 训练阶段对比矩阵 | 第四部分 4.1 |
| 19 | Mano Action Description 示例 | 第四部分 4.2 |
| 20 | SFT 五个关键技巧 | 第四部分 4.2 |
| 21 | 三种输出格式对比 | 第四部分 4.2 |
| 22 | 数据配比经验 | 第四部分 4.2 |
| 23 | RL 算法选择对比 | 第四部分 4.3 |
| 24 | Reward 分层设计 | 第四部分 4.3 |
| 25 | **Entropulse 原理图** ⭐ | 第四部分 4.3 |
| 26 | 关键步骤训练 | 第四部分 4.3 |
| 27 | 跨平台梯度冲突方案 | 第四部分 4.3 |
| 28 | DART-GUI 自适应策略 | 第四部分 4.3 |
| 29 | 环境架构 + 规模需求 | 第五部分 |
| 30 | API-GUI Paradigm 代码示例 | 第五部分 |
| 31 | A11y 对比 + Verifier 难度矩阵 | 第五部分 |
| 32 | 开源数据集分类总览 | 第六部分 |
| 33 | 跨平台数据缺口热力图 | 第六部分 |
| 34-38 | 五大核心发现（每条一页）| 第七部分 |
| 39 | 我们的训练路线 | 第八部分 |
| 40 | 四条数据管线 | 第八部分 |
| 41 | Timeline 甘特图 | 第八部分 |
| 42 | 风险矩阵 | 第八部分 |
| 43 | Thank you + Q&A | 结束 |

**总计 ~43 页，按 2 分钟/页，约 85 分钟（含讨论）。**

---

## 讲解风格建议

1. **不要逐个工作串讲**。资深听众会觉得枯燥。应该按主题（数据/训练/基建）横向对比，让听众看到共性和差异。

2. **每个 section 以一个"provocative statement"开头**。例如：
   - 数据部分："Cold-start 只需要 5000 条轨迹。"
   - RL 部分："RL 的瓶颈不是算法，是你能开多少台虚拟机。"
   - 基建部分："2000-4000 并发环境是入场门票。"

3. **用具体数字说话**。资深研究员对 "很多/很少" 不感兴趣，但对 "12M grounding 样本" "180K 步 cold-start" "8000 个 Verifier" 会有直觉反应。

4. **每个方法论配一个反直觉的发现**。例如：
   - "少量数据比大量数据更有效"（前提是 Verifier 验证）
   - "一个 Query 多条轨迹比更多 Query 有效"
   - "RL entropy 下降不是坏事，但需要主动恢复"

5. **留出讨论时间**。资深听众一定有很多想法要碰撞，15 分钟 Q&A 是最低保证。
