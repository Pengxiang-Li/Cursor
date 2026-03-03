# CUA 基座模型训练 — 落地执行计划

> **目标**：全平台 (Win/macOS/Linux) Desktop GUI 基座模型，基于 Qwen2.5-VL  
> **核心原则**：数据闭环 > 模型架构；冷启动质量 > 数量；RL 瓶颈在环境和 Verifier  
> **本文档定位**：可直接分配到人的执行清单，每个 Task 标注负责角色、交付物、依赖关系

---

## 0. 角色定义

| 角色 | 职责 |
|------|------|
| **Infra** | VM 集群、Docker 编排、A11y 工具链、截图/录制管线 |
| **Data** | 开源数据清洗、自建数据管线、格式统一、质量控制 |
| **Train** | 模型训练、超参调优、评测跑分 |
| **Env** | Verifier 编写、RL 沙盒环境、任务池管理 |
| **Research** | 动作空间设计、CoT 格式、训练策略实验 |

---

## 1. Sprint 0: 基建 + Baseline（第 1-3 周）

> 目标：跑通全链路最小闭环，拿到 zero-shot baseline 数据

### 1.1 VM 环境搭建 [Infra]

| Task | 交付物 | 预计工时 |
|------|--------|----------|
| 部署 Ubuntu 24.04 GNOME VM × 10 | 可 SSH + VNC 的 VM 模板镜像 | 2d |
| 部署 Windows 11 VM × 10 | 同上，预装 Office/VS Code/Chrome | 3d |
| macOS VM × 5（AWS Mac Dedicated Host 或 Tart/Anka） | 同上，预装 Safari/Pages/Terminal | 3d |
| VM 快照/恢复脚本（<10s 重置） | `reset_vm.sh` | 2d |
| 截图服务（1080p PNG） | `screenshot_service.py`，REST API | 1d |

### 1.2 A11y 工具链 [Infra]

| 平台 | 工具 | Task | 交付物 |
|------|------|------|--------|
| Linux | `pyatspi2` + AT-SPI | 安装配置 + 写提取脚本 | `linux_a11y_extractor.py` |
| Windows | `pywinauto` + UIA | 安装配置 + 写提取脚本 | `win_a11y_extractor.py` |
| macOS | `macapptree` + AX API | 安装配置 + 写提取脚本 | `mac_a11y_extractor.py` |
| 跨平台 | 统一输出格式 | 三平台 A11y → 统一 JSON schema | `a11y_schema.json` |

**验收标准**：在三个 OS 上分别打开 Firefox/Chrome、文件管理器、文本编辑器，能提取完整 A11y Tree 并输出统一 JSON。

### 1.3 动作录制/回放引擎 [Infra]

| Task | 交付物 |
|------|--------|
| 键鼠事件录制（Linux: xdotool/ydotool, Win: pywinauto, macOS: cliclick） | `action_recorder.py` |
| 事件回放 + 截图同步 | `action_replayer.py` |
| 录制格式定义 | `action_schema.json` |

### 1.4 统一动作空间设计 [Research]

> 参考 Computer-RL 的 API-GUI Paradigm，这是当前最优方案

```
GUI Primitives（跨平台统一）:
  click(x, y)
  double_click(x, y)
  right_click(x, y)
  type_text(text)
  hotkey(key1, key2, ...)
  scroll(direction, amount)
  drag(start_x, start_y, end_x, end_y)
  wait(seconds)
  done()

Application-Specific API（按活跃窗口动态加载）:
  spreadsheet.set_cell(cell, value)
  terminal.run_command(cmd)
  browser.navigate(url)
  ...
```

**交付物**：
- `action_space.py` — 所有 action 的 Python 定义 + 解析器 + 执行器
- `api_registry.json` — 各应用 API 定义，推理时按活跃窗口注入 System Prompt
- 设计文档：坐标归一化方案（推荐 [0, 1000]）、code action vs JSON action 对比实验设计

