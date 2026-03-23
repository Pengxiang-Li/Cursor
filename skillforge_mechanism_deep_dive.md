# SkillForge 核心机制深入分析：Skill 是什么？RL 怎么发现 Skill？

---

## 一、"Skill" 到底是什么？——用具体例子说明

### 1.1 最直观的理解

Skill = **一段可复用的、参数化的 GUI 操作序列，能完成一个特定的子目标。**

就像人类使用电脑时，我们不会想 "先移动鼠标到坐标 (120, 45)，点击左键，等待 200ms，移动鼠标到坐标 (200, 300)……"。我们想的是 **"保存文件"、"搜索关键词"、"复制一段文字"**。每一个都是一个 skill。

### 1.2 具体例子

```
Skill: save_file_as(filename)
├── 前置条件 (precondition): 当前有一个可编辑文档打开
├── 参数: filename (字符串)
├── 动作序列:
│   ├── step 1: click(菜单栏 "File")
│   ├── step 2: click(下拉菜单 "Save As...")
│   ├── step 3: [等待对话框出现]
│   ├── step 4: clear(文件名输入框) + type(filename)
│   └── step 5: click("Save" 按钮)
├── 后置条件 (postcondition): 文件以 filename 保存成功
└── 适用范围: LibreOffice Writer, Calc, Impress, Notepad, etc.
```

```
Skill: scroll_to_find(target_description)
├── 前置条件: 当前页面可能需要滚动才能看到目标
├── 参数: target_description (文字描述，如 "Submit 按钮")
├── 动作序列 (条件循环):
│   ├── step 1: 观察当前截图，检查 target 是否可见
│   ├── step 2: if 可见 → click(target) → 结束
│   ├── step 3: if 不可见 → scroll_down
│   └── step 4: 回到 step 1 (最多重复 N 次)
├── 后置条件: 目标元素被找到并点击
└── 适用范围: 任何有滚动页面的应用
```

```
Skill: navigate_menu(menu_path)
├── 前置条件: 应用有菜单栏
├── 参数: menu_path (列表，如 ["Format", "Text", "Font Size"])
├── 动作序列:
│   ├── step 1: click(menu_path[0])  // 点击顶级菜单
│   ├── step 2: [等待下拉菜单出现]
│   ├── step 3: click(menu_path[1])  // 点击子菜单
│   ├── step 4: [如果还有更深层级，继续]
│   └── step 5: click(menu_path[-1]) // 点击最终选项
├── 后置条件: 目标菜单项被激活
└── 适用范围: 几乎所有桌面应用
```

```
Skill: fill_form_field(field_label, value)
├── 前置条件: 当前页面有表单
├── 参数: field_label (要填的字段名), value (要填的值)
├── 动作序列:
│   ├── step 1: 在截图中定位 field_label 对应的输入框
│   ├── step 2: click(输入框)
│   ├── step 3: select_all + delete (清空已有内容)
│   └── step 4: type(value)
├── 后置条件: 字段已填入 value
└── 适用范围: 任何表单页面
```

### 1.3 Skill 的三种可能的技术表示

| 表示方式 | 描述 | 优点 | 缺点 |
|---------|------|------|------|
| **A. 自然语言指令** | "点击 File 菜单，选择 Save As，输入文件名，点击 Save" | 简单、可解释、容易生成 | 不精确、无法处理条件分支、难以参数化 |
| **B. 代码/脚本** | Python 函数调用 pyautogui / accessibility API | 精确、可执行、可组合 | 需要 API 接口、跨应用难统一 |
| **C. 参数化子策略 (Sub-policy)** | 一个小的神经网络/LoRA，输入截图+参数，输出动作 | 最灵活、能处理视觉变化 | 训练成本高、难以解释 |

**实际建议：B + C 混合。** 
- 对于确定性高的操作（菜单导航、快捷键）→ 用代码/脚本
- 对于需要视觉判断的操作（scroll to find、在截图中定位元素）→ 用子策略

---

## 二、RL 怎么 "发现" Skill？——三种可行的技术路径

### 路径 1: 从 RL Rollout 中事后挖掘（Post-Hoc Mining）

**核心思想：先正常做 RL 训练（GRPO），然后从产生的大量轨迹中自动挖掘反复出现的成功模式。**

