# Idea 3+4 深入分析: GUI-HER × Genesis++ — 最大化每一份 GPU 算力

---

## 统一故事：GUI Agent RL 的两大浪费

GUI Agent 做 RL 训练有两个巨大的资源浪费:

```
浪费 1: 数据浪费 (GUI-HER 要解决的)
  ├── Agent 做 100 次 rollout
  ├── 只有 ~30 次成功 (reward=1)
  ├── ~70 次失败 (reward=0)
  └── 这 70 次失败轨迹在标准 GRPO 中只提供 "负信号"
      它们里面包含的正确子操作全被浪费了

浪费 2: 环境浪费 (Genesis++ 要解决的)
  ├── Agent 在 Task A 上已经学到了 90% success rate
  ├── 但还在对 Task A 做大量 rollout (因为任务池是固定的)
  ├── Task B 只有 5% success rate，急需更多练习
  └── 没有机制动态调整任务分配，也没有新任务补充
```

**一句话: GUI-HER 让失败轨迹变废为宝，Genesis++ 让训练环境供给永不枯竭。两者合在一起 = 从数据侧和环境侧同时最大化每一份 GPU 算力。**

---

## Part 1: GUI-HER — 让失败轨迹变成学习材料

### 1.1 核心问题

用一个具体数字说明浪费有多大:

```
DART 在 OSWorld 上的数据:
  基座模型 (UI-TARS-1.5-7B) 初始 success rate: ~27.52%
  这意味着每 100 条 rollout，~72 条是失败的

  假设每条轨迹平均 15 步，每步需要 GPU 做 VLM inference + 环境交互:
  ├── 总计算量: 100 × 15 = 1500 步
  ├── 有效计算量 (成功轨迹): 28 × 15 = 420 步
  └── 浪费计算量 (失败轨迹): 72 × 15 = 1080 步 → 72% 的算力被浪费了
```

**但这些 "失败" 轨迹真的一无是处吗？**

### 1.2 具体例子: 失败轨迹中的价值

```
原始任务: "在 LibreOffice Writer 中将字体改为 Arial 14pt"

Agent 的失败轨迹:
  step 1: click(菜单栏 "Format")           ✓ 正确
  step 2: click(下拉菜单 "Paragraph...")     ✗ 错了！应该点 "Character..."
  step 3: [打开了段落设置对话框]
  step 4: 修改了行间距为 1.5                  ✗ 与任务无关
  step 5: click("OK")
  → 任务失败 (字体没有改变)
```

这条轨迹在标准 GRPO 中: reward = 0，整条轨迹都被当作负样本。

**但仔细看:**
- Step 1 是正确的 (正确打开了 Format 菜单)
- Step 2-5 虽然对原任务错误，但 **完美地演示了 "如何修改段落行间距"**

**GUI-HER 做的事:** 用 VLM 分析这条轨迹实际达到了什么状态，生成一个匹配的新 instruction:

```
原始 instruction: "将字体改为 Arial 14pt"  → reward = 0 (失败)
重标注 instruction: "将行间距改为 1.5"      → reward = 1 (成功!)

这条轨迹从 "无用的失败样本" 变成了 "有用的成功样本"
```

### 1.3 技术方案

