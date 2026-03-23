# GUI Agent / Computer Use Agent × RL 顶会研究构想

> 聚焦 GUI Agent 和 Computer Use Agent（GUI + Tool Use）方向，面向 NeurIPS / ICML / ICLR 投稿。
> 基于 2026 年 3 月最新前沿：ComputerRL (ICLR'26, 48.9% OSWorld), Agent Alpha (77.29% OSWorld w/ MCTS), GUI-Genesis (合成环境+可验证奖励), AutoPlay (ICLR'26, 自动任务合成), Code2World (HTML 世界模型), DART (异步解耦 RL), OpenClaw-RL (异步 OPD+PRM) 等。

---

## Idea 1: DreamGUI — 世界模型驱动的 GUI Agent RL 训练

### 核心洞察

GUI Agent RL 的核心瓶颈是 **环境交互代价高昂**：每一步都要在真实桌面环境中执行动作、等待渲染、截取截图。DART 的数据显示，即使全异步架构，env utilization 也只有 67.7%；ComputerRL 需要调度数千个并行虚拟机。

2025-2026 年出现了 GUI 世界模型（ViMo、MobileDreamer、Code2World），它们能预测 "执行动作后的下一帧截图"。但一个关键 gap 是：**这些 world model 至今只被用于 test-time planning（Agent Alpha 式的 look-ahead），从未被集成到 RL training loop 中做 Dyna-style 的 imagined rollout。**

把 world model 用于 RL 训练和用于 test-time search 是完全不同的技术挑战：RL 训练需要 world model 在 **长序列上累积误差可控**，需要处理 **on-policy / off-policy 分布偏移**，需要 **与 GRPO/PPO 训练流程深度集成**。

### 技术方案

1. **GUI World Model 选型与改进**：
   - 以 Code2World 的 HTML-based 表示为基础（比 pixel-level 更结构化、更可控）
   - 改进：增加 state-validity checker——world model 生成的 HTML 截图必须可渲染且结构合法
   - 增加 uncertainty head：输出 world model 对预测的置信度

2. **Dyna-GUI Training Framework**：
   - **Real rollout**：agent 在真实 GUI 环境中交互，收集真实轨迹 → 同时用于训练 policy 和更新 world model
   - **Dream rollout**：agent 在 world model 中 "想象" 执行，生成虚拟轨迹 → 仅当 world model 置信度高时用于 policy 训练
   - **动态混合比例**：η = f(world_model_accuracy, policy_training_stage)
     - 初期训练：η 高（大量 dream rollout 加速 warm-up）
     - 后期精调：η 低（依赖真实环境保证精度）

3. **Error-Aware Imagination**：
   - World model 累积误差是 model-based RL 的经典问题
   - 方案 1: **Truncated imagination** — 虚拟轨迹最多 K 步（K 根据 model accuracy 动态调整）
   - 方案 2: **Branching correction** — 每 K 步从真实环境 "校准" 一次，然后继续 imagine
   - 方案 3: **Reward penalty** — dream rollout 的 reward 按照 world model uncertainty 打折

4. **与 DART/OpenClaw 架构集成**：
   - World model inference 作为独立的异步模块，与真实环境并行运行
   - 当真实环境 queue 满时，自动切换到 dream rollout
   - 当真实环境空闲时，优先使用真实环境
   - 实现 "环境永不闲置" 的目标

### 与已有工作的差异
| 工作 | World Model 用途 | 是否用于 RL 训练 |
|------|----------------|----------------|
| ViMo | 预测下一步截图用于 test-time decision | ❌ |
| MobileDreamer | test-time rollout imagination | ❌ |
| Code2World | 预测 HTML 用于 agent planning | ❌ |
| Agent Alpha | MCTS test-time search | ❌ |
| **DreamGUI (Ours)** | **Dyna-style RL training + test-time** | **✅** |

### 实验设计
- 核心指标：**相同 wall-clock time 下** real-only vs. dream-augmented 的 task success rate
- Benchmark: OSWorld, AndroidWorld
- Ablation: dream ratio η, truncation length K, uncertainty threshold
- 分析: world model prediction accuracy vs. downstream RL performance 的关系曲线

