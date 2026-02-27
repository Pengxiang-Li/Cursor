# CUA 调研汇报（逐页文案草案）

> 定位：面向资深 CUA 研究员，目标是从多篇工作中抽象出“如何做”的方法论（recipe），而非复述论文。

---

## 1. 封面

**标题**：CUA 调研汇报：从现有工作抽象出方法论  
**副标题**：数据飞轮 / Grounding / 轨迹生产 / RL+Verifier / 动作空间统一（自动生成日期）  
**讲法**：30 秒声明本报告只讲跨工作共性与可执行清单。

## 2. 目标与输出

- 目标：分析现有 SOTA 工作，抽象可执行方法论  
- 输出：训练路线图、关键 trade-off、工程/数据管线拆解

## 3. 问题定义：CUA 系统栈

- 输入：截图 +（可选）A11y/DOM + 历史摘要/记忆 + 指令  
- 输出：坐标 primitives / 代码（API-GUI）/ 工具调用（MCP）  
- 闭环：执行→观测→规划/反思→再执行；Verifier 提供成败信号

## 4. 共识 1：数据闭环 > 模型架构

- UI-TARS-2：Data Flywheel + 路由（高质→SFT，低质→CT）  
- Computer-RL：Entropulse（成功 rollout 回收→SFT 恢复熵）  
- Mano：成功回流 SFT；成功但有错→LLM 草稿→人修→注入  
- EvoCUA：小数据多轮 RFT + DPO 也能上分，强调迭代与 scaling

## 5. 共识 2：三大瓶颈

- Grounding  
- RL scaling（环境并发+Verifier）  
- 动作空间割裂（跨平台迁移与梯度冲突）

## 6. 动作空间：API-GUI Paradigm 与摘要化输出

- Computer-RL：Python 代码统一 primitives + app API  
- Mano：Action Desp 摘要  
- Mobile-Agent：Token-ID transport 对齐 logprob

## 7. 数据版图：Grounding / Trajectory / Cognition / World Model

- 数据按训练目标分桶，便于配比与路由

## 8. Grounding 数据工程

- Hard grounding synthesis + infeasible 负样本 + 轨迹挖掘（critic）  
- 量级参考：AgentCPM 12M grounding + 通用混合正则

## 9. Trajectory 生产：三条路线

- DAG 自动探索（checkpoint+失败回滚+重写指令）  
- 虚拟环境（可控、无验证码、长轨迹高效）  
- Mano Explorer（A11y/OmniParse + DFS + 质量打分）  
- in-policy 人类标注（accept/override）

## 10. 任务生成与难度分层

- UI-TARS-2：obfuscation / multi-hop 条件  
- Computer-RL：难度分层 + model pool  
- EvoCUA：同一 query 多轨迹更有效  
- 关键步骤 upsampling + offline DPO

## 11. 训练范式总览（推荐 recipe）

CT/Pretrain（可选）→ SFT → Online RL → Entropulse → Online RL → Offline DPO → 融合（MRPO/插值）

## 12. SFT 细节（输入组织 + 输出结构）

- 2 帧历史图像 + 全历史摘要（Mano）  
- CoT：Observation/Memory/Progress/Reflection → Thought  
- World modeling 监督

## 13. RL 细节（算法/奖励/一致性/熵）

- GRPO / PPO / MRPO  
- 分层 reward（verifier tiers）  
- token-id transport  
- Entropulse 处理熵坍塌

## 14. Verifier 体系

- Rule-based → screenshot-diff+OCR → LLM judge → Generative ORM

## 15. 环境与系统架构

- 2000–4000 并发、快照池、<10s 重置  
- Env/Rollout/DataMgr/Trainer 解耦异步；near on-policy

## 16. 观测输入：Vision-only vs A11y

- 训练混合、推理 gating；兼容 schema

## 17. 桌面应用选择：可程序化 + 易验证优先

- P0：文件/浏览器/终端/Office/VSCode/设置/文本  
- 最佳 code 自动化：Playwright、COM/UNO、gsettings/defaults 等

## 18. 方法论：8 步执行清单

1) 动作空间 2) P0 应用 3) 先做 verifier 4) grounding 5) 冷启动 SFT  
6) 启动飞轮 7) RL+熵管理 8) 融合与扩展

## 19. Failure modes → 对策

- grounding、熵坍塌、梯度冲突、验证缺口、系统约束等

## 20. 开源数据与评测地形图（表格）

- 资源组合与使用注意事项

## 21. 结论与下一步实验

- 关键 ablation 与未解问题

## 22. References

- 列出材料覆盖的主要工作与数据集