```
                    GUI-HER 完整流程
                    
输入: 一条失败轨迹 τ = [(s₀,a₀), (s₁,a₁), ..., (sₜ,aₜ)]
      原始任务指令 g_original
      最终截图 sₜ

Step 1: VLM Hindsight Analyzer
┌─────────────────────────────────────────────┐
│ Prompt 给 VLM:                               │
│                                             │
│ "你是一个 GUI 操作分析专家。                    │
│  以下是一个 agent 在桌面环境中的操作轨迹:        │
│  - 初始截图: [s₀]                             │
│  - 操作序列: [a₀, a₁, ..., aₜ]               │
│  - 最终截图: [sₜ]                             │
│                                             │
│  原始任务是: {g_original} (agent 未能完成)      │
│                                             │
│  请分析:                                      │
│  1. 这条轨迹实际上完成了什么操作？               │
│  2. 用一个任务指令描述它实际达到的状态变化         │
│  3. 这个轨迹的哪些前缀完成了某个有意义的子目标？   │
│"                                             │
└─────────────────────────────────────────────┘

VLM 输出:
  全轨迹重标注: "将段落行间距修改为 1.5 倍"
  前缀重标注:
    - 前 1 步: "打开 Format 菜单"
    - 前 2 步: "打开段落设置对话框"
    - 前 5 步: "将行间距修改为 1.5 并确认"

Step 2: Quality Filter
┌─────────────────────────────────────────────┐
│ 过滤掉低质量的重标注:                          │
│                                             │
│ Filter 1: g_new ≠ g_original                 │
│   (新任务不能和原任务一样)                      │
│                                             │
│ Filter 2: g_new 是有意义的 GUI 任务             │
│   (VLM 判断: "将行间距改为1.5" → 有意义 ✓)      │
│   (排除: "随机点击几个按钮" → 无意义 ✗)          │
│                                             │
│ Filter 3: 轨迹确实完成了 g_new                  │
│   (VLM 对比 s₀ 和 sₜ，确认状态变化与 g_new 匹配) │
└─────────────────────────────────────────────┘

Step 3: 加入训练
┌─────────────────────────────────────────────┐
│ 原始数据:                                     │
│   (τ, g_original, reward=0)  → GRPO 负样本    │
│                                             │
│ HER 生成的数据:                                │
│   (τ, g_new, reward=1)       → GRPO 正样本    │
│   (τ[:1], g_prefix_1, reward=1) → 正样本      │
│   (τ[:2], g_prefix_2, reward=1) → 正样本      │
│                                             │
│ 一条失败轨迹 → 1 条负样本 + 3 条正样本           │
│ 数据利用率提升 4 倍                             │
└─────────────────────────────────────────────┘
```

### 1.4 多粒度重标注——这是比经典 HER 更强的地方

```
一条 15 步的失败轨迹，可以生成多条不同粒度的正样本:

原始轨迹: s₀ →a₀→ s₁ →a₁→ s₂ →a₂→ ... →a₁₄→ s₁₅
                                              (失败)

前缀 1 (1步):  s₀ →a₀→ s₁
  重标注: "打开 Format 菜单"                    (简单任务)

前缀 2 (3步):  s₀ →a₀→ s₁ →a₁→ s₂ →a₂→ s₃
  重标注: "打开段落设置对话框"                    (中等任务)

前缀 3 (5步):  s₀ → ... → s₅
  重标注: "将段落行间距改为 1.5"                  (完整任务)

里程碑 (step 7-10): s₇ → ... → s₁₀
  重标注: "在已打开的设置中修改缩进"              (片段任务)
```

**这天然生成了一个从简单到复杂的 curriculum!** 短前缀 = 简单任务，长轨迹 = 复杂任务。不需要人工设计 curriculum，HER 自动产出。

### 1.5 相关工作对比

| 工作 | 方法 | 用于 GUI? | 多粒度? | 生成新 instruction? |
|------|------|----------|--------|-------------------|
| HER (Andrychowicz 2017) | 替换 goal state | ❌ (机器人) | ❌ | ❌ (直接用达到的 state) |
| HIR (Zhang 2023) | VLM 重写 instruction | ❌ (文本任务) | ❌ | ✅ |
| HiR (2025.12) | 失败→成功 relabeling | ❌ (LLM 对齐) | ❌ | ✅ |
| DART experience pool | 存储成功轨迹备用 | ✅ | ❌ | ❌ (不生成新任务) |
| **GUI-HER (Ours)** | **VLM 分析 GUI 状态变化** | **✅** | **✅** | **✅** |

**关键差异:**
1. 所有已有 HER 变体都没有用于 GUI/Computer Use 场景
2. 多粒度重标注（前缀/里程碑/全轨迹）是新的
3. GUI 状态变化的分析需要 VLM 的视觉理解能力，这是文本 HER 做不到的

---

## Part 2: Genesis++ — 让训练环境永不枯竭

### 2.1 核心问题

