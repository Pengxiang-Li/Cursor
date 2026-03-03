# CUA RL 训练执行计划

> **前提**：已有不错的基础模型（SFT / Grounding 能力已具备），本计划聚焦 RL 阶段  
> **核心参考**：EvoCUA（5K 轨迹冷启动 → 多轮 RFT → OSW 51 → DPO → 55）  
> **辅助参考**：Computer-RL（Entropulse / API-GUI Paradigm）、DART-GUI（工程架构）  
> **核心公式**：RL 上限 = min(沙盒规模, Verifier 质量, 任务多样性)

---

## 0. 当前状态与目标

| 维度 | 现状 | 目标 |
|------|------|------|
| 基础模型 | SFT + Grounding 已完成 | — |
| OSWorld SR | ? (先测 baseline) | >30%，争取 50+ |
| RL Query 池 | 无 | 3000-5000 query + verifier |
| RL 环境 | 无 | 2000-4000 并发 |
| Verifier | 无 | 3000-5000 个，模型生成为主 |

---

## 1. 总体路线（EvoCUA 风格）

```
已有 SFT 模型
     │
     ▼
[Cold-start SFT] ← 少量高质量轨迹（~5K），格式对齐 + 关键步骤 upsampling
     │
     ▼
[RFT Round 1] ← 模型 rollout → Verifier → 成功轨迹回收 → reject sampling SFT
     │
     ▼
[RFT Round 2..N] ← 循环迭代，每轮扩任务池 / 提高难度
     │              EvoCUA: 多轮 RFT → OSW 51
     ▼
[Offline DPO] ← 关键步骤级别偏好学习
     │            EvoCUA: +4 分，到 55
     ▼
[Model Merge] ← 可选：多平台 vertical agents 参数插值
```

**EvoCUA 关键数字**：
- 冷启动 5K 轨迹，每 query 平均 4-5 条正确轨迹
- 总计 ~5000 query + verifier，实际用 ~3000
- Verifier 全部模型生成，无人工
- RL 需 2000-4000 并发环境
- 多轮 RFT → 51；减少数据也能 51；加 DPO → 55

---

## 2. Phase 0: RL 基建（第 1-3 周）

> 最重要的事，也是最容易低估工时的事。EvoCUA 原话："最重视 scaling，沙盒还有 verifier"

### 2.1 沙盒环境 [Infra, 2-3 人]

| Task | 交付物 | 工时 |
|------|--------|------|
| Ubuntu 24.04 Docker 镜像（预装 Firefox, LibreOffice, VS Code, Terminal, Files, Settings, GIMP） | `Dockerfile` + 镜像 | 3d |
| Windows 11 VM 快照模板（预装 Office, Chrome, VS Code, Explorer, Settings） | VM 模板 | 3d |
| macOS VM 模板（如有资源，否则先 skip） | VM 模板 | 3d |
| 快照/重置机制：Docker commit/restore 或 VM snapshot，**< 10s 重置** | `reset_env.sh` | 2d |
| 任务初始状态预配置脚本（每个任务的起始文件/应用状态） | `task_init/` 目录 | 持续 |
| 截图服务（1080p 采集 → 720p 输入） | `screenshot.py` | 1d |

**先 Linux Docker 跑通，Windows VM 第二优先，macOS 第三。**

### 2.2 分布式环境管理器 [Infra]

> 参考 DART-GUI 四模块解耦异步架构

```
┌─────────────┐   ┌─────────────────┐   ┌──────────────┐   ┌───────────┐
│ Env Cluster  │◀─▶│ Rollout Service  │──▶│ Data Manager │──▶│  Trainer  │
│ K8s Docker   │   │ vLLM workers    │   │ MySQL/Redis  │   │ verl/FSDP │
│ 2000-4000    │   │ 多 worker 推理   │   │ 轨迹/任务调度 │   │ GRPO 更新  │
└─────────────┘   └─────────────────┘   └──────────────┘   └───────────┘
```

