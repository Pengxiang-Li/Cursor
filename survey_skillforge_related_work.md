# SkillForge 相关工作调研报告

> 调研问题：
> 1. 目前有没有人做过类似的 idea？
> 2. 业界对这类 idea 在其他 topic 的态度是什么？
> 3. GUI 领域里有没有人做过类似的事情？做到了什么程度？

---

## 一、总体结论（先说答案）

**结论：这个方向有人在做，但关键的 gap 仍然存在——"RL-driven skill discovery for GUI agents" 这个交叉点几乎没有人做过。**

具体来说：

| 维度 | 现状 | 你的机会 |
|------|------|---------|
| 通用 RL 的 skill/option discovery | 经典研究方向，持续有顶会论文 | 成熟理论可借鉴 |
| LLM Agent 的 skill library | 2023 Voyager 开创，2026 SkillRL/MetaClaw 是最新 | 都是 **prompt-level / code-level skill**，不是 RL 训练出来的 |
| GUI Agent 的 skill abstraction | CUA-Skill (Microsoft) 和 WALT 是最相关的 | 它们是 **人工/LLM 预构建的 skill**，不是 agent 自己通过 RL 发现的 |
| GUI Agent × Hierarchical RL | HiPER, HiMAC, Co-EPG 做了层次化 RL | 它们的 "层次" 是 **plan vs. execute**，不是 **skill discovery + reuse** |
| **GUI Agent × RL-driven Skill Discovery** | **几乎空白** | **核心机会** |

---

## 二、通用 RL 领域的 Skill Discovery / Option Discovery

### 2.1 经典理论基础

- **Options Framework** (Sutton, Precup & Singh, 1999)：将 RL 的动作空间从 primitive actions 扩展到 temporally extended actions (options)，每个 option = (initiation set, policy, termination condition)。这是所有 skill discovery 工作的理论基础。

- **Option-Critic Architecture** (Bacon et al., 2017, AAAI)：端到端学习 options 的 policy 和 termination condition，不需要预定义 options。

### 2.2 最新进展（2024-2026）

| 工作 | 会议 | 核心贡献 |
|------|------|---------|
| **Autonomous Option Invention** | AAAI 2025 | 在 continual RL 中自动发明可迁移、可组合的 symbolic options |
| **OptionZero** | arXiv 2025.2 | 将 option network 集成到 MuZero，通过 self-play 发现 options，Atari 上 +131% |
| **HiMaCon** | NeurIPS 2025 | 从无标注多模态数据中自动发现层次化 manipulation concepts |
| **DEPS** | NeurIPS 2025 | 从专家演示中发现参数化技能，temporal variational inference |
| **OTA-V** | NeurIPS 2025 Spotlight | Option-aware temporal abstraction for offline goal-conditioned RL |
| **Factorized Skill Learning** | CoRL 2025 | 无监督 skill discovery + sim-to-real transfer for quadruped |

### 2.3 业界态度

**非常正面。** Skill/option discovery 是 RL 社区几十年的核心话题，每年 NeurIPS/ICML/ICLR 都有相关论文被接收，且近年来与 foundation model 的结合是明显的趋势。NeurIPS 2025 就有至少 3 篇 skill discovery 相关论文（其中 OTA-V 拿到了 Spotlight）。

**但要注意**：纯粹的 option discovery（没有结合新场景/新视角）已经很难发顶会了，**需要与具体应用场景（如 GUI Agent）深度结合才有竞争力。**

---

## 三、LLM/VLM Agent 领域的 Skill Library / Hierarchical RL

### 3.1 Skill Library 范式（Prompt-Level Skills）