### 1.5 Zero-shot Baseline [Train]

| Task | 交付物 |
|------|--------|
| Qwen2.5-VL 7B / 72B 在 ScreenSpot-Pro 上跑分 | baseline 数据 |
| Qwen2.5-VL 7B / 72B 在 OSWorld 50-task subset 上跑分 | baseline 数据 |
| 整理 prompt template（参考 UI-TARS-1.5 / DART-GUI 格式） | `system_prompt.txt` |

### 1.6 统一数据格式定义 [Data]

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
      "action_description": "...",
      "screenshot_before": "path/to/001.png",
      "screenshot_after": "path/to/002.png",
      "a11y_tree_before": {},
      "a11y_tree_after": {},
      "action": {
        "action_type": "click",
        "coordinate": [320, 28],
        "code": "click(320, 28)",
        "element_id": "menu_table",
        "element_role": "MenuItem",
        "element_name": "Table"
      }
    }
  ],
  "metadata": {
    "resolution": "1920x1080",
    "os_version": "Ubuntu 24.04",
    "language": "en",
    "total_steps": 8,
    "success": true,
    "quality_score": 4.2
  }
}
```

**交付物**：`data_schema.json` + 格式转换脚本 `convert_{dataset_name}.py`

---

## 2. Sprint 1: 开源数据清洗 + Grounding 训练（第 3-8 周）

### 2.1 开源数据下载与清洗 [Data]

**P0 — 立即下载**：

| 数据集 | 用途 | 量级 | 处理要点 |
|--------|------|------|----------|
| OS-ATLAS | Grounding 核心 | 13M+ 元素 | 提取桌面部分（Win/Linux/macOS），按 OS 均衡采样 |
| GroundCUA | Grounding | 3.56M 标注 / 56K 截图 | 直接可用，格式转换 |
| Jedi | Grounding 增强 | 4M 合成 | 与真实数据混合使用 |
| OpenCUA/AgentNet | SFT 轨迹核心 | 22,625 轨迹 / 3 OS | **已知问题**：与 Qwen pattern 不兼容，需 RoPE 对齐 + 格式转换 |
| GUI-360° | SFT 轨迹 | 1.2M 步 | 仅 Windows，含 reasoning trace |
| ScaleCUA | SFT 轨迹 | 大规模 / 6 OS | 提取桌面部分 |

**P1 — 第二批**：

| 数据集 | 用途 | 处理要点 |
|--------|------|----------|
| GUICourse | OCR + 基础 grounding | curriculum learning 早期使用 |
| Mind2Web / Multimodal-Mind2Web | 浏览器操作 | 格式转换 |
| GUIAct | GUI 交互动作 | 格式转换 |
| AITW | 交互模式迁移 | ResNet-50 特征去重，保留约 40%（参考 AgentCPM） |
| Rico | Mobile grounding 迁移 | resize 到 1080p |
| OmniACT | 代码级动作 | PyAutoGUI 格式，适配动作空间 |

**清洗 pipeline**：
1. 格式统一 → 自定义 schema
2. ResNet-50 特征 + 余弦相似度去重（AITW 等冗余数据集）
3. 规则过滤：截图模糊/黑屏/重复、坐标越界、轨迹连续性检查
4. LLM API 对轨迹打分（完成度/效率/推理质量，0-5 分），保留 ≥ 3.5
5. OpenCUA 特殊处理：RoPE 对齐 + 混合比例调优（参考 EvoCUA 经验）

**交付物**：各数据集的 `convert_xxx.py`、清洗后数据统计报告、HuggingFace datasets 格式存储

### 2.2 自建 A11y Grounding 数据 [Data + Infra]

> 利用已搭好的 VM + A11y 工具链，零标注成本批量生产

| Step | 操作 |
|------|------|
| 1 | 在 VM 上自动遍历目标应用（P0 应用列表见下） |
| 2 | 每个界面提取截图 + A11y Tree |
| 3 | 从 A11y Tree 中提取 (element_name, element_role, bounding_box) |
| 4 | LLM API 生成 grounding 指令（"点击保存按钮" → 坐标） |
| 5 | 质量过滤 |

**P0 应用列表**（跨平台优先）：
- 文件管理器（Files/Explorer/Finder）
- 浏览器（Firefox/Chrome/Safari）
- Office（LibreOffice Writer/Calc, MS Word/Excel, Pages/Numbers）
- 终端（GNOME Terminal / Windows Terminal / Terminal.app）
- VS Code
- 系统设置
- 文本编辑器

**目标产出**：2-3M grounding pairs

### 2.3 Hard Grounding Synthesis [Data]

> 参考 Mobile-Agent-v3.5

| 策略 | 方法 | 目标量 |
|------|------|--------|
| 多窗口场景合成 | 单窗口截图重组为多窗口高分辨率场景 | 200K |
| 专业软件截图 | MLLM 渲染高难度 UI（密集元素、小按钮） | 100K |
| Infeasible 负样本 | (截图, Query) 随机组合 + 多模型共识过滤 | 正负比 ~1:10 |

### 2.4 Phase 1 训练：UI 感知预训练 [Train]

```
数据规模: ~15-20M 样本
数据配比:
  OS-ATLAS (桌面)      40%    ~8M
  GroundCUA            15%    ~3M
  Jedi (合成)          15%    ~3M
  自建 A11y 标注       15%    ~3M
  Rico (mobile迁移)    10%    ~2M
  GUICourse (OCR)       5%    ~1M

