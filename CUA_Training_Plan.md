# CUA RL 训练执行计划

> **前提**：已有不错的基础模型（SFT / Grounding 已具备）  
> **聚焦**：RL 阶段，Linux (Ubuntu) 先行，对齐 OSWorld 应用  
> **约束**：标注人力有限、API quota 充足  
> **核心参考**：EvoCUA

---

## 一、我们要做什么

用 RL 把现有 SFT 模型从当前 baseline 提升到 OSWorld 50+ 分。

EvoCUA 的核心经验：5K 轨迹冷启动 → 多轮 RFT → 51 分 → DPO 关键步骤 → 55 分。整个过程的瓶颈不在模型、不在算法，而在 **沙盒环境 × Verifier × 任务池** 三件事的规模和质量。

我们的策略：先把这三件基础设施搭好，然后进入 RL 迭代循环。

---

## 二、OSWorld 应用范围与 Task 池规划

OSWorld 的 369 个 Ubuntu 任务分布在 10 个 domain：

| Domain | 任务数 | 应用 | Verifier 难度 | 我们目标生成量 |
|--------|--------|------|-------------|-------------|
| os | 24 | Nautilus/Terminal/Settings | **低**（shell 命令检查文件/配置） | 800 |
| chrome | 46 | Chrome | **低**（prefs JSON / CDP） | 500 |
| vs_code | 23 | VS Code | **低**（settings.json / extension list） | 400 |
| libreoffice_calc | 47 | Calc | **中**（需 compare_table, 要准备 gold 文件） | 500 |
| libreoffice_writer | 23 | Writer | **中**（需 compare_docx） | 300 |
| libreoffice_impress | 47 | Impress | **中**（需 compare_pptx） | 300 |
| gimp | 26 | GIMP | **高**（图像比对精度有限） | 150 |
| thunderbird | 15 | Thunderbird | **中**（prefs.js 检查） | 100 |
| vlc | 17 | VLC | **中**（config 文件检查） | 100 |
| multi_apps | 93 | 跨应用组合 | **中**（组合多个 verifier） | 350 |
| **合计** | **361** | | | **~3500** |

**优先顺序**：先做 Verifier 难度低的（os → chrome → vs_code），因为 RL 信号越精确效果越好。LibreOffice 系列第二批。GIMP/Thunderbird/VLC 第三批。

---

## 三、Task 自动生成方案

> 核心思路：人工定义模板和质量标杆（少量），LLM 批量扩写（大量），自动化验证（过滤）

### 3.1 OSWorld 的 Verifier 长什么样

研究了 OSWorld 全部 369 个 task 的 JSON 结构后，提炼出以下模式。每个 task 有三部分：

1. **config**（初始状态）：创建文件、打开应用、下载素材
2. **instruction**（自然语言任务描述）
3. **evaluator**（验证器）：postconfig → getter → metric function → expected value

最常用的 5 种 verifier 模式：

| 模式 | 使用频率 | 原理 | 适用 domain |
|------|---------|------|------------|
| **命令输出检查** | ~55 个 task | 在 VM 里跑 shell 命令，检查输出包含/不包含特定字符串 | os, vs_code, chrome, thunderbird |
| **文件比对** | ~100 个 task | 把 VM 里的文件拉出来，和 gold answer 文件逐字段比对 | calc(compare_table), writer(compare_docx), impress(compare_pptx) |
| **精确匹配** | ~13 个 task | 命令输出必须完全等于预期值 | chrome settings, gsettings |
| **JSON 配置检查** | ~18 个 task | 解析 JSON/prefs 文件，检查特定 key-value | vs_code(settings.json), thunderbird(prefs.js) |
| **图像比对** | ~7 个 task | 像素级或结构相似度比对 | gimp |

### 3.2 生成流程（三步走）

**第一步：Seed 生成（LLM 批量）**

