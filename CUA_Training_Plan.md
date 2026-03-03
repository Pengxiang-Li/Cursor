# CUA RL 训练执行计划

> **前提**：已有不错的基础模型（SFT / Grounding 能力已具备），本计划聚焦 RL 阶段  
> **目标平台**：Linux (Ubuntu 24.04 GNOME)，应用范围对齐 OSWorld  
> **核心参考**：EvoCUA（5K 轨迹冷启动 → 多轮 RFT → OSW 51 → DPO → 55）  
> **关键约束**：标注团队有限，API quota 充足 → 最大化 LLM 驱动自动化  
> **核心公式**：RL 上限 = min(沙盒规模, Verifier 质量, 任务多样性)

---

## 0. 当前状态与目标

| 维度 | 现状 | 目标 |
|------|------|------|
| 基础模型 | SFT + Grounding 已完成 | — |
| 平台 | 尚未搭建环境 | Ubuntu 24.04, 对齐 OSWorld |
| Task 池 | 空 | 3000-5000 query + verifier |
| RL 环境 | 无 | 2000-4000 并发 |
| Verifier | 无 | 3000-5000 个，**LLM 自动生成为主** |
| OSWorld SR | ? (先测 baseline) | >50 |

---

## 1. 总体路线

```
已有 SFT 模型
     │
     ▼
[自动化 Task 生成] ← LLM 批量生成 query + verifier + init_state（已有工具链）
     │
     ▼
[Cold-start SFT] ← 少量高质量轨迹（~5K），对齐格式
     │
     ▼
[RFT Round 1..N] ← rollout → verify → 成功轨迹回收 → reject sampling SFT
     │               EvoCUA: 多轮 RFT → OSW 51
     ▼
[Offline DPO] ← 关键步骤级别偏好学习（EvoCUA: +4 分）
     │
     ▼
[Model Merge] ← 可选
```

---

## 2. Task 自动生成系统（已落地，见 `task_generator/`）

> 核心原则：人工定义 **模板和质量标杆**，LLM 批量生产，自动化验证

### 2.1 OSWorld 应用覆盖

我们的 task 池对齐 OSWorld 的 10 个 domain：

| Domain | OSWorld 任务数 | App | 主要 Verifier 模式 |
|--------|--------------|-----|-------------------|
| `os` | 24 | Files/Terminal/Settings | `vm_command_line` → `check_include_exclude` |
| `chrome` | 46 | Chrome | prefs / CDP → `exact_match` / `check_json` |
| `libreoffice_calc` | 47 | Calc | `vm_file` → `compare_table` |
| `libreoffice_impress` | 47 | Impress | `vm_file` → `compare_pptx_files` |
| `libreoffice_writer` | 23 | Writer | `vm_file` → `compare_docx_files` |
| `vs_code` | 23 | VS Code | `vm_command_line` → extension/settings check |
| `gimp` | 26 | GIMP | `vm_file` → `compare_images` |
| `thunderbird` | 15 | Thunderbird | `vm_file` → prefs check |
| `vlc` | 17 | VLC | config file check |
| `multi_apps` | 93 | 跨应用 | 组合验证 |

### 2.2 生成管线架构

```
Verifier Templates ──▶ generate_tasks.py ──▶ Raw Tasks (JSON)
(人工定义模式                 │(LLM API)
+ few-shot 示例)             │
                              ▼
                     validate_tasks.py ──▶ ✓ Valid / ✗ Rejected
                              │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
              augment_tasks.py (3种策略)
              ├─ parameter_variation (5x)
              ├─ difficulty_escalation
              └─ cross_app_composition
                    │
                    ▼
              Final Task Pool (3000-5000)
```

### 2.3 三阶段扩量

| 阶段 | 方法 | 输入 | 产出 |
|------|------|------|------|
| 1. Seed 生成 | `generate_tasks.py --domain all --num_tasks 50` | 模板 + LLM | ~500 seed tasks |
| 2. 验证 | `validate_tasks.py --mode sanity` | 500 seeds | ~400 validated |
| 3a. 参数变异 (5x) | `augment_tasks.py --strategy parameter_variation` | 400 seeds | ~2000 tasks |
| 3b. 难度升级 | `augment_tasks.py --strategy escalation` | 400 seeds | ~400 hard tasks |
| 3c. 跨应用组合 | `augment_tasks.py --strategy composition` | all seeds | ~200 multi-app |
| 4. 全量再验证 | `validate_tasks.py` | ~2600 | **~2400 final** |
| 5. 迭代扩展 | 扩展模板 + 重复 1-4 | 新类别 | **3000-5000** |