```
GUI-Genesis (已有工作) 的流程:
  Step 1: 拿到一批 GUI 任务 (如 OSWorld 的 369 个)
  Step 2: 用 LLM 为每个任务合成一个轻量 web 环境 + 可验证奖励
  Step 3: 在合成环境上做 RL 训练
  
  结果: 14.54% 提升，环境延迟降低 10x
  
GUI-Genesis 的局限:
  ├── 合成是一次性的，不会根据 agent 的学习进度更新
  ├── 不知道 agent 哪些任务已经学会了、哪些还差
  ├── 不会生成 agent "刚好需要练习" 的新任务
  └── 可验证奖励可能有 bug (LLM 生成的 assertion 不一定对)
```

### 2.2 Genesis++ 的核心改进: 闭环进化

```
┌──────────────────────────────────────────────────┐
│                Genesis++ 闭环                     │
│                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ 环境合成  │───→│ RL 训练   │───→│ 弱点分析  │   │
│  │ (生成)   │    │ (学习)    │    │ (诊断)    │   │
│  └────▲─────┘    └──────────┘    └─────┬────┘   │
│       │                                │        │
│       │          ┌──────────┐          │        │
│       └──────────│ 新环境生成 │◄─────────┘        │
│                  │ (治疗)    │                    │
│                  └──────────┘                    │
│                                                  │
│  闭环: 诊断弱点 → 针对性合成 → 训练 → 再诊断       │
└──────────────────────────────────────────────────┘
```

### 2.3 具体例子

```
Round 1: 初始训练
  ├── 环境池: GUI-Genesis 合成的 300 个环境
  ├── RL 训练 5000 steps
  └── 结果: 整体 success rate 35%

弱点分析:
  ├── 按任务类型统计 success rate:
  │   ├── 文件操作: 60% (已经不错)
  │   ├── 浏览器任务: 45% (中等)
  │   ├── 终端命令: 25% (差)
  │   └── 多步表单填写: 10% (极差)
  │
  ├── 失败模式分析 (用 VLM 分析失败轨迹):
  │   ├── Pattern A: "需要滚动但不知道滚动" (出现 50 次)
  │   ├── Pattern B: "在多选下拉框中选错选项" (出现 30 次)
  │   └── Pattern C: "跨 tab 操作时丢失上下文" (出现 25 次)

Round 2: 针对性环境生成
  ├── 为 "终端命令" 类型额外合成 50 个新环境
  ├── 为 "多步表单填写" 额外合成 80 个新环境
  ├── 针对 Pattern A: 合成 30 个 "目标在页面底部需要滚动" 的环境
  ├── 针对 Pattern B: 合成 20 个 "包含多选下拉框" 的环境
  ├── 减少 "文件操作" 的 rollout 频率 (已经够好了)
  └── 更新环境池: 300 + 50 + 80 + 30 + 20 = 480 个环境

Round 3: 继续训练，再分析，再合成...
```

### 2.4 奖励自修复

```
GUI-Genesis 合成的可验证奖励 = Python assertion 代码
这些 assertion 可能有 bug:

例如: 任务 "将字体大小改为 14pt"
  合成的 assertion:
    assert document.font_size == 14  
  
  问题: 如果 agent 通过另一种方式完成了 (比如选中文字后在工具栏直接输入 14)
        但 assertion 检查的是样式表中的字体大小
        可能出现 false negative (agent 做对了但 assertion 说没对)

奖励自修复机制:
  ├── 收集所有 "agent 看起来做对了但 reward=0" 的轨迹
  │   (用 VLM 判断截图是否满足任务要求)
  ├── 这些是 assertion 可能有 bug 的信号
  ├── 用 LLM 分析并修复 assertion 代码
  └── 修复后重新计算这些轨迹的 reward
```

### 2.5 与 GUI-Genesis 和 AutoPlay 的差异