| Task | 交付物 | 工时 |
|------|--------|------|
| K8s 编排脚本，支持按需扩缩 Docker 实例 | `k8s/` | 5d |
| Rollout Service：vLLM 部署，支持多 worker 并行推理 | `rollout_service/` | 3d |
| Data Manager：MySQL 存轨迹 + 任务调度 + Experience Pool | `data_manager/` | 3d |
| Trainer 对接：异步接收 filtered trajectories，做 GRPO 更新 | 对接 verl | 3d |
| 端到端跑通：10 并发环境 + 1 worker rollout + 1 trainer | 集成测试 | 2d |

**里程碑**：第 3 周末能在 10 并发环境上跑完一次 mini RL loop（rollout → verify → train → rollout）。

### 2.3 Baseline 测试 [Train]

| Task | 交付物 |
|------|--------|
| 当前 SFT 模型在 OSWorld 369 tasks 跑分 | baseline SR |
| 当前 SFT 模型在 ScreenSpot-Pro 跑分 | baseline Acc |
| 分析模型失败 case：grounding 错误 / 规划错误 / 格式错误 / 能力缺失 | 错误分布报告 |

**这个 baseline 非常重要**，决定了冷启动 SFT 是否还需要、以及 RL 的起点在哪。

---

## 3. Phase 1: Query 池 + Verifier 构建（第 2-5 周，与 Phase 0 并行）

> EvoCUA: ~5000 query + verifier，实际用 ~3000。Verifier 全部模型生成。
> 这是 RL 的燃料，质量和数量直接决定上限。

### 3.1 任务(Query)设计 [Data + Research]

**目标**：3000-5000 个 query，覆盖多应用、多难度

**来源 1：从 Benchmark 复用**

| 来源 | 数量 | 备注 |
|------|------|------|
| OSWorld | 369 | 已有 verifier 框架，直接用 |
| Windows Agent Arena | 154+ | 已有 eval 逻辑 |
| AssistGUI | 100 | 专业软件任务 |
| Computer-RL SpreadsheetBench/PPTC | 数百 | 表格/PPT 相关 |

**来源 2：LLM 批量生成**

| Step | 操作 |
|------|------|
| 1 | 定义应用-功能矩阵（见下表） |
| 2 | 对每个 (应用, 功能) 对，用 LLM API 生成 20-50 个变体 query |
| 3 | 按难度打标签：easy / medium / hard / expert |
| 4 | 为每个 query 同时让 LLM 生成 verifier（见 3.2） |

**应用-功能矩阵（Linux 优先，~30 应用 × ~10 功能）**：

| 应用 | 核心功能 | 预期 query 数 |
|------|----------|---------------|
| Files (Nautilus) | 创建/移动/删除/重命名/搜索/权限 | 200 |
| Firefox/Chrome | 导航/搜索/书签/下载/标签管理/表单填写 | 500 |
| LibreOffice Writer | 排版/表格/插图/导出PDF/查找替换/页眉页脚 | 400 |
| LibreOffice Calc | 公式/格式/筛选/排序/图表/数据验证 | 400 |
| LibreOffice Impress | 幻灯片/布局/动画/母版/导出 | 200 |
| Terminal | 文件操作/包管理/进程/网络/脚本 | 300 |
| VS Code | 打开/编辑/搜索/安装扩展/终端/Git | 300 |
| Settings (GNOME) | 网络/显示/声音/主题/快捷键 | 200 |
| Text Editor | 编辑/保存/格式/搜索 | 100 |
| GIMP | 裁剪/调色/图层/文字/导出 | 200 |
| 跨应用工作流 | 浏览器→Writer/从终端整理到Calc/... | 200 |

**来源 3：指令复杂化（参考 UI-TARS-2）**

在已有 query 基础上用 LLM 做增广：
- **Multi-Condition Obfuscation**：附加混淆条件（"如果当前是暗色主题则先切换到亮色主题"）
- **Multi-Hop Chain**：多跳条件链（"先搜索 X，然后根据结果做 Y"）

### 3.2 Verifier 构建 [Env + Data]

> EvoCUA: Verifier 全部由模型生成和修改，无人工参与。