### 目标会议: NeurIPS / ICML

---

## Idea 2: SkillForge — GUI Agent 通过 RL 自动发现和学习可复用技能

### 核心洞察

当前 GUI agent 的动作空间要么是 low-level atomic actions（click, type, scroll），要么是 ComputerRL/UltraCUA 的 API-GUI hybrid。无论哪种，agent 在每个任务中都必须**从零开始逐步执行**，不能复用之前学到的操作序列。

人类使用电脑的方式完全不同：我们把 "打开浏览器 → 搜索关键词 → 点击第一个结果" 视为一个 **skill**（"搜索某个东西"），而不是 5 个独立的 atomic action。这种层次化的技能复用是人类效率的关键。

**核心问题：能否让 GUI agent 通过 RL 自动发现频繁出现的动作序列，将其封装为可复用的 "技能"（macro-action / option），并在后续任务中直接调用？**

这不是简单的 "学习子任务"（那是 HiPER 等工作做的），而是 **data-driven 的技能发现** + **RL-driven 的技能优化** + **动态技能库管理**。

### 技术方案

1. **技能发现（Skill Discovery）**：
   - 从大量 GUI 轨迹数据中，用频繁子序列挖掘 + VLM 语义聚类发现反复出现的操作模式
   - 例如：{click(file_menu) → click(save_as) → type(filename) → click(save)} → 命名为 `save_file(filename)`
   - 用 VLM 为每个发现的技能生成自然语言描述和使用条件

2. **技能封装（Skill Parameterization）**：
   - 每个技能 = (precondition, policy, postcondition, parameters)
   - precondition：截图中需要满足什么视觉条件才能调用此技能
   - policy：执行此技能的 action 序列（参数化的，例如 filename 是变量）
   - postcondition：执行成功后截图应该是什么样

3. **层次 RL 训练（Hierarchical RL）**：
   - **High-level policy**：给定 (task, screenshot)，输出 skill selection + skill parameters
   - **Low-level policy**：执行具体 skill 内的 atomic actions
   - **RL 目标**：同时优化两层——high-level 学习何时调用哪个 skill，low-level 学习如何更好地执行 skill
   - 用 option framework 形式化：每个 skill 是一个 option (I, π, β)

4. **技能库动态演化**：
   - RL 训练过程中持续发现新技能（当某个 action 序列被多次成功执行时自动提取）
   - 淘汰低频或低成功率的技能
   - 技能组合：两个技能可以组合成更高层的技能（递归层次化）
   - 类比人类学习：从 "一步步操作" → "熟练的快捷操作" → "复杂的工作流"

### 为什么这不是简单的 hierarchical RL
- 不是预定义子任务（HiPER）→ 技能是 data-driven 自动发现的
- 不是固定的 option set → 技能库随训练动态演化
- 不是 code-as-action（CodeDance）→ 技能是从 GUI 交互中学到的，不需要编程接口
- 关键贡献：**技能发现 + 层次 RL + 动态技能库** 三位一体

### 实验设计
- **迁移学习**：在 app A 上学到的技能，在 app B 上直接使用的成功率
- **效率提升**：使用技能库 vs. 不使用技能库的平均轨迹长度和 task success rate
- **技能可解释性**：可视化发现的技能，展示 agent 自动学会了 "哪些操作模式"
- **Scaling**：技能库大小 vs. agent 能力的关系
- Benchmark: OSWorld, AndroidWorld, WebArena

### 目标会议: NeurIPS / ICLR

---

## Idea 3: GUI-Genesis++ — Agent 自主合成训练环境与可验证奖励的闭环进化

### 核心洞察

GUI-Genesis (2026.2) 展示了一个重要的 paradigm：**不是在真实 app 上做 RL，而是用 LLM 自动合成轻量 web 环境 + 代码原生可验证奖励**，效率提升 10 倍，成本降低 $28K/epoch。

