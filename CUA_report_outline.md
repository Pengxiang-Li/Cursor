# CUA 汇报流程与逐页 PPT 脚本（面向资深研究员）

## 0. 汇报目标（开场 30 秒）

本次汇报不是做“资料罗列”，而是回答三个问题：
1. 现有 CUA 工作到底分别解决了什么问题、如何解决；
2. 哪些结论具有可迁移的方法论价值；
3. 如果我们要做下一代跨平台 CUA 基座，最小可行路径是什么。

---

## 1) 讲解流程（Part-by-Part）

## Part I - 问题定义与分析框架（约 5 分钟）

**讲什么**
- 定义 CUA 研究对象：跨 OS（Win/macOS/Linux）桌面任务完成，不只是 grounding。
- 统一分析坐标：`数据闭环 / 感知与 grounding / 动作空间 / RL+Verifier / 基础设施` 五个轴。
- 给出评估目标：不仅看 benchmark 分数，也看可扩展性与工程可复现性。

**怎么讲**
- 先给“全景图”，明确你不会按论文逐篇讲，而是按问题分解。
- 用 1 页“分析框架图”做后续所有对比的索引页，听众更容易建立共同上下文。

**这一部分的产出**
- 听众接受你后面所有比较的口径和评价标准。

---

## Part II - 现有工作拆解（约 15 分钟）

**讲什么**
- 用五个轴对比 Mobile-Agent-v3.5、Mano、EvoCUA、UI-TARS-2、AgentCPM、Computer-RL、DART-GUI。
- 强调“共识”和“分歧”：
  - 共识：SFT 后必须 RL；数据飞轮是核心；grounding 是瓶颈；
  - 分歧：是否依赖 A11y、动作表示（JSON vs Code）、RL 算法与 reward 设计。
- 数据侧补充：开源数据版图（trajectory vs grounding vs QA）与缺口（macOS/Linux 轨迹、A11y、代码级动作）。

**怎么讲**
- 每个轴只回答 3 个问题：`SOTA 在做什么？证据是什么？迁移时注意什么？`
- 不复述论文细节，专注“可执行经验”和“失败模式”。
- 举 2-3 个“跨论文一致证据”作为锚点（如 Entropulse、关键步骤 DPO、Action Desp）。

**这一部分的产出**
- 把“工作堆叠”提炼为“能力构建规律”。

---

## Part III - 方法论抽象（约 15 分钟）

**讲什么**
- 提出统一方法论：`L0.5 感知/grounding -> L1 轨迹与规划 -> Online RL -> Entropy 恢复 -> 关键步骤 DPO`。
- 统一动作空间建议：`API-GUI Paradigm`（GUI primitive + 应用 API + 代码输出）。
- Verifier 分层：Rule-based -> Screenshot diff -> LLM Judge -> Generative ORM。
- 数据飞轮路由：成功/失败/部分成功轨迹如何分流回 SFT/CT/RL。

**怎么讲**
- 以“流水线图 + 关键决策点”来讲，不以模型名为主语。
- 每个决策点给一句“为什么”：例如 code action 是为了统一工具调用与 GUI 操作。
- 对可能争议点提前给边界条件（如纯视觉是否可行、A11y 的 token 成本）。

**这一部分的产出**
- 一套可复用的 CUA 研发范式，而不是单模型 recipe。

---

## Part IV - 落地路线图与讨论（约 8 分钟）

**讲什么**
- 0-2 月基建、2-4 月 grounding、3-5 月 SFT、4-7 月 RL、6-10 月扩展融合。
- 风险-对策：macOS 成本、Verifier 构建难、跨平台梯度冲突、OpenCUA pattern 对齐。
- 里程碑指标：ScreenSpot-Pro、OSWorld、WAA、AssistGUI 的阶段目标。

**怎么讲**
- 把路线图转成“可决策清单”：本季度必须做/可延后/暂不做。
- 结尾抛 2-3 个开放问题，邀请资深听众进入技术讨论。

**这一部分的产出**
- 汇报从“分析”转向“决策”，形成行动项。

---