**构建流程**：

```
1. LLM 生成 query 时，同时生成该 query 的 verifier 伪代码
2. LLM 将伪代码转为可执行 Python 脚本
3. 在沙盒中试运行 verifier（无 agent 操作 → 应返回 fail）
4. 人工抽检 10-20% 确认 verifier 逻辑正确
5. 有问题的回 LLM 修改
```

**Verifier 分层策略**：

| Tier | 方式 | 适用任务 | 预期覆盖 |
|------|------|----------|----------|
| **Tier 1: Rule-based** | 检查文件系统状态 / 应用配置 / 文档内容解析 | 文件管理、终端、设置、文本编辑 | ~40% query |
| **Tier 2: Document Parse** | UNO API 解析文档结构 / Playwright 检查 DOM | Office 套件、浏览器 | ~30% query |
| **Tier 3: LLM-as-Judge** | 任务指令 + 初始截图 + 最终截图 → 成功/失败 | 复杂视觉任务、跨应用 | ~30% query |

**Tier 1 Verifier 示例**（文件管理）：

```python
def verify_task(env):
    """Task: 在 ~/Documents 下创建名为 'report' 的文件夹，并在其中创建 notes.txt"""
    dir_exists = os.path.isdir(os.path.expanduser("~/Documents/report"))
    file_exists = os.path.isfile(os.path.expanduser("~/Documents/report/notes.txt"))
    return 1.0 if (dir_exists and file_exists) else 0.0
```

**Tier 3 LLM-as-Judge Prompt 模板**：

```
你是一个 GUI 任务评判器。
任务指令：{instruction}
初始截图：{screenshot_before}
最终截图：{screenshot_after}
操作历史：{action_history}

请判断任务是否成功完成。输出 JSON：{"success": true/false, "score": 0.0-1.0, "reason": "..."}
```

**交付物**：
- `verifier_generator.py` — 输入 query，LLM 自动生成 verifier
- `verifier_runner.py` — 在沙盒中执行 verifier
- `verifiers/` — 所有 verifier 脚本
- `query_pool.json` — 全部 query + 元数据 + verifier 路径

### 3.3 任务初始状态配置 [Env]

每个 query 需要一个确定的环境初始状态：

| Task | 操作 |
|------|------|
| 为每个 query 写 `init_state.sh` | 创建所需文件/打开应用/设置初始内容 |
| 将初始状态固化为 Docker snapshot 或 restore 脚本 | 重置后即进入该 query 的初始状态 |
| LLM 辅助生成 init 脚本 | 与 query 和 verifier 一起生成 |

---

## 4. Phase 2: Cold-start SFT（第 4-5 周）

> EvoCUA 冷启动配比：50% 通用 + 35% 普通步骤 + **15% 关键步骤**
> EvoCUA 冷启动仅 5K 轨迹。质量 >> 数量。

### 4.1 判断是否需要 Cold-start

基于 Phase 0 的 baseline 结果决策：

| Baseline 情况 | 决策 |
|---------------|------|
| OSWorld >15%，格式正确率 >90% | 可以跳过 cold-start，直接进 RL |
| OSWorld 5-15%，格式基本正确 | 轻量 cold-start（~2K 轨迹），主要对齐输出格式和 CoT |
| OSWorld <5% 或格式问题严重 | 需要 cold-start（~5K 轨迹），对齐动作空间 + CoT + 基本能力 |

### 4.2 Cold-start 数据准备（如需要）

**数据量**：~5K 轨迹（参考 EvoCUA）

**来源**：
1. 用多个强模型（GPT-4o, Claude-3.5-Sonnet）作为 Teacher，在沙盒中执行 query，录制轨迹
2. 仅保留 Verifier 验证通过的成功轨迹
3. 同一 query 保留多条轨迹（EvoCUA: 每 query 4-5 条 → 更好的 policy space 覆盖）

**配比（EvoCUA 方案）**：

```
通用数据（防止 mode collapse）       50%
普通步骤轨迹                         35%
关键步骤轨迹（upsampling）           15%
```