| 工作 | 会议/时间 | 方法 | 技能形式 | 训练方式 |
|------|----------|------|---------|---------|
| **Voyager** | NeurIPS 2023 | Minecraft 中自动 curriculum + skill library | 可执行 JS 代码 | **无 RL，纯 LLM prompting** |
| **JARVIS-1** | T-PAMI 2024 | 多模态 memory-augmented agent | 经验记忆 | **无 RL，检索+规划** |
| **CREATOR/LATM** | EMNLP 2023 | LLM 自动创建 Python 工具 | Python 函数 | **无 RL，纯 LLM** |
| **SkillRL** | ICLR 2026 Workshop | 从轨迹中蒸馏 skill + recursive evolution | 文本化策略 heuristics | **有 RL（GRPO）** |
| **MetaClaw** | arXiv 2026.3 | 从失败轨迹合成 skill + cloud LoRA | 行为指令 + LoRA 权重 | **有 RL（PRM-RL）** |
| **HiMAC** | arXiv 2026.3 | Macro-level plan + micro-level execution | 子目标描述 | **有 RL（hierarchical GRPO）** |
| **EvoSkill** | arXiv 2026.3 | 从失败分析中 discover + refine skills | 结构化 skill folder | **无 RL，LLM evolution** |

### 3.2 关键观察

1. **Voyager 是开山之作**，但技能是 **代码形式**（Minecraft 的 JS 函数），且**完全不涉及 RL 训练**——技能是通过 LLM prompting + 自我验证获得的。

2. **SkillRL 是与你 idea 最相似的工作**：它确实做了 "RL + skill discovery + skill evolution"。但关键区别：
   - SkillRL 的 "skill" 是 **文本形式的策略 heuristics**（"先搜索产品，再比价"），不是可执行的 macro-action
   - SkillRL 只发了 **ICLR 2026 Workshop**，不是主会
   - SkillRL 的任务是 ALFWorld + WebShop（文本交互为主），**不涉及视觉 GUI 操作**

3. **MetaClaw 也很相关**：skill library + RL co-evolution + 实际部署。但：
   - MetaClaw 的 skill 也是 **文本行为指令**，不是参数化的 GUI macro-action
   - MetaClaw 的 RL 是 **LoRA fine-tuning**，不是 hierarchical RL with options
   - MetaClaw 刚出来（2026.3），没有顶会评审记录

4. **HiMAC 做了 hierarchical RL**，但它的 "macro" 是 **自然语言子目标**（"找到冰箱"），不是可复用的技能。每个任务的 macro-plan 都是从头生成的，没有技能库的概念。

### 3.3 业界态度

**趋势非常正面，但大多数工作都不涉及 RL 训练。** Voyager 在 NeurIPS 2023 获得了极高的影响力（4000+ 引用），证明 "agent + skill library" 的叙事非常吸引人。但后续工作大多沿用 "LLM prompting + 代码工具" 的路线，**真正用 RL 来发现和优化技能的工作极少**。这是一个明显的 gap。

SkillRL 只发到了 Workshop（可能说明 reviewer 认为 contribution 不够主会），但也可能是因为它的技能形式太 "soft"（文本 heuristics），缺乏形式化的技能表示和理论分析。

---

## 四、GUI Agent 领域的 Skill / Subroutine / Macro 相关工作

### 4.1 最直接相关的工作

#### 4.1.1 CUA-Skill (Microsoft, 2026.1) — ⚠️ 最强竞品

**核心方法**：人工 + LLM 为 17+ Windows 应用构建结构化技能库。每个 skill = (skill cell 捕获意图, parameterized execution graph 指定 GUI 操作, skill composition graph 定义组合方式)。Agent 通过 RAG 检索技能并执行。

**结果**：WindowsAgentArena 上 57.5% success rate (SOTA)。

**关键差异（你的机会）**：
- ❌ **技能不是自动发现的**——需要人工或 LLM 预先构建
- ❌ **技能不通过 RL 优化**——execution graph 是固定的
- ❌ **技能库不会随使用而演化**——静态库
- ❌ **没有 hierarchical RL**——planning 层不涉及 RL 训练

#### 4.1.2 WALT (Salesforce, ICLR 2026 Poster) — 相关但不同

**核心方法**：反向工程网站功能，生成确定性可调用工具（`search(query)`, `create(listing)` 等）。

**结果**：VisualWebArena 52.9%, WebArena 50.1%, 252 tools discovered on 139 real-world websites。

**关键差异**：
- WALT 的 "tool" 是 **网站自身暴露的 API/功能**，不是从 GUI 操作中抽象出的 skill
- WALT **仅适用于 Web**（利用了 HTML/DOM 结构），不能推广到桌面 GUI
- WALT **不涉及 RL 训练**