## 2) 逐页 PPT 内容（20 页）

> 建议总时长 40-45 分钟；每页 1.5-2 分钟，保留 8-10 分钟讨论。

### Slide 1 - 标题页
**标题**：CUA 现有工作的系统拆解与方法论抽象  
**副标题**：面向跨平台 Desktop Agent 基座（Win/macOS/Linux）  
**怎么讲**：一句话定义目标：“我们要抽象可复用的方法，不是追单点 SOTA。”

### Slide 2 - 汇报目标与结论预告
**要点**
- 目标 1：统一分析口径，比较现有工作
- 目标 2：提炼可迁移方法论
- 目标 3：给出可执行训练路线
- 预告结论：数据飞轮与 Verifier 决定上限；动作空间统一是关键突破口  
**怎么讲**：先给“答案大纲”，降低听众认知负担。

### Slide 3 - 问题定义：我们在优化什么？
**要点**
- 任务：复杂、长序列、跨应用、跨 OS 的真实计算机使用
- 能力链：感知 -> grounding -> 规划 -> 执行 -> 纠错
- 评估：成功率 + 效率 + 稳定性 + 可扩展性  
**怎么讲**：强调“benchmark 分高不等于可扩展”。

### Slide 4 - 分析框架（五轴）
**要点**
- Axis A：Data Flywheel（采集/过滤/回流）
- Axis B：Grounding（难例、负样本、A11y 融合）
- Axis C：Action Space（JSON / 坐标 / Code / API）
- Axis D：RL & Verifier（reward 可编程性）
- Axis E：Infra（并发环境、重置速度、成本）  
**怎么讲**：后面所有对比都映射到这五轴。

### Slide 5 - 工作全景与定位
**要点**
- 代表工作：Mobile-Agent-v3.5 / Mano / EvoCUA / UI-TARS-2 / AgentCPM / Computer-RL / DART-GUI
- 共性：SFT 后 RL、强调数据闭环
- 差异：动作表示、reward 设计、环境依赖  
**怎么讲**：从“共同范式”切入，再看差异来源。

### Slide 6 - 轴 A：数据闭环对比
**要点**
- UI-TARS-2：Data flywheel + in-policy 标注 + CT/SFT 路由
- Mano：自动探索 + 人工兜底 + 成功轨迹回流
- Computer-RL：Model Pool 分层采样 + verifier 过滤
- EvoCUA：小规模高质量冷启动 + 多轮 RFT  
**怎么讲**：强调“迭代效率 > 单次数据量”。

### Slide 7 - 轴 B：Grounding 是底座瓶颈
**要点**
- 证据：ScreenSpot-Pro 仍低天花板，专业软件/小目标最难
- 手段：Hard synthesis、infeasible 负样本、A11y 自动标注
- 规模经验：10M+ 才能稳定跨域  
**怎么讲**：指出“grounding 不稳，后续 RL 只会放大错误”。

### Slide 8 - 轴 C：动作空间统一（关键分歧）
**要点**
- 现状：mobile/web/desktop action space 割裂
- Computer-RL 路径：代码动作统一 GUI primitive + app API
- 优势：可组合、可调用工具、复用 LLM code prior  
**怎么讲**：把“代码动作”定义为工程可扩展方案，而非风格选择。

### Slide 9 - 轴 D：RL 与 Verifier 体系
**要点**
- GRPO/PPO/DPO 的角色分工
- Verifier 分层：Rule-based > Diff > LLM Judge > ORM
- 核心约束：桌面任务 verifier 构建是 RL 扩展瓶颈  
**怎么讲**：先讲 reward 信号来源，再讲算法选择。

### Slide 10 - 轴 E：基础设施与并发规模
**要点**
- 经验区间：online RL 需要 2000-4000 并发环境
- 三层环境：采集层 / RL 沙盒层 / 虚拟渲染层
- 关键指标：重置速度、稳定性、可监控性  
**怎么讲**：强调“算力不是唯一瓶颈，环境工程才是”。