但 GUI-Genesis 有一个根本局限：**环境合成和 RL 训练是解耦的两个阶段**——先合成一批环境，然后在上面训练。这意味着：
- 合成的环境可能不是 agent 当前最需要练习的
- 无法根据 agent 的弱点动态调整环境难度
- 无法形成 "agent 变强 → 环境变难 → agent 更强" 的自我进化循环

**核心想法：让 GUI agent 自己参与到环境合成过程中——agent 的失败案例驱动新环境的生成，形成 "合成环境 → RL 训练 → 发现弱点 → 合成针对性环境 → 继续训练" 的闭环。**

### 技术方案

1. **Weakness-Driven Environment Synthesis**：
   - 分析 agent 在 RL 训练中的失败轨迹，提取失败模式（pattern）
   - 例如：agent 反复在 "需要滚动才能看到目标" 的场景中失败
   - 用 LLM 合成更多包含此类挑战的环境
   - 类比 curriculum learning 中的 "hard example mining"，但在环境层面

2. **Self-Improving Verification**：
   - GUI-Genesis 的可验证奖励是 LLM 生成的断言代码（assertion code）
   - 问题：LLM 生成的 assertion 可能有 bug（false positive/negative）
   - 改进：用 agent 的成功/失败轨迹反向验证 assertion 的正确性
   - 如果 agent 明显完成了任务但 assertion 给了负奖励 → 标记此 assertion 为可疑 → 修复

3. **Difficulty-Adaptive Environment Pool**：
   - 维护一个动态环境池，按难度分层
   - 用 multi-armed bandit 策略动态选择训练环境
   - 优先从 "agent 当前 pass rate ≈ 30-70%" 的环境中采样（学习效率最高的区间）
   - 自动退役太简单或太难的环境

4. **Compositional Environment Generation**：
   - 简单环境 → 复杂环境的自动组合
   - 例如：环境 A（文件操作）+ 环境 B（浏览器操作）→ 环境 C（"在浏览器中下载文件并保存到指定目录"）
   - 用 agent 的技能掌握情况决定何时组合、如何组合

### 与 GUI-Genesis 和 AutoPlay 的差异
| 工作 | 环境来源 | 是否闭环 | 难度自适应 | 奖励自修复 |
|------|--------|--------|----------|----------|
| GUI-Genesis | LLM 一次性合成 | ❌ | ❌ | ❌ |
| AutoPlay | MLLM 探索 + 合成 | ❌ | ❌ | ❌ |
| **Ours** | **Agent 失败驱动 + LLM 合成** | **✅** | **✅** | **✅** |

### 实验设计
- 对比：static env pool (GUI-Genesis) vs. dynamic self-evolving pool vs. real-world env
- 泛化测试：在合成环境上训练，在真实 OSWorld 上测试
- 分析：环境多样性曲线、难度分布演化、assertion 质量改善
- 关键指标：相同计算预算下的最终 task success rate

### 目标会议: NeurIPS / ICLR

---

## Idea 4: GUI-HER — 基于后见之明的轨迹重标注加速 GUI Agent RL

### 核心洞察

GUI Agent RL 中，agent 的成功率通常很低（OSWorld 上初始 RL 前约 27%）。这意味着 **约 73% 的 rollout 产生的都是失败轨迹**。在标准 GRPO 中，这些失败轨迹只提供 "负信号"，学习效率极低。

但仔细观察这些失败轨迹就会发现：**一条 "任务 X 失败" 的轨迹，可能成功完成了任务 Y。** 例如：
- 任务是 "在 Word 中将字体改为 Arial"，agent 错误地打开了 "段落设置" → 轨迹失败
- 但这条轨迹 **完美地演示了 "如何打开段落设置"** → 对另一个任务来说是成功的

这正是 Hindsight Experience Replay（HER）的核心思想，但 HER 的原始形式需要 goal-conditioned policy，不能直接用于 GUI agent 的 instruction-following 设定。

**核心想法：用 VLM 对失败轨迹进行 "后见之明重标注"——分析轨迹实际达到了什么状态，反向生成一个匹配的 task instruction，把失败轨迹重标注为 "成功" 轨迹。**

### 技术方案