#### 4.1.3 ActionEngine (arXiv 2026.2) — 方向相关

**核心方法**：用 crawling agent 构建 GUI 的 state machine memory，然后 execution agent 合成完整的 Python 程序执行任务。

**结果**：WebArena Reddit 95% success rate，1.8 LLM calls/task（vs. 10.2 for reactive agents）。

**关键差异**：
- ActionEngine 的 "程序" 是 **per-task 生成的**，不是 reusable skill library
- **不涉及 RL 训练**——纯 LLM planning + 代码生成
- 但 state machine memory 的思路对 skill precondition/postcondition 建模有启发

#### 4.1.4 ReUseIt (UCSB + Microsoft, 2025.10) — 相关

**核心方法**：从 agent 成功/失败尝试中自动合成 reusable workflow。

**结果**：成功率从 24.2% 提升到 70.1%。

**关键差异**：
- Workflow 是从 **已有轨迹中提取的**，不是通过 RL exploration 发现的
- **不涉及 RL 训练**
- 但 "从成功和失败轨迹中提炼可复用模式" 的思路与 SkillForge 有相似之处

### 4.2 Hierarchical RL for GUI Agent（间接相关）

| 工作 | 方法 | "层次" 的含义 | RL 训练 | 可复用技能 |
|------|------|-------------|---------|----------|
| **HiPER** (arXiv 2026.2) | 高层 plan + 低层 execute | 子任务分解 | ✅ (hierarchical advantage) | ❌（每个任务重新规划） |
| **Co-EPG** (arXiv 2025.11) | Planning + Grounding 共进化 | Plan 模型 + Ground 模型 | ✅ (GRPO) | ❌ |
| **CES** (arXiv 2025.11) | Coordinator + Executor + State Tracker | 调度 + 执行 | ✅ (execution-feedback RL) | ❌ |
| **Hi-Agent** | 高层推理 + 低层动作 | Reasoning + Action | ✅ (foresight advantage) | ❌ |

**关键观察：现有的 hierarchical GUI RL 工作都在做 "plan-execute 分离"，没有一个做 "skill discovery + reuse"。**

### 4.3 GUI 领域 Skill 相关工作的完整图谱

```
                              GUI Agent Skill 相关工作
                                      |
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              人工/LLM预建         轨迹提取           RL训练
                    │                 │                 │
              ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
              │           │    │           │    │           │
          CUA-Skill   Anthropic  ReUseIt  UI-Mem  HiPER    Co-EPG
          (MS, 2026)  Skills   (UCSB,    (2026)  (2026)   (2025)
              │       (2025)    2025)       │       │        │
          手动构建      │     workflow     经验    plan/     plan/
          skill库    prompt    提炼      存储    execute  ground
              │      技能集      │         │       │        │
              │           │    │           │       │        │
              └─────┬─────┘    └─────┬─────┘       │        │
                    │                │              │        │
               不涉及RL          不涉及RL       有RL但      有RL但
               不自动发现        不是RL发现    无skill库   无skill库
                                                    │        │
                                                    └────┬───┘
                                                         │
                                                   SkillForge 要填的 GAP:
                                                   RL-driven discovery
                                                   + reusable skill library
                                                   + hierarchical execution
```

---

## 五、Gap 分析与机会

### 5.1 现有工作的核心局限

1. **CUA-Skill/Anthropic Skills 路线**：技能库是人工或 LLM 预构建的 → **不 scalable**，无法自动适应新应用、新 OS、新版本

2. **ReUseIt/Voyager 路线**：技能是从轨迹中提取或 LLM 生成的 → **没有通过 RL 优化**，技能的质量和适用范围缺乏保障

3. **HiMAC/HiPER 路线**：做了 hierarchical RL → **但 "高层" 是 per-task 的 plan，不是 reusable skill**，每个新任务都要重新规划

4. **SkillRL/MetaClaw 路线**：做了 RL + skill evolution → **但 skill 是文本 heuristics，不是 GUI 操作层面的 macro-action**，且不涉及视觉 GUI 场景