对每个 domain：
1. 人工写 5-10 个高质量 exemplar task（完整的 instruction + config + evaluator JSON），作为 few-shot 示例
2. 给 LLM 定义该 domain 可用的 verifier 模式（只允许用上面 5 种中对应的那种）
3. LLM 按 few-shot + 约束批量生成 50-100 个 task
4. 每个 domain 产出 ~50 个 seed task

目标：**500 个 seed tasks**

**第二步：验证与过滤**

两层过滤：
- **结构验证**：JSON 格式是否正确、evaluator 的 func 名是否是 OSWorld 已有的、result type 是否合法、必填字段是否完整
- **Sanity 验证**：在一个干净环境上跑 verifier——agent 什么都没做，verifier 应该返回 fail。如果返回 pass，说明这是 false positive，直接淘汰

人工抽检每个 domain 的 10-20% 样本，修正 LLM 的常见错误模式，然后反馈到 prompt 迭代。

预期通过率 ~80%，剩 **~400 个 validated seeds**。

**第三步：扩量**

三种扩量策略，全部用 LLM：

| 策略 | 方法 | 倍率 |
|------|------|------|
| **参数变异** | 同一个 task 结构，换文件名/路径/文本内容/设置值 | 5x |
| **难度升级** | 给 task 加条件（"如果 X 则做 Y"）、加多目标、加约束 | 1x |
| **跨应用组合** | 从不同 domain 各取一个 task，让 LLM 组合成一个 multi-app workflow | 产出 ~300 |

扩量后全量重跑验证。

| 阶段 | 产出 |
|------|------|
| 500 seeds | → 验证后 ~400 |
| 参数变异 5x | → ~2000 |
| 难度升级 1x | → ~400 |
| 跨应用组合 | → ~300 |
| 全量验证后 | → **~2500** |
| 再迭代一轮 | → **3000-3500** |

### 3.3 LibreOffice 系列的特殊处理

compare_table / compare_docx / compare_pptx 这类 verifier 需要一个 **gold answer 文件**（正确完成任务后文档应该长什么样）。

这些 LLM 很难自动生成。方案：
- **LLM 负责生成** instruction + config（初始文件 + 打开应用）
- **Gold answer 文件由脚本生成**：用 python-docx / openpyxl / python-pptx 编程构造初始文件和 gold 文件
- 或者：用强模型（GPT-4o）在沙盒里实际执行任务，人工确认结果正确后，把结果文件存为 gold answer

这块需要单独安排人做，工作量比 os/chrome/vscode 域大。

---

## 四、沙盒环境

### 4.1 Docker 镜像

一个 Ubuntu 24.04 GNOME 镜像，预装 OSWorld 全部应用：

```
Firefox, Chrome, LibreOffice (Writer/Calc/Impress), VS Code,
GIMP, Thunderbird, VLC, Nautilus, Terminal, Settings, Text Editor
+ 截图服务 (1080p) + pyautogui/xdotool + 环境 agent（接收命令/返回截图）
```

### 4.2 关键指标

| 指标 | 要求 |
|------|------|
| 重置速度 | < 10s |
| 截图 | 1080p 采集 → 720p 输入 |
| 每个 task 独立初始状态 | config 脚本自动设置 |
| Verifier 执行 | 在容器内跑命令 → 返回输出 |

### 4.3 分布式架构（参考 DART-GUI）

四个模块完全解耦异步：

| 模块 | 职责 |
|------|------|
| **Env Cluster** | K8s 管理 Docker 容器池，按需扩缩 |
| **Rollout Service** | vLLM 多 worker 推理 |
| **Data Manager** | 轨迹存储 + 任务调度 + Experience Pool |
| **Trainer** | verl/FSDP，异步接收 trajectories 做 GRPO 更新 |

以单条轨迹为最小调度单元（rollout-wise），逐 worker 渐进式模型同步。

---

## 五、RL 训练流程

### 5.1 Cold-start（视 baseline 决定）

| 当前 OSWorld SR | 决策 |
|----------------|------|
| >15% 且格式正确 | 跳过，直接 RL |
| 5-15% | 轻量 cold-start ~2K 轨迹 |
| <5% | 需要 ~5K 轨迹 |