1. **Visual Hindsight Relabeling**：
   - 输入：失败轨迹 τ = [(s_0, a_0), (s_1, a_1), ..., (s_T, a_T)]，原始任务 g_original
   - VLM 分析最终状态 s_T 和中间状态序列
   - 输出：一个新的任务描述 g_new，使得 τ 在 g_new 下是"成功"的
   - 例如："将字体改为 Arial" → relabel 为 "打开段落设置对话框"

2. **Multi-Granularity Relabeling**：
   - **Full trajectory relabeling**：整条轨迹重标注为一个新任务
   - **Prefix relabeling**：轨迹的前 k 步重标注为一个子任务（更灵活）
   - **Milestone relabeling**：识别轨迹中的关键里程碑状态，每个里程碑生成一个子任务
   - 这自然生成了 **由简到难的 curriculum**——短前缀是简单任务，长轨迹是复杂任务

3. **Quality-Filtered Training**：
   - 不是所有 relabeled 轨迹都有用——需要过滤：
   - Filter 1: g_new 与 g_original 不能太相似（避免循环）
   - Filter 2: g_new 描述的任务必须是 "合理的"（用 VLM 判断）
   - Filter 3: relabeled 轨迹确实能完成 g_new（用验证器或 VLM 检查）

4. **混合训练策略**：
   - 原始成功轨迹: 标准 GRPO positive reward
   - 原始失败轨迹: 标准 GRPO negative reward
   - Relabeled 轨迹: 作为额外的 positive reward 样本（但权重 lower，因为质量不如真实成功）
   - 动态调整混合比例：agent 越强，relabeled 轨迹的价值越低（因为真实成功越多）

### 为什么这不是简单的 HER
- HER 要求 goal-conditioned policy（替换 goal）→ 我们是 instruction-following（用 VLM 生成新 instruction）
- HER 的 "achieved goal" 是从状态空间直接读取 → GUI 的 "achieved task" 需要 VLM 推理
- 我们增加了 multi-granularity relabeling（前缀/里程碑），这在 HER 中没有
- 我们增加了 quality filtering，这对于 GUI 场景的噪声很关键

### 实验设计
- 核心实验：标准 GRPO vs. GRPO + HER-relabeling 的 sample efficiency 对比
- 分析：relabeled 轨迹的质量（人类评估）和对训练的贡献
- 在低成功率的困难任务（如 OSWorld 的 OS-level 任务）上效果最显著
- Ablation: relabeling granularity, filter strictness, mixing ratio

### 目标会议: ICML / NeurIPS

---

## Idea 5: ReflectRL — 通过 RL 训练 GUI Agent 的错误检测与自主恢复能力

### 核心洞察

现有 GUI agent 的错误恢复工作（BacktrackAgent、BEAP-Agent、GUI-Reflection）有一个共同的问题：**backtracking 策略不是 RL 训练出来的**，而是基于规则/启发式或 SFT 学习的。这意味着：
- 不能根据具体的错误类型和上下文做出最优的恢复决策
- 不能权衡 "继续尝试 vs. 回退几步 vs. 完全重新开始" 的 trade-off
- 不能从错误恢复的成功/失败经验中持续改进

人类使用电脑时，错误恢复是一种 **通过大量实践习得的 skill**——我们学会了 Ctrl+Z、学会了 "如果这条路不通就换另一条"。这种 skill 是 RL 最擅长学习的。

**核心想法：设计一个专门用于训练 GUI agent 错误检测与恢复能力的 RL 框架，让 agent 学会 "什么时候知道自己错了" 和 "错了以后怎么办"。**

### 技术方案

1. **扩展动作空间——加入元动作**：
   - 标准 GUI 动作：click, type, scroll, ...
   - **新增元动作**：
     - `detect_error()`：agent 主动判断当前是否偏离正确路径
     - `backtrack(n)`：回退 n 步到之前的状态
     - `restart()`：放弃当前尝试，完全重新开始
     - `reflect(observation)`：暂停执行，分析当前截图和历史，输出反思文本
   - Agent 通过 RL 学习何时调用这些元动作