```
┌─────────────────────────────────────────────────────┐
│                  具体流程                             │
│                                                     │
│  Phase 1: 标准 RL 训练                               │
│  ├── Agent 用 GRPO 在 GUI 任务上训练                   │
│  ├── 收集数千条轨迹 (成功 + 失败)                       │
│  └── 每条轨迹: [(screenshot_0, action_0, reward_0),   │
│                  (screenshot_1, action_1, reward_1),   │
│                  ...]                                │
│                                                     │
│  Phase 2: 频繁子序列挖掘                              │
│  ├── 从成功轨迹中提取所有长度 2-10 的动作子序列           │
│  ├── 统计每个子序列的出现频率                           │
│  ├── 过滤: 频率 > 阈值 且 出现在多个不同任务中             │
│  └── 得到候选 skill 集合                              │
│                                                     │
│  Phase 3: VLM 语义聚类 + 命名                         │
│  ├── 用 VLM 分析每个候选 skill 的截图上下文              │
│  ├── 语义相似的子序列聚类 (如不同 app 中的 "保存文件")     │
│  ├── 为每个 cluster 生成名称和参数化描述                  │
│  └── 得到结构化的 skill 定义                           │
│                                                     │
│  Phase 4: Skill-Augmented RL                         │
│  ├── 将发现的 skill 加入 agent 的动作空间               │
│  ├── Agent 现在可以输出: atomic_action OR skill_call    │
│  ├── 用 GRPO 训练 agent 学习何时调用哪个 skill           │
│  └── 不常用/无效的 skill 被淘汰，有效的被强化             │
│                                                     │
│  Phase 5: 迭代 (回到 Phase 1)                        │
│  ├── 用 skill-augmented agent 再做 RL                 │
│  ├── 从新的轨迹中可能发现更高层的 skill                  │
│  └── 例如: skill "打开文件" + skill "编辑内容"          │
│        + skill "保存" → 组合成 "编辑文档" 超级 skill    │
└─────────────────────────────────────────────────────┘
```

**具体例子——RL 怎么发现 "scroll_to_find" skill：**

1. Agent 在 OSWorld 上做 GRPO 训练，遇到很多 "点击页面底部的某个按钮" 的任务
2. 在成功轨迹中，agent 经常做出这样的序列：
   ```
   scroll_down → [观察] → scroll_down → [观察] → scroll_down → click(target)
   ```
3. 这个模式在 30 个不同任务的成功轨迹中出现了 150 次
4. 频繁子序列挖掘算法把它提取出来
5. VLM 分析上下文后命名为 `scroll_to_find(target)`，参数是目标元素的描述
6. 在 Phase 4 中，agent 可以直接输出 `scroll_to_find("Submit button")` 而不是逐步 scroll

**优点：** 实现简单，与现有 GRPO pipeline 兼容，不需要改模型架构
**缺点：** skill 是事后发现的，不是 RL "在线" 发现的，两阶段之间有 gap

---

### 路径 2: Option-Critic 式端到端发现

**核心思想：直接在 RL 训练中学习 "什么是一个好的 skill"，用可微分的方式同时学习 skill 的策略和终止条件。**

```
模型架构:

Input: (screenshot, task_instruction, history)
        │
        ▼
  ┌──────────────┐
  │   VLM Backbone  │  (Qwen2.5-VL-7B)
  │   (共享特征)     │
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│ Meta   │ │ Skill Pool │
│ Policy │ │ (K个skill)  │
│ (选skill)│ │            │
└────┬───┘ └──────┬─────┘
     │            │
     │   选中 skill_i
     │            │
     ▼            ▼
┌─────────────────────┐
│  Skill_i Sub-Policy  │  → 输出 atomic GUI action
│  (LoRA_i adapter)   │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ Termination Network │  → β(s) ∈ [0,1]
│ (这个 skill 该结束了吗?)│     当 β > 0.5 时切换到下一个 skill
└─────────────────────┘
```

**训练方式：**
- Meta Policy 用 GRPO 训练：哪个 skill 在什么场景下最好？
- Sub-Policy 用 GRPO 训练：选定 skill 后，怎么执行最好？
- Termination Network 用 policy gradient 训练：skill 什么时候该结束？

**具体例子——端到端发现 "导航到设置页面" skill：**

1. 初始化 K=20 个空白 skill slot（每个有一个 LoRA adapter）
2. RL 训练开始，各种任务需要 agent 操作不同的 app
3. 经过训练，skill_3 的 LoRA 自动特化为 "在 Settings 类 app 中导航"：
   - 它学会了识别设置图标、侧边栏、分类标签等视觉模式
   - Termination network 学会了在 "到达目标设置页面" 时终止
4. Skill_7 特化为 "文本编辑操作"：选中、复制、粘贴、格式化
5. 最终每个 skill slot 都特化为一种常见操作类型

**优点：** 真正端到端，skill 的发现和使用通过同一个 RL 目标优化
**缺点：** 
- 训练非常不稳定（option-critic 本身就难训练，加上 VLM 更难）
- Skill 不可解释（LoRA adapter 不知道自己学了什么）
- 计算成本高（K 个 LoRA adapter 同时训练）

---

### 路径 3: VLM-Guided Skill Proposal + RL Verification（推荐）