训练任务:
  UI Element Detection  30%
  OCR                   20%
  Layout Description    15%
  Screen Summary        15%
  Element Counting      10%
  A11y Tree Prediction  10%

混入通用 VLM 数据 ~30%（防止视觉模块退化，参考 AgentCPM 经验，Qwen 基座强可降到 25-30%）

超参 (7B): LR 2e-5 cosine, BS 256, Epochs 2-3, 动态分辨率, Warmup 5%
先训 7B 验证全流程，再扩展到其他尺寸
```

### 2.5 Phase 2 训练：GUI Grounding [Train]

```
数据规模: ~10M 样本
数据配比:
  OS-ATLAS 桌面         35%    ~3.5M
  GroundCUA             25%    ~2.5M
  Jedi (合成)           20%    ~2M
  自建 grounding        20%    ~2M

训练任务:
  Point Grounding       40%    指令 → 坐标
  Box Grounding         30%    指令 → bbox
  Referring Expression  20%    指令 → 描述 + 坐标
  Multi-modal Grounding 10%    截图 + A11y → 坐标

坐标归一化: [0, 1000]
混入 ~10% 负样本（无匹配元素 → 拒答）
Loss: L1 on coordinates + CE on text

超参 (7B): LR 1e-5 cosine, BS 256, Epochs 2-3
```

**评测门槛**：ScreenSpot-Pro 进入 top-3 水平

---

## 3. Sprint 2: SFT 轨迹数据 + 训练（第 6-12 周）

> 与 Sprint 1 后半段并行启动

### 3.1 自建轨迹数据 — 四条并行管线 [Data + Infra]

**管线 A: 逆向任务合成（OS-Genesis 风格）**

| Step | 操作 |
|------|------|
| 1 | Agent 在 VM 中自由探索 GUI（随机/启发式点击） |
| 2 | 每步记录 (screenshot_before, a11y_before, action, screenshot_after, a11y_after) |
| 3 | 将 (state_before, action, state_after) 送 LLM API 反向生成任务指令 |
| 4 | 连续单步拼接为多步轨迹 |
| 5 | LLM API 评分 (0-5)，过滤低分 |

产出：每 VM 每天 ~1000-5000 步。10 台 VM × 30 天 → ~300K-1.5M 步

**管线 B: 教程驱动合成（AgentTrek 风格）**

| Step | 操作 |
|------|------|
| 1 | 爬取桌面教程（Microsoft Learn, Apple Support, ArchWiki, wikiHow, YouTube 字幕） |
| 2 | LLM API 转为结构化步骤 |
| 3 | VLM Agent 在 VM 中按教程执行，录制轨迹 |
| 4 | VLM 评估结果与教程预期一致性 |

产出：取决于教程数量，目标爬取数万篇教程 → 数十万步

**管线 C: 任务模板批量生成**

| Step | 操作 |
|------|------|
| 1 | 定义应用-功能矩阵（~50 应用 × ~10 功能） |
| 2 | LLM API 按 (应用, 功能) 对生成 N 个变体任务 |
| 3 | Agent 在 VM 中执行，录制轨迹 |
| 4 | 自动验证任务完成 |

产出：~50 × 10 × 20 = 10,000 基础任务 → ~100K 步

**管线 D: 人机协作标注**

| Step | 操作 |
|------|------|
| 1 | 人工执行复杂多步任务（跨应用工作流等长尾任务） |
| 2 | 录屏 + 动作记录工具自动捕获 |
| 3 | LLM API 生成 thought/reasoning 标注 |
| 4 | 人工审核关键节点 |

产出：~10K 高质量完整轨迹（每条 10-30 步）→ ~100K-300K 步

### 3.2 CoT 格式标注 [Data]

> 所有轨迹数据统一标注为三段式 CoT（参考 Mano，+2.8 提升）

```
<think>
[Observation] 当前界面：LibreOffice Writer，空白文档。
[Memory] 任务要求创建会议纪要模板。
[Progress] Step 1/6：输入标题。
[Thought] 先输入标题文字。
</think>
<summary>Type "会议纪要" at cursor position.</summary>
<action>type_text(text="会议纪要")</action>
```

**Mano 的关键发现**：在 Thought 和 Action 之间加一句 Action Description（summary），单项 +2.8 分。必须加。

**历史帧策略**（Mano 实验最优）：保留前 2 帧截图 + 全部历史文本摘要。

### 3.3 Phase 3 训练：动作预测 + 轨迹 SFT [Train]

```
数据规模: ~5M 步
数据配比:
  GUI-360° (Windows)     25%    ~1.25M steps
  自建轨迹               25%    ~1.25M steps
  ScaleCUA (跨平台)      20%    ~1M steps
  OpenCUA/AgentNet       15%    跨平台（已对齐格式）
  OmniACT (代码级)        5%    ~0.25M steps
  Mind2Web + GUIAct      10%    ~0.5M steps