2. **Error-Augmented Training**：
   - 故意在 rollout 中 **注入错误**（随机替换 agent 的某步动作为错误动作）
   - 奖励设计：
     - 如果 agent 检测到注入的错误并成功恢复 → 高 reward
     - 如果 agent 未检测到错误继续错下去 → 负 reward
     - 如果 agent 错误检测（false alarm）→ 小负 reward
   - 这创造了大量的错误恢复训练信号（比等待自然出错高效得多）

3. **Recovery-Aware Reward**：
   - 不仅奖励最终成功，还奖励 **高效的恢复过程**：
   - R = task_success + α × (recovery_speed) + β × (error_detection_accuracy)
   - recovery_speed：从错误状态恢复到正确状态的步数越少越好
   - error_detection_accuracy：precision & recall of error detection

4. **Self-Verification Loop**：
   - 每执行几步，agent 自动进入 "verification mode"——对比当前截图和任务要求
   - RL 训练 agent 学习最优的 verification 频率（太频繁浪费步数，太稀疏错过错误）
   - 类似 Agent Alpha 的 step-level evaluation，但集成在 RL 训练中而非 test-time

### 与已有工作的差异
| 工作 | 方法 | RL 训练 | 主动注入错误 | 恢复策略 |
|------|------|---------|-----------|---------|
| BacktrackAgent | SFT + judgment reward | 部分 | ❌ | 固定规则 |
| BEAP-Agent | DFS 框架 | ❌ | ❌ | DFS 回溯 |
| GUI-Reflection | SFT + online tuning | 部分 | ❌ | 反思+重试 |
| **ReflectRL (Ours)** | **端到端 RL** | **✅** | **✅** | **RL 学习的自适应策略** |

### 实验设计
- 对比: standard RL vs. ReflectRL（错误检测率、恢复成功率、最终 task success）
- 特别关注 **长序列任务**（agent 犯错概率更高，恢复能力更重要）
- Ablation: error injection rate, verification frequency, meta-action design
- 人类评估: agent 的 "犯错-发现-恢复" 行为是否像人类

### 目标会议: ICLR / NeurIPS

---

## Idea 6: Computer Use Agent 的 GUI-API 模式选择学习

### 核心洞察

ComputerRL (ICLR'26) 提出了 API-GUI paradigm，UltraCUA (ICLR'26) 融合了 GUI primitives 和 programmatic tool calls。这代表了 Computer Use Agent 的未来方向——不仅能点击屏幕，还能调用 API 和执行代码。

但一个被忽略的核心问题是：**agent 什么时候应该用 GUI 操作，什么时候应该用 API/代码？** 当前方案要么固定比例混合，要么让 model 隐式学习。但最优策略高度依赖上下文：
- 安装软件 → `apt install` 比 GUI 快 10 倍
- 排版文档 → GUI 所见即所得更直观
- 批量重命名文件 → 一行 shell 命令搞定
- 精确定位界面元素 → accessibility API 比 pixel clicking 更准确

**核心想法：将 "选择 GUI 还是 API/Code" 建模为 RL 的显式决策，让 agent 通过大量试错学习每种场景下的最优控制模式。**

### 技术方案

1. **Tri-Modal Action Space**：
   - **GUI Mode**：标准的 click/type/scroll/keyboard shortcut
   - **API Mode**：调用系统 API（accessibility API, file system API, application API）
   - **Code Mode**：生成并执行 Python/Shell 脚本
   - 每一步，agent 先决定用哪种 mode，再在该 mode 下生成具体 action

2. **Mode Selection via RL**：
   - Mode selector 接收 (task, current_screenshot, action_history, available_APIs)
   - 输出：mode_choice ∈ {GUI, API, Code} + confidence
   - Reward：task_completion + efficiency_bonus（步数越少奖励越高）
   - 关键：GUI 操作步数多但直观；API/Code 操作步数少但需要正确的接口知识

3. **Mode-Specific Reward Shaping**：
   - GUI 操作的每步给小的 step cost（鼓励使用更高效的 API/Code 当可行时）
   - API 操作成功给 bonus（鼓励发现可用的 API）
   - Code 操作的 syntax error 给即时 negative reward（鼓励生成正确代码）
   - 最终 task completion 是最大的 reward