**核心思想：用 VLM 的世界知识来 "提议" 候选 skill，然后用 RL 来验证和优化哪些 skill 真正有用。**

**这是路径 1 和路径 2 的折中，也是我认为最可行的方案。**

```
┌─────────────────────────────────────────────────────┐
│              VLM-Guided Skill Discovery              │
│                                                     │
│  Step 1: VLM Skill Proposer                         │
│  ├── 输入: 一批 GUI 任务描述 + 对应应用的截图             │
│  ├── Prompt: "分析这些任务，列出完成它们可能需要的         │
│  │          可复用的基本操作技能"                        │
│  ├── VLM 输出候选 skill 列表:                          │
│  │   - save_file(filename)                           │
│  │   - open_application(app_name)                    │
│  │   - navigate_menu(path)                           │
│  │   - scroll_to_find(target)                        │
│  │   - fill_form(field, value)                       │
│  │   - switch_window(window_name)                    │
│  │   - ...                                          │
│  └── 每个 skill 附带: 自然语言描述、参数说明、适用场景      │
│                                                     │
│  Step 2: Skill Grounding via RL Rollout              │
│  ├── 对每个候选 skill，从 RL rollout 数据中寻找匹配的      │
│  │   成功动作子序列                                     │
│  ├── 如果找到足够多的匹配 → skill 被 "grounded"          │
│  ├── 如果找不到 → skill 被标记为 "unverified"            │
│  └── Grounded skill 获得具体的动作模板                   │
│                                                     │
│  Step 3: RL-Augmented Training                       │
│  ├── Agent 的动作空间 = {atomic actions} ∪ {skills}     │
│  ├── 用 GRPO 训练:                                    │
│  │   - 调用 skill 且任务成功 → skill 获得高 advantage     │
│  │   - 调用 skill 但效果不如 atomic actions → 低/负 adv   │
│  │   - 不调用 skill 直接用 atomic actions → 正常 reward   │
│  └── RL 自然淘汰没用的 skill，强化有用的 skill            │
│                                                     │
│  Step 4: Skill Refinement & New Discovery            │
│  ├── 对高频使用的 skill，从成功执行中提炼更精确的模板        │
│  ├── 从新的 RL 轨迹中发现 VLM 没有提议到的 skill           │
│  │   (路径 1 的 post-hoc mining)                       │
│  ├── 发现 skill 的组合模式 → 创建更高层的 composite skill  │
│  └── 迭代优化                                         │
└─────────────────────────────────────────────────────┘
```

**具体例子——发现一个人类可能想不到的 skill：**

1. VLM 提议了常见 skill: save_file, open_app, navigate_menu, ...
2. Agent 在 RL 训练中反复执行 OSWorld 任务
3. Post-hoc mining 从成功轨迹中发现了一个 VLM 没提议的模式：
   ```
   在 LibreOffice Calc 中，agent 经常做：
   click(cell_A1) → Ctrl+Shift+End → Ctrl+C → click(目标位置) → Ctrl+V
   ```
   这是 "选中从当前位置到表格末尾的所有内容并复制" 的快捷键操作
4. VLM 分析后命名为 `select_all_below_and_copy(start_cell)`
5. 这个 skill 在多个 Calc 任务中被复用，显著提升了效率
6. **人类构建 CUA-Skill 时不一定会想到这种组合快捷键模式，但 RL 从大量试错中发现了它**

---

## 三、RL 在这里的核心角色是什么？

很多 skill library 工作（Voyager、CUA-Skill、WALT）不用 RL。**那 RL 的不可替代价值在哪里？**

### 3.1 RL 解决了三个非 RL 方法解决不了的问题

| 问题 | 非 RL 方法的局限 | RL 的优势 |
|------|----------------|---------|
| **Skill 的边界在哪？** | 人工定义或 LLM 猜测 → 可能不是最优粒度 | RL 的 termination learning 自动发现最优的 skill 边界 |
| **什么时候该用 Skill？** | 规则匹配或 LLM 判断 → 不考虑长期收益 | RL 的高层策略优化 skill 选择，考虑全局最优 |
| **Skill 执行的鲁棒性** | 固定脚本遇到 UI 变化就失败 | RL 训练的子策略能处理视觉变化和异常情况 |

### 3.2 具体举例：为什么 RL 比 "直接用 LLM 构建 skill" 更好

**场景：** 在 Firefox 中下载文件并保存到指定目录

**CUA-Skill 方式（人工构建）：**
```
Skill: download_and_save(url, target_dir)
  1. click(地址栏)
  2. type(url)
  3. press(Enter)
  4. [等待页面加载]
  5. right_click(下载链接)
  6. click("Save Link As...")
  7. [在保存对话框中导航到 target_dir]
  8. click("Save")
```
问题：
- 如果下载链接不需要右键而是直接点击呢？
- 如果浏览器弹出了 "是否允许下载" 的权限对话框呢？
- 如果保存对话框的默认目录不同呢？
- 每种异常情况都需要人工预见并编码