### 2.4 Verifier 可靠性保障

| 层 | 方法 | 目的 |
|----|------|------|
| 结构验证 | `validate_tasks.py --mode dry_run` | JSON 格式、字段完整性、func/type 合法性 |
| Sanity 验证 | `validate_tasks.py --mode sanity` | 在 clean env 上跑 verifier，必须 FAIL（否则是 false positive） |
| 人工抽检 | 按 domain 分层抽样 10-20% | 确认 verifier 逻辑正确 |
| RL 中反向验证 | 对比 agent 成功率和人工评估 | 发现 verifier 漏洞 |

### 2.5 重点：哪些 domain 优先生成

> 按 verifier 可靠性排序（越可靠 → 越应该多生成 → RL 信号越干净）

| 优先级 | Domain | 理由 | 目标数量 |
|--------|--------|------|----------|
| P0 | `os` | 文件系统检查最可靠，shell 命令即可验证 | 800 |
| P0 | `vs_code` | settings.json / extension list 可精确检查 | 400 |
| P0 | `chrome` | prefs / DOM 可程序化检查 | 500 |
| P1 | `libreoffice_calc` | UNO API 可解析表格，compare_table 已有 | 500 |
| P1 | `libreoffice_writer` | docx 结构可解析 | 300 |
| P1 | `libreoffice_impress` | pptx 结构可解析 | 300 |
| P2 | `gimp` | 图像比对精度有限 | 200 |
| P2 | `thunderbird` | prefs.js 可检查，但场景受限 | 100 |
| P2 | `vlc` | 场景较窄 | 100 |
| P1 | `multi_apps` | 由 composition 策略自动组合 | 300 |
| | **合计** | | **~3500** |

---

## 3. 沙盒环境（第 1-3 周）

### 3.1 Docker 镜像

目标：一个预装所有 OSWorld 应用的 Ubuntu 24.04 Docker 镜像

```
Ubuntu 24.04 GNOME Base
├── Firefox / Chrome
├── LibreOffice (Writer, Calc, Impress)
├── VS Code
├── GIMP
├── Thunderbird
├── VLC
├── GNOME Files (Nautilus)
├── GNOME Terminal
├── GNOME Settings
├── GNOME Text Editor
├── 截图服务 (1080p)
├── A11y 工具 (pyatspi2)
└── 环境 agent (接收命令, 执行动作, 返回截图)
```

### 3.2 关键要求

| 要求 | 规格 |
|------|------|
| 重置速度 | < 10s (Docker commit/restore) |
| 每个 task 有独立初始状态 | config 脚本自动设置 |
| 截图 | 1080p → 720p resize |
| 动作执行 | pyautogui / xdotool |
| Verifier 执行 | 在 VM 内 run command → return output |

### 3.3 分布式环境管理器（参考 DART-GUI）

```
Env Cluster (K8s) ◀──▶ Rollout Service (vLLM) ──▶ Data Manager (MySQL) ──▶ Trainer (verl)
```

**里程碑**：Week 3 末在 10 并发环境上跑通 mini RL loop。

---

## 4. Cold-start SFT（第 4-5 周，视 baseline 决定）

基于 baseline 结果决策：

| Baseline OSWorld SR | 决策 |
|---------------------|------|
| >15% 且格式正确率 >90% | 跳过 cold-start，直接 RL |
| 5-15% | 轻量 cold-start ~2K 轨迹，主要对齐格式 |
| <5% | 需要 cold-start ~5K 轨迹 |

Cold-start 数据来源：强模型 (GPT-4o / Claude) 作为 Teacher 在沙盒执行 → 仅保留 Verifier 通过的成功轨迹 → 每 query 4-5 条。

---

## 5. 多轮 RFT — 核心阶段（第 5-12 周）

### 5.1 每轮 RFT 循环

```
当前模型 rollout (2000-4000 并发)
    ↓
Verifier 验证每条轨迹
    ↓
成功轨迹 → Reject Sampling SFT (混入 30-50% 通用数据)
失败轨迹 → 存入负样本池 (后续 DPO)
    ↓
评测 → 更新 checkpoint
    ↓
扩展 query 池 / 提高难度 → 下一轮
```

### 5.2 EvoCUA 关键数字