训练任务:
  Next Action Prediction           40%
  Action + Thought Prediction      30%
  Multi-step Planning (3-5步)      20%
  Code Generation (统一动作空间)    10%

混入通用对话/VQA 数据 25%（防 mode collapse）
冷启动先用高质量子集 100K-200K 步（参考 Computer-RL 180K 步 cold-start）

超参 (7B): LR 1e-5 cosine, BS 256, Epochs 2-3
```

### 3.4 Phase 4 训练：Agent SFT [Train]

```
数据:
  自建高质量轨迹         50%    ~500K
  GUI-360° (reasoning)   15%    ~150K
  OpenCUA/AgentNet       10%    ~100K
  NatureGAIA (自纠正)     5%    ~50K
  通用对话/VQA           20%    ~200K

关键步骤 upsampling 到 15-20%（参考 EvoCUA 冷启动配比：50% 通用 + 35% 普通 + 15% 关键步骤）

关键步骤识别方法：
  - Verifier 回溯：失败轨迹中第一个偏离正确路径的步骤
  - 状态变化分析：前后截图差异大的步骤
  - 末步强制标记（save/submit/confirm）

超参 (7B): LR 5e-6 cosine, BS 128
```

**评测门槛**：OSWorld >15% SR

---

## 4. Sprint 3: RL（第 10-20 周）

> RL 是性能跃迁的关键，但瓶颈在环境和 Verifier

### 4.1 Verifier 体系构建 [Env]

**按应用构建优先级排序**（从易到难）：

| 优先级 | 应用 | Verifier 方式 | 目标数量 |
|--------|------|---------------|----------|
| P0 | 文件管理 | 检查文件系统状态 | 1000 |
| P0 | 文本编辑 | 读取文件内容比对 | 500 |
| P0 | 终端 | 检查命令输出/文件变化 | 500 |
| P1 | 浏览器 | URL + DOM 状态 (Playwright) | 1500 |
| P1 | Office (表格/文档/PPT) | 解析文档结构 (UNO/COM API) | 2000 |
| P1 | 系统设置 | 读取配置值 (gsettings/reg/defaults) | 500 |
| P2 | VS Code / IDE | Extension API 检查 | 1000 |
| P2 | 图像编辑 | 像素比对 | 500 |

**Verifier 分层体系**：

| Tier | 方式 | 精度 | 适用 |
|------|------|------|------|
| Tier 1: Rule-based | 文件系统/应用状态/文档结构/配置值 | 精确 | P0 应用 |
| Tier 2: Screenshot-diff | 前后截图关键区域比对 + OCR | 中等 | 视觉变化明显的任务 |
| Tier 3: LLM-as-Judge | 任务指令 + 初始/最终截图 + 操作历史 → 成功/失败 | 灵活 | 兜底 |
| Tier 4: Generative ORM | 自训练 Outcome Reward Model | 可学习 | 后期 RL 用 |

**目标**：5000-10000 个有 Verifier 的任务（参考 Computer-RL ~8000 个）

**EvoCUA 经验**：Verifier 可以全部由模型生成和修改，无需人工。但建议 P0 应用的 Verifier 做人工审核。

### 4.2 RL 沙盒扩容 [Infra]

| Task | 交付物 |
|------|--------|
| Docker/VM 快照池，预配置应用 + 任务初始状态 | 快照模板 × N |
| 快速重置 <10s | 重置脚本 |
| 分布式环境管理器 | 参考 Computer-RL / DART-GUI 架构 |
| 目标并发 2000-4000 | K8s 编排 |

**DART-GUI 架构参考**（四模块解耦异步）：
- **Env Cluster**：并行 Docker (K8s)
- **Rollout Service**：vLLM 多 worker 推理
- **Data Manager**：MySQL，管理轨迹/任务调度
- **Trainer**：FSDP (verl)，异步接收 filtered trajectories

### 4.3 RL 训练 [Train]

**Phase 1: Step-level GRPO**

```
算法: Step-level GRPO（无 Value Network，显存低）
Reward:
  R_task:       Rule-based Verifier 优先 → LLM-as-Judge 兜底
  R_format:     代码可解析 = 0 / 不可解析 = -1 / 坐标越界 = -0.5
  R_efficiency: -0.01 per step / -0.1 重复动作