**RL-Discovered Skill 方式：**
- Agent 通过大量 RL 交互，在各种下载场景中试错
- 自动学会了处理各种边界情况（因为 RL 的 exploration 会遇到这些情况）
- Sub-policy 是一个 VLM，能根据 **当前截图** 动态决定下一步操作
- 不是固定脚本，而是 **能理解视觉上下文的条件策略**

### 3.3 RL 的角色总结

```
Skill Library 的完整闭环:

VLM 世界知识 → [提议候选 skill]
      +
RL Rollout 数据 → [挖掘频繁模式] → [发现新 skill]
      +
RL Training → [优化何时用哪个 skill] → [优化 skill 内部执行策略]
      +
RL 淘汰机制 → [去除无用 skill] → [保留有效 skill]
      │
      ▼
持续迭代，skill 库越来越好
```

**一句话总结 RL 的角色：VLM 负责 "skill 可能是什么"（knowledge-driven），RL 负责 "skill 是否真的有用、怎么用最好"（data-driven）。两者缺一不可。**

---

## 四、实操层面的关键设计选择

### 4.1 Skill 在模型中怎么表示？

**推荐方案：** Skill 作为 VLM 输出中的特殊 token 序列

```
标准 agent 输出:
  Thought: 我需要保存这个文件
  Action: click(x=120, y=45)

Skill-augmented agent 输出:
  Thought: 我需要保存这个文件
  Action: <skill>save_file_as</skill>(filename="report.pdf")
```

训练时，当 agent 输出 `<skill>save_file_as</skill>(filename="report.pdf")` 时：
- Execution engine 展开这个 skill 为具体的 atomic action 序列
- 在环境中逐步执行
- 整个 skill 的成功/失败作为 reward 反馈给 agent

### 4.2 一个重要的 Alternative 思路——或许更可行

实际上，还有一种更简单但可能更有效的 formulation：

**不把 skill 建模为 "macro-action"，而是建模为 "context injection"。**

```
没有 skill 的 agent:
  System prompt: 你是一个 GUI agent...
  User: 请在 LibreOffice 中将文件保存为 PDF
  Agent: [从零开始推理每一步该做什么]

有 skill 的 agent:
  System prompt: 你是一个 GUI agent...
  
  可用技能库:
  - save_file_as(filename): 点击 File → Save As → 输入 filename → 点击 Save
  - export_as_pdf(): 点击 File → Export as PDF → 确认设置 → 点击 Export
  - navigate_menu(path): 依次点击菜单路径中的每一项
  
  User: 请在 LibreOffice 中将文件保存为 PDF
  Agent: 我应该使用 export_as_pdf() 技能
         Step 1: [按照技能描述执行]
```

在这种 formulation 下：
- **Skill discovery = 发现哪些 "context injection" 对 agent 的成功率帮助最大**
- **RL 的角色 = 优化 "什么样的 skill 描述应该被注入到 context 中"**
- 不需要改模型架构，只需要优化 prompt 中的 skill library

这实际上与 SkillRL 和 MetaClaw 的路线更接近，但可以用 **GUI-specific 的 visual grounding** 来区分。

---

## 五、我的诚实评估

### 值得做的理由
1. Gap 确实存在（详见调研报告）
2. GUI 场景天然适合 skill abstraction（操作有明显的层次性）
3. Skill reuse 能带来实际的效率提升（减少轨迹长度）
4. 与你组的 DART/TongUI 基础设施能对接

### 需要注意的风险
1. **"RL 发现 skill" 的定义可能不够清晰**：如果 reviewer 质疑 "这不就是 post-hoc 提取 + 检索增强吗？RL 在哪？"，需要有坚实的回答
2. **路径 1（post-hoc mining）不够 "RL"**：reviewer 可能认为这只是数据挖掘，不是真正的 RL contribution
3. **路径 2（option-critic）太难做**：VLM + option-critic 的训练稳定性是个大问题
4. **路径 3 是最实际的**，但需要精心设计 RL 的角色，让它不只是 "选择 skill" 这么简单

### 如果要做，最推荐的策略
**路径 3 (VLM-Guided + RL Verification) 为主，路径 1 (Post-Hoc Mining) 为辅：**
- 用 VLM 提议 + rollout mining 发现 skill → 解决 "怎么发现"
- 用 hierarchical GRPO 训练 skill selection + execution → 解决 "怎么用"
- 用 RL reward signal 做 skill 淘汰 + 精炼 → 解决 "怎么进化"
- 在论文中，关键是展示 **"RL 发现了人/LLM 想不到的 skill" 的涌现案例**