- 5K 轨迹冷启动，每 query 4-5 条正确轨迹
- ~3000 query 实际使用
- 多轮 RFT → OSW 51；加 DPO → 55
- 一个 query 多条轨迹 > 更多 query
- 2000-4000 并发环境

### 5.3 DART-GUI 自适应策略（推荐采用）

| 策略 | 作用 |
|------|------|
| Dynamic Rollout Number | 成功率高的 query 减少采样，省算力给难 query |
| Dynamic Trajectory Length | 最大步数基于历史成功轨迹长度 |
| High-Entropy Step Selection | 只对高熵 step 算 loss |
| Experience Pool | 难 query 全败时补历史正样本 |

### 5.4 Entropy Collapse → Entropulse

```
触发: entropy 监控显示显著下降 + 性能不再提升
操作: 收集所有成功 rollout → SFT 一轮 (LR = 5e-6) → 恢复 entropy → 继续 RL
```

---

## 6. DPO on 关键步骤（第 10-14 周）

> EvoCUA: 关键步骤 DPO +4 分（51 → 55）

偏好对来源：
- 同 query 成功 vs 失败轨迹的关键步骤
- 高效 vs 冗余轨迹
- 关键步骤：不可逆操作 / 分支决策点 / 末步 save/submit

---

## 7. Timeline

```
Week 1-2    Task 自动生成 (seed → validate → augment)
            ├── [Data] generate 500 seeds → validate → augment to 2000+
            ├── [Data] 人工抽检 10-20%，修复模板
            └── [Data] 迭代到 3000+ tasks

Week 1-3    沙盒基建
            ├── [Infra] Docker 镜像制作 (OSWorld 应用全装)
            ├── [Infra] K8s 编排 + 环境管理器
            ├── [Infra] vLLM 部署
            └── [Train] 跑 OSWorld baseline

Week 4-5    Cold-start (如需要)
            ├── [Train] 强模型 teacher rollout
            └── [Train] Cold-start SFT

Week 5-12   多轮 RFT (核心)
            ├── [Infra] 扩容到 2000-4000 并发
            ├── [Train] RFT Round 1, 2, ..., N
            ├── [Data]  持续扩展 query 池
            └── [Train] 如遇 entropy collapse → Entropulse

Week 10-14  DPO + Merge
            ├── [Train] 关键步骤 DPO
            └── [Train] 最终评测

里程碑:
  Week 2:  3000+ tasks with verifiers 就绪
  Week 3:  10 并发 mini RL loop 跑通
  Week 5:  100+ 并发, RFT Round 1 完成
  Week 8:  2000+ 并发, OSW >30
  Week 12: 多轮 RFT 收敛, OSW >45
  Week 14: DPO 完成, OSW >50
```

---

## 8. Week 1 立即开工清单

### Data（利用 API quota）
- [ ] 跑 `generate_tasks.py --domain os --num_tasks 100` 生成第一批 seed
- [ ] 跑 `validate_tasks.py --mode dry_run` 检查格式
- [ ] 人工审阅 20 个生成结果，修正模板中的 few-shot 示例
- [ ] 迭代模板后，跑 `generate_tasks.py --domain all --num_tasks 50`
- [ ] 跑 `augment_tasks.py --strategy parameter_variation --multiplier 5`
- [ ] 目标：Week 1 末有 1000+ validated tasks

### Infra
- [ ] Ubuntu 24.04 Docker 镜像制作（预装 OSWorld 全部应用）
- [ ] 写 `reset_env.sh`（< 10s 重置到 clean state）
- [ ] 部署 vLLM，能跑当前 SFT 模型推理

### Train
- [ ] 跑 OSWorld 全量 baseline（369 tasks）
- [ ] 分析失败 case 分布
- [ ] 确定是否需要 cold-start SFT

---

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| LLM 生成的 verifier 质量不够 | 结构验证 + sanity 验证 + 人工抽检三层过滤 |
| False positive verifier（总是 pass）| sanity check 在 clean env 必须 fail |
| compare_table 等复杂 verifier 难以自动生成 | 这些 domain 先少量人工写 gold answer 文件，LLM 负责生成 instruction + init |
| 并发环境扩容慢 | 先用 Docker（扩容快），优先 os/vscode/chrome 等轻量应用 |
| Entropy collapse | 监控 entropy，Entropulse 应对 |
| Query 池多样性不足 | augment_tasks 的三种策略 + 持续扩展模板 |