**关键步骤识别**：
- 不可逆操作（删除、提交、保存）
- 分支决策点（条件判断后选择哪条路径）
- 末步（save / submit / confirm）
- 失败轨迹中第一个偏离正确路径的步骤

**CoT 格式**（Mano 验证 +2.8，必须用）：

```
<think>
[Observation] 当前界面状态描述
[Memory] 任务目标和已完成进度
[Thought] 下一步推理
</think>
<summary>一句话动作摘要</summary>
<action>click(x=320, y=28)</action>
```

**训练配置**：

```
超参: LR 5e-6, BS 128, Epochs 2-3
策略: 历史帧 = 前 2 帧截图 + 全部历史文本摘要（Mano 最优）
```

---

## 5. Phase 3: 多轮 RFT（第 5-12 周）— 核心阶段

> EvoCUA 的核心：多轮 RFT（Rejection Fine-Tuning），即 rollout → verify → 收集成功轨迹 → SFT → 循环
> 多轮 RFT → OSW 51 分

### 5.1 RFT Round 1

**步骤**：

```
1. 当前模型在 Query 池中 rollout
   - 每 query 采样 N 条轨迹（N=8-16，DART-GUI 动态调 N）
   - 2000-4000 并发环境

2. Verifier 验证每条轨迹
   - 成功轨迹 → 进入正样本池
   - 失败轨迹 → 进入负样本池（后续 DPO 用）

3. 成功轨迹做 Reject Sampling SFT
   - 仅用成功轨迹做一轮 SFT
   - 混入部分通用数据防 collapse

4. 评测 → 更新 checkpoint
```

**超参**：

```
Rollout:
  - 每 query 采样 N=8-16 条轨迹
  - 最大步数: 按任务历史成功轨迹动态设定（DART-GUI）
  - 温度: 0.7-1.0（保证多样性）

SFT (on successful rollouts):
  - LR: 5e-6（Computer-RL Entropulse 参考）
  - Epochs: 1
  - 混入通用数据 30-50%
```

### 5.2 RFT Round 2..N — 迭代飞轮

每轮迭代做以下事情：

```
Round K:
  1. 用 Round K-1 的模型 rollout
  2. Verifier 验证
  3. 收集新的成功轨迹，与历史成功轨迹合并
  4. SFT（或 GRPO）
  5. 评测

扩展策略（每轮可选一个或多个）:
  a. 扩大 Query 池（加入新任务）
  b. 提高难度（用 LLM 对简单 query 做条件复杂化）
  c. 增加采样数 N
  d. 加入更多 OS 的任务（Win → macOS）
```

**关键经验（EvoCUA）**：
- 一个 query 多条轨迹 > 更多 query（同一任务的不同解法更有价值）
- 减少数据量不一定掉分（质量 > 数量）
- 多轮迭代比一次性大规模训练效果好

### 5.3 可选升级：Step-level GRPO

> 如果 RFT 效果触顶，可以切换到 Online RL

```
算法: Step-level GRPO（Computer-RL / DART-GUI）

Reward:
  R_task   = Verifier 结果（成功=1, 失败=0）
  R_format = 代码可解析=0 / 不可解析=-1 / 坐标越界=-0.5
  R_total  = R_task + R_format

Credit assignment: 成功轨迹上所有格式正确的 step 获得 r=1

KL: β=0.0003

预期: ~100-200 training steps 后 entropy collapse
```

### 5.4 Entropulse（如遇 Entropy Collapse）

> Computer-RL 独创，解决 RL 后期 entropy 下降问题

```
触发条件: entropy 监控显示显著下降 + 性能不再提升

操作:
  1. 收集当前 RL 阶段所有成功 rollout
  2. 用这些数据做一轮 SFT（恢复 entropy）
  3. LR = 上一次 SFT 的 1/2（Computer-RL: 5e-6）
  4. 加载新权重，继续 GRPO

效果: 打破性能瓶颈，允许继续 RL
```

### 5.5 DART-GUI 自适应策略（推荐采用）