4. **Progressive Mode Unlocking**：
   - 训练初期：只开放 GUI mode（让 agent 先学会基础操作）
   - 中期：开放 API mode（agent 开始探索更高效的路径）
   - 后期：开放 Code mode（agent 学习生成自动化脚本）
   - 类似课程学习，避免 agent 一开始就陷入复杂的 code generation

5. **Cross-Mode Fallback**：
   - RL 还要学习 "fallback" 策略：API 调用失败 → 自动切换到 GUI；Code 报错 → 分析错误信息 → 修正代码或切换到手动操作
   - 这种 robustness 是纯 GUI 或纯 API agent 做不到的

### 与 ComputerRL / UltraCUA 的差异
| 工作 | API-GUI 融合方式 | 显式模式选择 | RL 优化模式切换 |
|------|----------------|-----------|---------------|
| ComputerRL | 隐式混合 | ❌ | ❌ |
| UltraCUA | 预定义优先级 | 部分 | ❌ |
| **Ours** | **RL 学习的显式选择** | **✅** | **✅** |

### 实验设计
- 对比：GUI-only vs. API-only vs. Code-only vs. fixed hybrid vs. **RL-learned mode selection**
- 分析 agent 学到的 "mode selection policy"：在什么场景下选择什么 mode？
- 效率指标：平均步数、wall-clock time、token 消耗
- Benchmark: OSWorld（桌面操作最能体现多模式优势）

### 目标会议: NeurIPS / ICLR

---

## Idea 7: GUI Agent 的 Online Continual RL — 从部署中持续进化

### 核心洞察

当前 GUI Agent RL 是 "训练完就部署" 的范式——在 OSWorld/AndroidWorld 上训练到收敛，然后 freeze 模型部署。但真实世界中：
- 用户的电脑环境千差万别（不同 OS 版本、不同主题、不同语言、不同安装的软件）
- App 会更新 UI（Chrome 每 6 周更新一次、各种 app 界面常变）
- 用户有个性化的操作习惯和偏好
- Agent 在新环境中必然会犯错，需要从错误中学习

OpenClaw-RL 展示了 "边用边学" 的可能性，但只处理了文本交互。GUI 场景的 online RL 有独特的技术挑战：visual distribution shift（不同电脑的截图风格不同）、不可逆操作的安全风险、用户反馈信号的稀疏性。

**核心想法：设计一个 Online Continual RL 框架，让部署后的 GUI agent 能安全地从真实交互中持续学习，同时避免灾难性遗忘和不可逆错误。**

### 技术方案

1. **Safe Online Exploration**：
   - **Safety Classifier**：执行动作前，预判该动作是否可能造成不可逆的有害结果
   - 高风险动作（删除文件、发送邮件、修改系统设置）→ 必须用户确认
   - 低风险动作（打开 app、滚动、阅读）→ 自动执行
   - RL 训练 safety classifier：reward = (没有造成不可逆错误) × (没有过度打扰用户)

2. **多来源 Online Reward Signal**：
   - **User correction**：用户手动修正 agent 的操作 → 最强的 negative signal
   - **User continuation**：用户接受 agent 的操作继续下一步 → 隐式 positive signal（类似 OpenClaw 的 next-state signal）
   - **Task re-query**：用户重新描述任务 → agent 的理解有误
   - **Environment feedback**：操作后的截图变化、error dialog 出现等
   - 用 PRM（类似 OpenClaw）将这些多源信号统一为 step-level reward

3. **Anti-Forgetting Online RL**：
   - 挑战：在新环境上学习时不能遗忘在训练集上学到的能力
   - 方案 1：**EWC（Elastic Weight Consolidation）**——对重要参数施加正则化
   - 方案 2：**LoRA-based Adaptation**——online learning 只更新 LoRA 参数，保持基座不变
   - 方案 3：**Replay Buffer**——在 online learning 中混入少量 pre-training 数据
   - 方案 4：**Progressive LoRA**——每个新 "环境" 分配一个小的 LoRA adapter，通过 routing 选择