### 5.2 SkillForge 可以填的独特 Gap

**没有任何现有工作同时做到以下四点：**

| 维度 | 要求 | CUA-Skill | WALT | SkillRL | HiMAC | HiPER | SkillForge |
|------|------|-----------|------|---------|-------|-------|-----------|
| 自动技能发现 | data-driven | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| GUI 视觉操作 | screenshot-based | ✅ | ❌(Web DOM) | ❌(Text) | ❌(Text) | ✅ | ✅ |
| RL 训练优化 | end-to-end RL | ❌ | ❌ | ✅(弱) | ✅ | ✅ | ✅ |
| 可复用技能库 | skill library | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 技能动态演化 | evolving | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

---

## 六、风险评估与建议

### 6.1 主要风险

1. **SkillRL/MetaClaw 的存在**：虽然它们不是 GUI 场景，但 reviewer 可能认为 "RL + skill discovery for agents" 的 idea 已经被做了。**应对：强调 GUI 的独特挑战（视觉 grounding、不可逆操作、跨应用迁移），以及你的技能表示与它们本质不同（参数化 GUI macro-action vs. 文本 heuristics）。**

2. **CUA-Skill 的强基线**：微软的 CUA-Skill 在 WindowsAgentArena 上 57.5%，如果你自动发现的技能不如人工构建的好，narrative 会受质疑。**应对：可以考虑 "CUA-Skill 作为初始化 + RL-based evolution" 的混合路线，或者在 CUA-Skill 未覆盖的新应用上展示优势。**

3. **技能发现的质量控制**：自动发现的技能可能包含大量噪声。**应对：需要严格的 skill quality metrics 和 filtering pipeline。**

### 6.2 建议的差异化策略

1. **强调 "RL-discovered skills" vs. "LLM-constructed skills" 的本质区别**：
   - CUA-Skill 的技能是基于人类对应用的理解构建的 → 受限于人的认知
   - 你的技能是从大量 RL 交互中自动发现的 → 可能发现人类想不到的高效操作模式

2. **利用 Option Framework 的形式化**：
   - 给 skill 一个严格的数学定义：(initiation set I, parameterized policy π, termination condition β)
   - 这样可以利用 HRL 的理论分析（如 option-critic 的收敛性证明）
   - 这是 SkillRL/MetaClaw 等 "soft skill" 工作做不到的

3. **重点展示技能的迁移能力**：
   - 在 App A 上发现的 "保存文件" skill → 在 App B 上直接可用
   - 这是 CUA-Skill（per-app 手动构建）和 WALT（per-website 反向工程）都做不到的

4. **与 DART/ComputerRL 的基础设施结合**：
   - 利用 DART 的异步 RL 训练框架
   - Skill discovery 的计算开销可以通过异步并行化来解决
   - 这是你组的基础设施优势

---

## 七、参考文献索引

### 最直接相关（必须在论文中讨论）
1. CUA-Skill (Microsoft, 2026.1) — 人工构建 GUI 技能库
2. WALT (Salesforce, ICLR 2026) — Web agent 自动发现可调用工具
3. SkillRL (ICLR 2026 Workshop) — RL + 文本技能发现 + evolution
4. MetaClaw (arXiv 2026.3) — skill library + RL co-evolution
5. HiMAC (arXiv 2026.3) — hierarchical macro-micro RL for LLM agents
6. HiPER (arXiv 2026.2) — hierarchical RL with explicit credit assignment
7. Voyager (NeurIPS 2023) — LLM agent + skill library 的开山之作

### 需要引用的背景工作
8. Options Framework (Sutton et al., 1999)
9. Option-Critic (Bacon et al., 2017)
10. Cradle (ICML 2025) — general computer control with skill curation
11. ActionEngine (arXiv 2026.2) — programmatic GUI agent with state machine
12. ReUseIt (arXiv 2025.10) — reusable web workflow synthesis
13. ComputerRL (ICLR 2026) — online RL for computer use agents
14. DART (arXiv 2025.9) — decoupled RL training for GUI agents
15. Co-EPG (arXiv 2025.11) — co-evolution of planning and grounding