| 策略 | 作用 | 实现 |
|------|------|------|
| Dynamic Rollout Number | 成功率高的 query 减少采样，省算力给难 query | 根据实时成功率动态调 N |
| Dynamic Trajectory Length | 每个 query 的最大步数基于历史成功轨迹长度 | 非全局固定 max_step |
| High-Entropy Step Selection | 只对高熵 step 算 loss，跳过 trivial step | 节省计算 + 更有效学习 |
| Experience Pool | 困难任务当前 batch 全败时，补历史正样本 | 保证正负样本共存 |

---

## 6. Phase 4: Offline DPO on 关键步骤（第 10-14 周）

> EvoCUA: 关键步骤 DPO 比全轨迹 DPO 更 sample-efficient，+4 分（51 → 55）

### 6.1 偏好对构造

```
来源 1: 同一 query 的成功 vs 失败轨迹
  - 正例: 成功轨迹的关键步骤
  - 负例: 失败轨迹中第一个偏离正确路径的步骤

来源 2: 同一 query 的高效 vs 冗余轨迹
  - 正例: 步数少的成功轨迹
  - 负例: 步数多但最终成功的轨迹

来源 3: 关键步骤精确 vs 错误
  - 正例: grounding 准确的关键步骤
  - 负例: grounding 偏移但因后续纠正仍成功的步骤
```

### 6.2 DPO 训练

```
数据: 关键步骤级别偏好对（非全轨迹）
超参: LR 1e-6, β=0.1, Epochs 1-2
```

### 6.3 Model Merge（可选）

> EvoCUA 提到 model merge 有效

```
策略: 分别训练针对不同 OS / 应用类型的 vertical agents
融合: θ_merge = Σα_k · θ_k（参考 UI-TARS-2）

例如:
  θ_linux  = RL on Linux tasks
  θ_win    = RL on Windows tasks
  θ_merge  = 0.5 * θ_linux + 0.5 * θ_win
```

---

## 7. 完整迭代循环

```
                    ┌─────────────────────────────┐
                    │                             │
                    ▼                             │
              ┌──────────┐                        │
              │  Rollout  │  2000-4000 并发        │
              │  (vLLM)   │                        │
              └────┬─────┘                        │
                   │                              │
              ┌────▼─────┐                        │
              │ Verifier  │  Rule / Parse / LLM    │
              └────┬─────┘                        │
                   │                              │
          ┌────────┼────────┐                     │
          ▼        ▼        ▼                     │
      成功轨迹  失败轨迹  部分成功                  │
          │        │        │                     │
          ▼        ▼        ▼                     │
      [RFT SFT]  [DPO负例]  [LLM修正→SFT]         │
          │        │                              │
          ▼        ▼                              │
      ┌──────────────┐                            │
      │   Train       │  GRPO / RFT / DPO         │
      │   (verl)      │                            │
      └──────┬───────┘                            │
             │                                    │
             ▼                                    │
       ┌──────────┐    不够好                      │
       │  评测     │ ──────────────────────────────┘
       │ OSWorld   │
       └──────┬───┘
              │ 达标
              ▼
          发布模型
```

---

## 8. 评测节奏

| 时机 | 评测内容 | 耗时 |
|------|----------|------|
| 每轮 RFT 后 | OSWorld 50-task subset + 自建 smoke test 100 tasks | ~4h |
| 每 2-3 轮 RFT | OSWorld 全量 369 tasks | ~12h |
| Phase 切换时 | OSWorld + ScreenSpot-Pro + WAA + AssistGUI | ~24h |

**目标里程碑**：

| 阶段 | 预期 OSWorld SR |
|------|-----------------|
| Baseline (当前 SFT 模型) | ? |
| Cold-start SFT 后 | baseline + 3-5 |
| RFT Round 3 后 | 25-35 |
| RFT Round 5+ 后 | 40-50 |
| DPO 后 | 45-55 |

---

## 9. 团队分工与 Timeline

### 角色