4. **Deployment Architecture**：
   - Agent 在用户电脑上运行推理（或云端推理 + 本地执行）
   - 交互数据异步上传到训练服务器
   - 定期（例如每天）在服务器上进行 online RL 更新
   - 更新后的模型推送回用户端
   - 隐私保护：只上传 anonymized 轨迹，不包含个人信息

### 与已有工作的差异
| 工作 | 学习阶段 | GUI 支持 | 安全机制 | 抗遗忘 |
|------|--------|--------|--------|-------|
| OpenClaw-RL | online | 有（但重点在文本） | ❌ | ❌ |
| UI-Mem | 无梯度更新 | ✅ | ❌ | 不适用 |
| PersonalAlign | 无梯度更新 | ✅ | ❌ | 不适用 |
| **Ours** | **online RL** | **✅（核心）** | **✅** | **✅** |

### 实验设计
- 模拟部署环境：在与训练分布不同的 OS 版本/主题/语言上部署
- 对比：frozen model vs. online SFT vs. online RL
- 衡量灾难性遗忘：online 学习后在原始 benchmark 上的性能变化
- 安全性评估：不可逆错误发生率
- 个性化评估：经过 N 次交互后，agent 对特定用户习惯的适应程度

### 目标会议: NeurIPS / ICML

---

## 综合对比与投稿策略

| Idea | 核心贡献 | 新颖度 | 可行性 | Impact | 计算需求 | 最佳投稿 |
|------|---------|--------|--------|--------|---------|---------|
| 1. DreamGUI | World Model ↔ RL 闭环 | ★★★★★ | ★★★☆☆ | ★★★★★ | 高 | NeurIPS/ICML |
| 2. SkillForge | 自动技能发现+层次 RL | ★★★★☆ | ★★★★☆ | ★★★★★ | 中 | NeurIPS/ICLR |
| 3. Genesis++ | 闭环环境进化 | ★★★★☆ | ★★★★★ | ★★★★☆ | 中 | NeurIPS/ICLR |
| 4. GUI-HER | 轨迹重标注加速 RL | ★★★★★ | ★★★★★ | ★★★★☆ | 低 | ICML/NeurIPS |
| 5. ReflectRL | RL 训练错误恢复 | ★★★★☆ | ★★★★☆ | ★★★★☆ | 中 | ICLR/NeurIPS |
| 6. Mode Selection | GUI-API-Code 切换学习 | ★★★★☆ | ★★★★☆ | ★★★★★ | 中 | NeurIPS/ICLR |
| 7. Online Continual RL | 部署后持续进化 | ★★★★★ | ★★★☆☆ | ★★★★★ | 高 | NeurIPS/ICML |

### 组合推荐

**最佳双打（两篇互补的论文）**：
- **Idea 4 (GUI-HER) + Idea 3 (Genesis++)**：一个优化数据利用效率（让失败轨迹变有用），一个优化环境供给效率（动态合成最需要的环境）。合在一起讲 "如何最大化 GUI Agent RL 的每一份计算" 的故事。

**最有 Oral 潜力**：
- **Idea 1 (DreamGUI)**：World model for RL training 是 RL 社区几十年的核心话题（Dyna, Dreamer, MBPO 等），首次在 GUI Agent 场景落地，且与当前 GUI world model 热潮（ViMo, Code2World, MobileDreamer）完美衔接。
- **Idea 2 (SkillForge)**：Skill discovery + hierarchical RL 也是经典话题的新应用，GUI 场景天然适合层次化。

**最适合你组优势（计算资源 + GUI 基础设施）**：
- **Idea 1 (DreamGUI)** + **Idea 7 (Online Continual RL)**：需要大量环境和计算资源，你组的基础设施天然匹配。

**最快能出结果（可行性最高）**：
- **Idea 4 (GUI-HER)**：不需要新的模型架构，只需要在现有 GRPO pipeline 上加一个 VLM relabeling 模块，改动最小但 insight 强。