Credit assignment: 成功轨迹上所有格式正确的 step 获得 r=1
KL: low_var_kl, β=0.0003

预期: ~100-200 training steps 后触顶（entropy collapse）
```

**Phase 2: Entropulse（Computer-RL 独创）**

```
收集 Phase 1 所有成功 rollout（~130K steps）
用这些数据做一轮 SFT → 恢复 entropy
LR: SFT 的 1/2（Computer-RL: 5e-6 vs 1e-5）
```

**Phase 3: 继续 GRPO / 尝试 PPO**

```
加载 Entropulse 权重，继续 GRPO
如切换 PPO:
  - 先冻结 policy 离线训练 value model（参考 UI-TARS-2 Value Pretraining）
  - Decoupled GAE 解耦长序列 advantage 计算
```

**Phase 4: Offline DPO on 关键步骤（EvoCUA 方案）**

```
偏好对来源:
  - 同一任务的成功 vs 失败轨迹
  - 高效 vs 冗余轨迹（步数少 vs 步数多）
  - 关键步骤级别的正确 vs 错误执行

关键步骤 DPO 比全轨迹 DPO 更 sample-efficient（EvoCUA: +4 分）
```

### 4.4 数据飞轮 [Data + Train]

```
RL Rollout → Verifier 验证 → 数据回收 → 质量过滤 → 路由
                                                    │
  高质量成功轨迹 ──────────▶ SFT 数据集              (UI-TARS-2)
  低质量/失败轨迹 ──────────▶ CT 数据集              (UI-TARS-2)
  成功但中间有错 ───────────▶ LLM 修正 → SFT         (Mano)
  成功 Rollout 集合 ────────▶ Entropulse SFT         (Computer-RL)