| 维度 | GUI-Genesis | AutoPlay (ICLR'26) | Genesis++ (Ours) |
|------|-------------|---------------------|------------------|
| 环境来源 | LLM 一次性合成 | MLLM 探索 + 合成 | Agent 弱点驱动 + LLM 合成 |
| 闭环更新 | ❌ | ❌ | ✅ |
| 难度自适应 | ❌ | ❌ | ✅ (MAB 策略) |
| 奖励自修复 | ❌ | ❌ | ✅ |
| 失败模式分析 | ❌ | ❌ | ✅ |

---

## Part 3: 两者如何组合成一篇论文？

### 3.1 统一的故事: Compute-Efficient RL for GUI Agents

```
论文标题候选:
  "Every Rollout Counts: Maximizing Data and Environment Efficiency 
   for GUI Agent Reinforcement Learning"
   
  或

  "Waste Not, Want Not: Hindsight Relabeling and Adaptive Environment
   Synthesis for Sample-Efficient GUI Agent RL"
```

**核心叙事:**

> GUI Agent RL 训练中有两大计算浪费：失败轨迹被丢弃（数据浪费），和固定任务池导致的无效 rollout（环境浪费）。我们提出两个互补的技术来消除这些浪费：GUI-HER 通过后见之明重标注让每条失败轨迹都变成学习材料，Genesis++ 通过弱点驱动的环境合成确保 agent 始终在最需要的任务上练习。两者合在一起，在相同计算预算下实现了显著的性能提升。

### 3.2 两者如何互补

```
GUI-HER 和 Genesis++ 的配合:

                   ┌────────────────┐
                   │  RL 训练引擎    │
                   │  (GRPO)        │
                   └───┬────────┬───┘
                       │        │
              产出成功轨迹  产出失败轨迹
                       │        │
                       │        ├──────────────────┐
                       │        │                  │
                       ▼        ▼                  ▼
              ┌──────────┐  ┌──────────┐    ┌──────────┐
              │ 正常正样本 │  │ GUI-HER  │    │ Genesis++│
              │ (reward=1)│  │ 重标注为  │    │ 分析失败 │
              │          │  │ 正样本    │    │ 模式     │
              └─────┬────┘  └─────┬────┘    └─────┬────┘
                    │             │                │
                    ▼             ▼                ▼
              ┌──────────────────────┐    ┌──────────────┐
              │  更丰富的训练数据      │    │  更有针对性的  │
              │  (原始正样本 + HER正样本)│    │  新环境和任务  │
              └──────────┬───────────┘    └──────┬───────┘
                         │                       │
                         └───────┬───────────────┘
                                 │
                                 ▼
                        下一轮 RL 训练
```

**具体的互补关系:**

1. **HER 的重标注任务 → Genesis++ 的环境需求**
   - HER 发现 agent 经常 "误入" 段落设置（本来要改字体）
   - 这说明 agent 对 "Format 菜单下各选项的区分" 不够好
   - Genesis++ 据此合成更多 "区分 Format 子菜单" 的训练环境

2. **Genesis++ 的新环境 → HER 的更多重标注机会**
   - Genesis++ 合成了新的困难环境，agent 在上面大量失败
   - 这些失败轨迹通过 HER 重标注为其他任务的成功样本
   - 即使在困难任务上失败，也不浪费计算

3. **形成正向循环:**
   ```
   更多失败 → HER 产出更多训练数据 → agent 变强
                                      ↓
   agent 变强 → Genesis++ 生成更难的任务 → 更多失败 → ...
   ```

### 3.3 实验设计

```
主实验: OSWorld benchmark

Baselines:
  B1: Vanilla GRPO (标准 RL，固定任务，不处理失败轨迹)
  B2: GRPO + DART adaptive curation (现有 SOTA 数据策略)
  B3: GRPO + GUI-Genesis (合成环境，但不闭环)
  B4: GRPO + AutoPlay (自动任务合成，但不闭环)

Ablations:
  A1: GRPO + GUI-HER only (只加重标注，环境不变)
  A2: GRPO + Genesis++ only (只加闭环环境，不重标注)
  A3: GRPO + GUI-HER + Genesis++ (完整方案)

指标:
  ├── Sample efficiency: 达到 X% success rate 需要多少 rollout
  ├── Compute efficiency: 达到 X% success rate 需要多少 GPU hours
  ├── Final performance: 固定计算预算下的最终 success rate
  ├── Data utilization: 每条 rollout 平均贡献多少有效训练信号
  └── 泛化: 在训练中从未见过的任务上的 zero-shot performance

期望结果:
  A3 >> A1 ≈ A2 >> B1
  (完整方案远好于任一单独技术，单独技术好于 baseline)
  
  关键数字 (期望):
  ├── HER: 相同 rollout 数量下 success rate +5-10%
  ├── Genesis++: 相同 rollout 数量下 success rate +5-8%
  └── 组合: +10-15% (有协同效应)
```

### 3.4 分析实验 (增加论文深度)

```
分析 1: HER 重标注质量
  ├── 人工评估 200 条重标注的准确率
  ├── 重标注任务的多样性分布
  └── 不同粒度 (全轨迹/前缀/里程碑) 的各自贡献

分析 2: Genesis++ 环境进化
  ├── 可视化: 环境池的难度分布随训练轮次的变化
  ├── 弱点消除率: 识别的失败模式在下一轮中的改善程度
  └── 奖励修复: 被修复的 assertion 数量和修复准确率

分析 3: 数据利用率
  ├── 标准 GRPO: 每条 rollout 贡献 X bit 的训练信号
  ├── + HER: 每条 rollout 贡献 Y bit (Y >> X)
  └── 可视化: 计算预算 vs. 有效训练数据量的曲线

分析 4: 涌现的 curriculum
  ├── HER 生成的重标注任务自然形成由简到难的分布
  └── 对比: 人工设计的 curriculum vs. HER 自动产生的 curriculum
```

---

## Part 4: 风险评估与诚实判断

### 这个组合的优势

1. **RL contribution 非常清晰**: HER 直接改善 RL 的 sample efficiency，Genesis++ 直接改善 RL 的环境供给——两者都是实实在在的 RL 训练技术贡献
2. **不需要改模型架构**: 只改数据处理和环境管理，与任何 base model (7B-72B) 和任何 RL 算法 (GRPO/PPO) 兼容
3. **实验容易做**: 在现有 DART/ComputerRL 框架上加模块即可
4. **故事自洽**: "最大化每份 GPU 算力" 是一个清晰有力的叙事

### 主要风险

1. **HER 重标注的质量**:
   - VLM 分析 GUI 状态变化生成新 instruction 的准确率可能不够高
   - 低质量的重标注会引入噪声，可能反而损害训练
   - **应对**: 需要严格的 quality filter，宁缺毋滥

2. **Genesis++ 与 GUI-Genesis 的差异度**:
   - Reviewer 可能说 "这就是 GUI-Genesis + curriculum learning"
   - **应对**: 强调闭环（诊断→合成→训练→再诊断）和奖励自修复，这些 GUI-Genesis 完全没有

3. **HER 在 GUI 场景的独特挑战**:
   - 文本 HER: 替换 instruction 就行
   - GUI HER: 需要理解 **视觉状态变化** 来判断 "轨迹实际完成了什么"
   - 这更难，但也是 novelty 所在

4. **两个 contribution 合在一起是否太散**:
   - Reviewer 可能觉得 HER + Genesis++ 是两个独立的 trick
   - **应对**: 必须展示协同效应（A3 >> A1 + A2 的单独加和）

### 与 SkillForge 的对比

| 维度 | SkillForge | GUI-HER + Genesis++ |
|------|-----------|-------------------|
| RL contribution 清晰度 | 模糊 (skill vs plan 的区分不锐利) | **清晰** (sample efficiency + env efficiency) |
| Novelty | 中等 (SkillRL/CUA-Skill 已存在) | **较高** (GUI-HER 无先例, Genesis++ 有明确差异化) |
| 工程复杂度 | 高 (skill discovery + hierarchical RL) | **中等** (VLM relabeling + env synthesis) |
| 实验风险 | 高 (skill 的 value 可能不显著) | **中低** (HER 和 env synthesis 各自有较可靠的先验) |
| 审稿人接受度 | 需要强实验支撑 | **较高** (data efficiency 是普遍关心的问题) |