Cold-start 数据：强模型（GPT-4o / Claude）在沙盒执行 → 仅保留 verifier 通过的 → 每 query 留 4-5 条轨迹（EvoCUA 经验：同 query 多轨迹 > 更多 query）。

配比参考 EvoCUA：50% 通用 + 35% 普通步骤 + 15% 关键步骤。

### 5.2 多轮 RFT

每轮循环：

```
模型 rollout (2000-4000 并发, 每 query 采 8-16 条)
  → Verifier 验证
  → 成功轨迹做 Reject Sampling SFT（混 30-50% 通用数据防 collapse）
  → 评测
  → 扩 query 池 / 提难度 → 下一轮
```

EvoCUA 参考：多轮 RFT → 51 分。减少数据也能 51，说明迭代质量 > 一次性堆量。

### 5.3 Entropy Collapse 应对（Entropulse）

~100-200 training steps 后通常触顶。收集当前所有成功 rollout → SFT 一轮（LR 降半）→ 恢复 entropy → 继续 RL。来自 Computer-RL 的实证方案。

### 5.4 DPO on 关键步骤

EvoCUA 验证：关键步骤 DPO 比全轨迹 DPO 更高效，+4 分（51 → 55）。

关键步骤 = 不可逆操作 / 分支决策点 / 末步 save-submit。

偏好对来源：同 query 成功 vs 失败轨迹中的关键步骤。

---

## 六、分工

### 角色 A：Task 生成（2 人，Week 1-3）

> 核心交付：3000+ query + verifier，OSWorld JSON 格式

| Week | 任务 |
|------|------|
| W1 前半 | 为 os / chrome / vs_code 三个 domain 各手写 5-10 个 exemplar task（完整 JSON），作为 LLM few-shot |
| W1 后半 | 用 LLM 批量生成 os(100) + chrome(100) + vs_code(100) seed tasks |
| W1 后半 | 写结构验证 + sanity 验证脚本，跑第一轮过滤 |
| W1 末 | 人工抽检每 domain 20 个，记录 LLM 常见错误，修正 prompt |
| W2 前半 | 第二轮生成（修正后），覆盖 calc / writer / impress / thunderbird / vlc |
| W2 前半 | LibreOffice 系列：写脚本批量构造初始文件 + gold answer 文件 |
| W2 后半 | 三种扩量（参数变异 5x + 难度升级 + 跨应用组合） |
| W2 末 | 全量验证，目标 2500+ validated tasks |
| W3 | 迭代到 3000+，查漏补缺，按 domain 均衡化 |

**交付物**：
- 每个 domain 的 exemplar task 文件（few-shot 标杆）
- 生成 + 验证 + 扩量的脚本
- 最终的 task pool（OSWorld JSON 格式）
- 验证报告（通过率、domain 分布、难度分布）

### 角色 B：沙盒环境（2-3 人，Week 1-4）

> 核心交付：可快速重置的 Docker 环境 + 分布式管理器

| Week | 任务 |
|------|------|
| W1 | Docker 镜像制作（Ubuntu 24.04 + OSWorld 全部应用 + 截图/动作基础设施） |
| W1 | 镜像内环境 agent 调通（接收命令 → 执行 → 返回截图/命令输出） |
| W2 | 快速重置机制（< 10s），task 初始状态注入 |
| W2 | 与 Task 池对接：给定 task JSON，自动 init → 等待 agent → 跑 verifier → 返回 reward |
| W3 | K8s 编排，能管理 100+ 并发容器 |
| W3 | vLLM rollout service 部署 |
| W4 | 扩容到 2000+，压测稳定性 |

**交付物**：
- Docker 镜像 + Dockerfile
- 环境 agent 服务（REST API：reset / screenshot / execute / verify）
- K8s 部署配置
- 端到端联调报告（10 并发 mini RL loop 跑通）

### 角色 C：训练（2 人，Week 3 开始）

> 核心交付：从 baseline 到 OSWorld 50+