```

**评测门槛**：OSWorld >30% SR

---

## 5. Sprint 4: Scale + 融合（第 16-24 周）

### 5.1 多尺寸训练 [Train]

| 尺寸 | 策略 |
|------|------|
| 2B | 全参数训练 + 从 7B 蒸馏 |
| 7B | 完整四阶段（主力实验模型） |
| 72B | LoRA → 全参数 fine-tune |

### 5.2 跨平台融合 [Train + Research]

| 方案 | 方法 | 来源 | 建议 |
|------|------|------|------|
| A | 交替训练 Win→macOS→Linux 周期迭代 | MRPO (Mobile-Agent-v3.5) | 第二优先 |
| B | 分别训练 vertical agents → 参数插值 θ_merge = Σα_k·θ_k | UI-TARS-2 | **先做这个（最安全）** |
| C | 动态加权混合 batch 内混合 | Multi-task learning | 可选 |

### 5.3 持续飞轮

- RL 成功 → SFT 数据集
- 失败 → LLM 修正 → SFT
- 低质量 → CT 数据集
- 每个 query 多条轨迹 > 更多 query（EvoCUA 确认）

---

## 6. 评测体系

### 6.1 Benchmark

| 阶段 | Benchmark | 指标 | 频率 |
|------|-----------|------|------|
| Grounding | ScreenSpot, ScreenSpot-Pro | Grounding Acc | 每 checkpoint |
| 感知 | UI-Vision, 自建 UI 测试集 | Element F1, OCR Acc | 每 checkpoint |
| 端到端 | OSWorld (369 tasks, 跨 OS) | Task SR | 每阶段全量 |
| Windows | Windows Agent Arena (154+) | Task SR | 每阶段 |
| 专业软件 | AssistGUI (100 tasks) | Task SR | 每阶段 |
| 综合 | MMBench-GUI | 多层级 | 每阶段 |

### 6.2 持续评测节奏

- **每 checkpoint**：ScreenSpot-Pro (~1.5h) + OSWorld 50-task subset (~4h) + 自建 smoke test 100 tasks × 3 OS (~2h)
- **每阶段结束**：全量 OSWorld + WAA + AssistGUI + MMBench-GUI

---

## 7. 风险与对策

| 风险 | 对策 |
|------|------|
| macOS VM 成本高且许可复杂 | AWS Mac 预留实例 + Tart/Anka 虚拟化方案评估 |
| A11y 跨 OS 覆盖率不一致 | 混合有/无 A11y 训练数据，推理时按需降级到纯视觉 |
| 桌面 Verifier 构建困难 | P0 应用用 Rule-based，其余 LLM-as-Judge 兜底 |
| RL entropy collapse | Entropulse（Computer-RL 方案）+ entropy 监控 |
| OpenCUA 与 Qwen pattern 不兼容 | RoPE 对齐 + 混合比例调优（EvoCUA 经验） |
| 统一动作空间设计可能有坑 | Sprint 0 就做 Code Action 可行性验证实验 |
| 人力不足 | LLM 驱动为主，人工仅做 in-policy 标注 + 质检 |

---

## 8. 立即可执行的 Week 1 任务清单

> 以下是第一周每个角色应该立刻开始做的事情

### Infra（2-3 人）
- [ ] 采购/申请 VM 资源（Ubuntu × 10, Win × 10, macOS × 5）
- [ ] Ubuntu VM 模板镜像制作（预装 Firefox, LibreOffice, VS Code, GIMP, pyatspi2, xdotool）
- [ ] 写 `linux_a11y_extractor.py`，在 Ubuntu 上跑通 Files + Firefox + LibreOffice 的 A11y Tree 提取
- [ ] 截图服务 `screenshot_service.py` 基础版

### Data（2-3 人）
- [ ] 下载 OS-ATLAS, GroundCUA, Jedi 数据集
- [ ] 下载 OpenCUA/AgentNet, GUI-360°, ScaleCUA 数据集
- [ ] 开始写格式转换脚本 `convert_os_atlas.py`, `convert_groundcua.py`
- [ ] 定义 `data_schema.json` 终稿

### Train（1-2 人）
- [ ] 部署 Qwen2.5-VL-7B 推理环境
- [ ] 跑 ScreenSpot-Pro zero-shot baseline
- [ ] 跑 OSWorld 50-task subset zero-shot baseline
- [ ] 整理 System Prompt 模板

### Research（1 人）
- [ ] 完成统一动作空间设计文档（API-GUI Paradigm）
- [ ] 设计 CoT 三段式格式（Thought + Action Description + Action）
- [ ] 设计坐标归一化方案对比实验

---

## 9. 关键技术决策备忘

| 决策点 | 推荐方案 | 理由 |
|--------|----------|------|
| Action 输出格式 | Python Code（非 JSON） | 支持组合操作、条件判断；复用 LLM 代码能力（Computer-RL） |
| 坐标系 | 归一化 [0, 1000] | 跨分辨率泛化 |
| 输入分辨率 | 1920×1080 采集 → 1280×720 输入 | 平衡细节与效率（Computer-RL 方案） |
| A11y 使用策略 | 训练时混合有/无 A11y，推理时按需 | 增强鲁棒性（Computer-RL 纯视觉也可行） |
| CoT 格式 | Thought + Action Desp + Action 三段式 | Mano: 单项 +2.8 分 |
| 历史帧 | 前 2 帧截图 + 全部历史文本摘要 | Mano 实验最优 |
| RL 算法 | Step-level GRPO → Entropulse → GRPO → DPO | Computer-RL + EvoCUA 组合 |
| 跨平台融合 | 先 B（参数插值），再试 A（MRPO） | UI-TARS-2 最安全 |
| 基座模型 | Qwen2.5-VL-7B（主力实验），后扩展 | 社区生态好，视觉能力强 |
| 通用数据混合比例 | 25-30% | Qwen 基座强于 MiniCPM，可低于 AgentCPM 的 50% |

---

## 10. Timeline 总览

```
Week  1-3   Sprint 0: 基建 + Baseline
Week  3-8   Sprint 1: 开源数据清洗 + Grounding 训练 (Phase 1 & 2)
Week  6-12  Sprint 2: SFT 轨迹数据 + 训练 (Phase 3 & 4)
Week 10-20  Sprint 3: RL (Verifier + 沙盒 + GRPO + Entropulse + DPO)
Week 16-24  Sprint 4: Scale + 跨平台融合

里程碑:
  Week 3:  三平台 A11y 工具链跑通 + Zero-shot baseline
  Week 8:  ScreenSpot-Pro top-3 水平
  Week 12: OSWorld >15% SR (SFT)
  Week 20: OSWorld >30% SR (RL)
  Week 24: 多尺寸模型 + 跨平台融合完成
```