### Slide 11 - 数据版图：我们能直接用什么？
**要点**
- Grounding：OS-ATLAS / GroundCUA / Jedi
- Trajectory：OpenCUA/AgentNet / GUI-360 / ScaleCUA
- Eval：OSWorld / WAA / ScreenSpot-Pro / UI-Vision  
**怎么讲**：把“可用资产”与“缺口”拆开讲。

### Slide 12 - 数据缺口与风险
**要点**
- 缺口：macOS/Linux 轨迹、代码级动作、A11y 全量标注、失败纠错轨迹
- 风险：平台偏置、格式不一致、模式不兼容（如 OpenCUA vs Qwen pattern）
- 对策：统一 schema + 去重 + 对齐策略（RoPE/混合比例）  
**怎么讲**：风险要落在“可操作对策”，避免空泛。

### Slide 13 - 方法论总图（建议核心页）
**要点**
- L0.5 感知与 grounding
- L1 任务分解与重组（DAG + 指令复杂化）
- L2 Online RL（GRPO/PPO）
- L2.5 Entropy 恢复（Entropulse）
- L3 关键步骤 DPO 与持续飞轮  
**怎么讲**：这是你整场汇报的“主结论页”。

### Slide 14 - 方法细节 A：数据飞轮路由
**要点**
- 成功轨迹 -> SFT
- 失败轨迹 -> CT / 反例池
- 部分成功轨迹 -> LLM 修正 -> SFT
- 高熵探索轨迹 -> Entropulse 数据池  
**怎么讲**：突出“不是只收集成功样本”。

### Slide 15 - 方法细节 B：训练配方建议
**要点**
- Phase 1：Grounding 15-20M
- Phase 2：SFT 500K 轨迹 / 5M steps
- Phase 3：Online RL（10K+ tasks, 2k-4k env）
- Phase 4：关键步骤 DPO + 参数融合  
**怎么讲**：给出数量级，体现可执行性。

### Slide 16 - 方法细节 C：关键步骤学习
**要点**
- 关键步骤定义：不可逆、分支点、末步提交
- 标注方式：Verifier 回溯 + 状态变化 + DAG 结构
- 收益：比全轨迹偏好学习更高效  
**怎么讲**：可引用 EvoCUA 的实证趋势。

### Slide 17 - 方法细节 D：跨平台冲突与融合
**要点**
- 冲突来源：动作分布和 UI 结构差异
- 方案 A：交替平台优化（MRPO）
- 方案 B：vertical agent + 参数插值（UI-TARS-2）  
**怎么讲**：给建议优先级：先 B 后 A。

### Slide 18 - 评测设计：不仅看 Task SR
**要点**
- Grounding：text/icon/widget 分项准确率
- Execution：Task SR + Step Efficiency + 平均步数
- Robustness：异常 UI、弹窗、延迟、分辨率变化  
**怎么讲**：强调“可解释指标”服务模型迭代。

### Slide 19 - 6-10 个月执行路线图
**要点**
- M1-2：环境与数据基建
- M2-4：grounding 预训练
- M3-5：SFT 冷启动与飞轮
- M4-7：RL 与 verifier 扩展
- M6-10：多模型融合与规模化  
**怎么讲**：按“里程碑 + 验收指标”讲。

### Slide 20 - 结论与讨论问题
**要点**
- 结论 1：CUA 上限由“数据闭环 × verifier”共同决定
- 结论 2：动作空间统一是跨平台扩展核心
- 结论 3：grounding 质量决定 RL 有效性
- 讨论：A11y 与纯视觉最佳混合比？何时切换到 code-first agent？  
**怎么讲**：用问题收尾，引导资深听众给反馈。

---

## 3) PPT 设计建议（专家汇报风格）

- 配色：深色标题 + 高对比正文，避免花哨动画。
- 每页不超过 4 个主 bullet；复杂表格用“结论先行 + 附录备份”。
- 多用“方法图/流程图/对比矩阵”，少贴长段文字。
- 给每页准备一句“主张句”（takeaway），确保听众可复述。
- 在附录准备：
  - 数据集速览表（含规模口径差异说明）
  - 各工作 RL 配置细节
  - Verifier 示例模板（rule/script/judge）。