| Week | 任务 |
|------|------|
| W1-2 | 跑当前 SFT 模型的 OSWorld baseline（369 tasks） |
| W1-2 | 分析失败 case 分布（grounding 错 / 规划错 / 格式错 / 能力缺失），输出报告 |
| W3 | 根据 baseline 决定是否做 cold-start SFT |
| W3-4 | 如需 cold-start：用强模型在沙盒生成 teacher 轨迹 → SFT |
| W5-6 | RFT Round 1-2（小规模：100-500 并发） |
| W6-8 | 扩容到 2000+ 并发，RFT Round 3-5 |
| W8 | 如遇 entropy collapse → Entropulse |
| W9-10 | 继续 RFT 迭代 |
| W10-12 | 关键步骤 DPO |
| W12-14 | 最终评测，model merge 实验 |

**交付物**：
- Baseline 分析报告
- 每轮 RFT 后的评测数据（OSWorld 50-task subset + 全量）
- Entropy 监控看板
- 最终模型 checkpoint

### 角色 D：分析与策略（1 人，贯穿全程）

| 职责 |
|------|
| 每轮 RFT 后分析失败 case，定位瓶颈（是 task 覆盖不够？verifier 有噪声？grounding 弱？） |
| 根据分析结果指导 Task 生成团队补充特定类别任务 |
| 设计 entropy 监控方案（什么指标、什么阈值触发 Entropulse） |
| 设计关键步骤识别策略 |
| 对比实验设计（GRPO vs PPO、rollout 数量、DPO 粒度等） |

---

## 七、Timeline 与里程碑

```
Week 1-2    ▍Task 生成▍ seed → validate → augment → 2500+
            ▍沙盒基建▍ Docker 镜像 + 环境 agent
            ▍训练▍    跑 baseline + 失败分析

Week 3      ▍Task▍    扩到 3000+
            ▍沙盒▍    K8s + 100 并发 + vLLM，跑通 mini RL loop
            ▍训练▍    决定是否 cold-start

Week 4-5    ▍沙盒▍    扩容到 2000+
            ▍训练▍    Cold-start SFT (如需) → RFT Round 1

Week 5-8    ▍训练▍    多轮 RFT (核心阶段)
            ▍Task▍    根据分析补充 task，持续迭代 verifier

Week 8-10   ▍训练▍    Entropulse (如需) → 继续 RFT

Week 10-14  ▍训练▍    DPO 关键步骤 → 最终评测
```

**关键里程碑**：

| 时间 | 里程碑 | 验收标准 |
|------|--------|---------|
| Week 2 末 | Task 池就绪 | 2500+ validated tasks，domain 覆盖完整 |
| Week 3 末 | RL 基建跑通 | 10 并发 mini RL loop 端到端成功 |
| Week 5 | 首轮 RFT 完成 | OSWorld SR 有明显提升 |
| Week 8 | 大规模 RL 阶段 | 2000+ 并发稳定运行，OSWorld >30 |
| Week 12 | RFT 收敛 | OSWorld >45 |
| Week 14 | DPO 完成 | OSWorld >50 |

---

## 八、风险

| 风险 | 影响 | 对策 |
|------|------|------|
| LLM 生成的 verifier 质量不够 | RL 信号有噪声 | 三层过滤（结构 + sanity + 人工抽检）；先做 os/chrome/vscode 这些 verifier 最简单可靠的 domain |
| LibreOffice 系列 gold answer 难造 | 这些 domain task 量不够 | 用脚本 (openpyxl/python-docx) 批量构造；或强模型执行 + 人工确认 |
| 并发环境扩容慢 | RL 迭代效率低 | 先用 Docker（比 VM 扩容快得多），优先跑轻量应用 task |
| Entropy collapse | RL 性能停滞 | 提前设计 entropy 监控，及时 Entropulse |
| Task 池多样性不足导致过拟合 | 模型只会做特定模式的任务 | 三种扩量策略 + 持续分析 + 补充新类别 |
| Baseline 很低（<5%） | 需要更长的 cold-start | 用多个强模型 teacher 采集轨迹，按难度分层 |