| 角色 | 职责 | 人数 |
|------|------|------|
| **Infra** | 沙盒环境、K8s 编排、分布式管理器、截图服务 | 2-3 |
| **Env** | Query 设计、Verifier 编写、任务初始状态配置 | 2-3 |
| **Train** | 模型训练、RFT 循环、DPO、评测 | 2 |
| **Research** | 数据分析、错误归因、策略调优 | 1 |

### Timeline

```
Week 1-3    Phase 0: 沙盒基建 + baseline + 分布式架构
            ├── [Infra] Docker 镜像 + K8s + 环境管理器
            ├── [Train] 跑 baseline, 分析失败 case
            └── [Env]   开始 Query 设计

Week 2-5    Phase 1: Query 池 + Verifier（与 Phase 0 并行）
            ├── [Env]   3000-5000 query + verifier
            ├── [Env]   任务初始状态脚本
            └── [Infra] 扩容到 100+ 并发，联调 rollout pipeline

Week 4-5    Phase 2: Cold-start SFT（如需要）
            ├── [Train] 强模型 teacher rollout → 收集 5K 轨迹
            └── [Train] Cold-start SFT 训练

Week 5-12   Phase 3: 多轮 RFT（核心）
            ├── [Infra] 扩容到 2000-4000 并发
            ├── [Train] RFT Round 1, 2, 3, ... N
            ├── [Env]   持续扩展 Query 池 + 新 Verifier
            ├── [Research] 每轮分析失败 case, 调整策略
            └── [Train] 如遇 entropy collapse → Entropulse

Week 10-14  Phase 4: DPO + Merge
            ├── [Train] 关键步骤 DPO
            ├── [Train] Model merge 实验
            └── [全员]  最终评测 + 发布

里程碑:
  Week 3:  10 并发 mini RL loop 跑通
  Week 5:  100+ 并发 + 1000 query with verifier
  Week 8:  2000+ 并发 + 3000 query, RFT Round 3 完成, OSW >30
  Week 12: 多轮 RFT 收敛, OSW >45
  Week 14: DPO 完成, OSW >50
```

---

## 10. Week 1 立即开工清单

### Infra
- [ ] Ubuntu 24.04 Docker 镜像制作（预装 P0 应用 + 截图服务 + A11y 工具）
- [ ] 写 `reset_env.sh`（< 10s 重置到 clean state）
- [ ] 调研 K8s 方案（本地集群 or 云），出技术选型
- [ ] 部署 vLLM，能跑当前 SFT 模型推理

### Env
- [ ] 定义应用-功能矩阵终稿
- [ ] 写 `verifier_generator.py` — 输入 query 描述，LLM 输出 (query, verifier, init_state) 三元组
- [ ] 先手写 50 个 query + verifier（文件管理 + 终端），作为 LLM 生成的 few-shot 示例和质量标杆
- [ ] 开始批量生成，目标 Week 1 结束有 500+ query

### Train
- [ ] 跑 OSWorld 全量 baseline（369 tasks）
- [ ] 分析失败 case 分布（输出错误类型占比报告）
- [ ] 确定是否需要 cold-start SFT，制定 cold-start 数据方案

### Research
- [ ] 精读 EvoCUA、DART-GUI 论文细节，整理可复现的工程 checklist
- [ ] 设计 entropy 监控方案（什么指标、什么阈值触发 Entropulse）
- [ ] 设计关键步骤识别算法

---

## 11. 关键风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 并发环境扩容慢 | RL scaling 受限 | 先用 Linux Docker（扩容快），Win/macOS 逐步加 |
| Verifier 质量不够（假阳/假阴） | RL 信号有噪声，模型学歪 | P0 应用人工抽检 20%；LLM-as-Judge 做 double-check |
| Entropy collapse | RL 过拟合，停止提升 | 监控 entropy，及时 Entropulse |
| Query 池多样性不足 | 模型过拟合到特定任务模式 | 持续扩展 query 池 + 指令复杂化 |
| 当前模型 grounding 不够 | RL 探索困难 | 如果 baseline 显示 grounding 弱，先补一轮 grounding SFT |
| macOS/Windows 环境成本 | 跨平台覆盖不足 | 先 all-in Linux，后续逐步加平台 |
