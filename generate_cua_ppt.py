#!/usr/bin/env python3
"""Generate a CUA research presentation PPTX.

Usage:
  python generate_cua_ppt.py
  python generate_cua_ppt.py --output CUA_report.pptx
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Iterable, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

FONT_NAME = "Microsoft YaHei"
TITLE_COLOR = RGBColor(16, 43, 77)
BODY_COLOR = RGBColor(30, 30, 30)
ACCENT_COLOR = RGBColor(0, 102, 204)

BulletType = Union[str, tuple[str, int]]


def style_paragraph(paragraph, font_size: int, bold: bool = False, color: RGBColor = BODY_COLOR) -> None:
    paragraph.font.name = FONT_NAME
    paragraph.font.size = Pt(font_size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    paragraph.space_after = Pt(6)
    paragraph.line_spacing = 1.25


def add_title_slide(prs: Presentation, title: str, subtitle: str, notes: str | None = None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    title_p = slide.shapes.title.text_frame.paragraphs[0]
    style_paragraph(title_p, 40, bold=True, color=TITLE_COLOR)

    subtitle_box = slide.placeholders[1]
    subtitle_box.text = subtitle
    for p in subtitle_box.text_frame.paragraphs:
        style_paragraph(p, 20, color=BODY_COLOR)

    # Add date line
    tx = slide.shapes.add_textbox(Inches(0.8), Inches(6.7), Inches(6.0), Inches(0.4))
    tf = tx.text_frame
    tf.text = f"生成日期：{date.today().isoformat()}"
    style_paragraph(tf.paragraphs[0], 12, color=ACCENT_COLOR)

    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def _write_bullets(text_frame, bullets: Iterable[BulletType]) -> None:
    text_frame.clear()
    for idx, item in enumerate(bullets):
        if isinstance(item, tuple):
            text, level = item
        else:
            text, level = item, 0

        paragraph = text_frame.paragraphs[0] if idx == 0 else text_frame.add_paragraph()
        paragraph.text = text
        paragraph.level = level
        style_paragraph(
            paragraph,
            font_size=22 if level == 0 else 18,
            bold=False,
            color=BODY_COLOR,
        )


def add_bullet_slide(
    prs: Presentation,
    title: str,
    bullets: Iterable[BulletType],
    notes: str | None = None,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    style_paragraph(slide.shapes.title.text_frame.paragraphs[0], 34, bold=True, color=TITLE_COLOR)

    content = slide.placeholders[1]
    _write_bullets(content.text_frame, bullets)

    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def build_slides(prs: Presentation) -> None:
    add_title_slide(
        prs,
        "CUA 现有工作的系统拆解与方法论抽象",
        "面向跨平台 Desktop Agent 基座（Win / macOS / Linux）",
        notes=(
            "开场一句话：本报告目标不是复述论文，而是提炼可复用方法论，"
            "用于指导下一阶段 CUA 基座的工程与训练决策。"
        ),
    )

    add_bullet_slide(
        prs,
        "1. 汇报目标与结论预告",
        [
            "目标 1：统一分析口径，比较现有 CUA 工作",
            "目标 2：提炼可迁移方法论，而非单点 SOTA 经验",
            "目标 3：形成可执行训练路线（数据、模型、RL、评测）",
            "结论预告：数据飞轮与 Verifier 决定上限；动作空间统一是关键突破口",
        ],
        notes="先把答案给出框架，帮助听众建立预期，降低后续信息负担。",
    )

    add_bullet_slide(
        prs,
        "2. 问题定义：我们到底在优化什么？",
        [
            "任务对象：跨 OS、跨应用、长序列、可验证的真实计算机使用",
            "能力链路：感知 -> Grounding -> 规划 -> 执行 -> 纠错",
            "目标函数：Task SR + Step Efficiency + 稳定性 + 可扩展性",
            "关键提醒：Benchmark 分数高，不等于体系可扩展",
        ],
        notes="强调“系统能力”而非“单 benchmark 能力”，为后文方法论抽象铺垫。",
    )

    add_bullet_slide(
        prs,
        "3. 分析框架：五轴统一坐标",
        [
            "Axis A - Data Flywheel：采集、过滤、回流、迭代速度",
            "Axis B - Grounding：难例覆盖、负样本、A11y 融合策略",
            "Axis C - Action Space：坐标/元素/代码/API 的统一程度",
            "Axis D - RL + Verifier：reward 可编程性与训练稳定性",
            "Axis E - Infrastructure：并发环境、重置效率、成本与监控",
        ],
        notes="明确后续每个工作都会落到五轴之一，避免按论文线性叙述。",
    )

    add_bullet_slide(
        prs,
        "4. 代表工作全景图",
        [
            "Mobile-Agent-v3.5：多平台 + MRPO + 合成数据工程",
            "Mano：Explorer 自动采集 + Action Desp + 闭环修正",
            "EvoCUA：小规模高质量冷启动 + 多轮 RFT + 关键步骤 DPO",
            "UI-TARS-2：Data Flywheel + PPO 体系 + 参数插值融合",
            "Computer-RL：API-GUI 代码动作 + Entropulse + 大规模 Verifier",
        ],
        notes="先讲共性再讲差异：所有 SOTA 都依赖数据闭环与 RL，但实现路径不同。",
    )

    add_bullet_slide(
        prs,
        "5. Axis A：数据闭环对比（共识最强）",
        [
            "UI-TARS-2：in-policy 标注 + 轨迹路由（高质量->SFT，低质量->CT）",
            "Mano：自动探索为主，人工修正兜底，成功轨迹持续回流",
            "Computer-RL：Model Pool 分层采样，仅保留 verifier 成功轨迹",
            "EvoCUA：5K 轨迹冷启动 + 多轮 RFT，强调迭代效率而非一次性堆量",
            "迁移结论：数据闭环效率 > 模型结构微创新",
        ],
        notes="用“迭代效率”统一解释多篇论文现象。",
    )

    add_bullet_slide(
        prs,
        "6. Axis B：Grounding 是底座瓶颈",
        [
            "现象：专业软件、小目标、多窗口遮挡场景仍是主要失分点",
            "Mobile-Agent-v3.5：Hard grounding synthesis + infeasible 负样本",
            "AgentCPM：12M grounding 样本，且混入通用多模态数据防退化",
            "建议：Grounding 先行，未稳定前不应过早加大 RL 投入",
        ],
        notes="核心观点：后续 RL 只能放大或暴露 grounding 缺陷，不能替代基础感知学习。",
    )

    add_bullet_slide(
        prs,
        "7. Axis C：动作空间统一（当前最大分歧）",
        [
            "问题：Mobile / Web / Desktop 的 action schema 长期割裂",
            "Computer-RL：API-GUI Paradigm（Python 代码统一 GUI primitive + App API）",
            "收益：可组合控制流、可利用预训练代码能力、API 与 GUI 无缝混合",
            "建议：将代码动作作为跨平台中间表示层（而非仅 JSON）",
        ],
        notes="强调这不是格式喜好，而是可扩展性和能力上限问题。",
    )

    add_bullet_slide(
        prs,
        "8. Axis D：RL 与 Verifier 体系",
        [
            "算法分工：GRPO（轻量）/ PPO（稳定）/ Offline DPO（低成本专项对齐）",
            "Verifier 分层：Rule-based -> Screenshot Diff -> LLM-as-Judge -> Generative ORM",
            "Computer-RL：~8000 可编程 verifier，直接抬高 RL 天花板",
            "EvoCUA：关键步骤 DPO 在样本效率上优于全轨迹偏好学习",
        ],
        notes="先讲 reward 信号质量，再讲 RL 算法；算法是后验选择。",
    )

    add_bullet_slide(
        prs,
        "9. Axis E：环境与基础设施规模",
        [
            "在线 RL 的经验规模：2000-4000 并发环境（EvoCUA / Computer-RL）",
            "三层环境：采集层（50-100）/ RL 沙盒层（2k-4k）/ 虚拟渲染层",
            "关键工程指标：重置 <10s、任务快照稳定、故障可观测",
            "结论：环境工程是 RL scaling 的第一瓶颈",
        ],
        notes="强调‘更多 GPU’并不能替代‘更好的环境与 verifier’。",
    )

    add_bullet_slide(
        prs,
        "10. 开源数据版图：可用资产",
        [
            "Grounding：OS-ATLAS（13M+ elements）、GroundCUA（3.56M 标注）、Jedi（4M）",
            "Trajectory：OpenCUA/AgentNet（22,625 轨迹，3 OS）、GUI-360（1.2M+ steps）、ScaleCUA",
            "Evaluation：OSWorld（369 tasks）、WAA（154+）、ScreenSpot-Pro（1,590）",
            "经验：先用开源建立 baseline，再由自建数据补平台与任务缺口",
        ],
        notes="这页给资源盘点，下一页讲为什么仍不足。",
    )

    add_bullet_slide(
        prs,
        "11. 数据缺口与已知风险",
        [
            "缺口：macOS/Linux 长轨迹、代码级动作、跨应用工作流、失败纠错轨迹",
            "风险：数据格式不一、平台偏置、OpenCUA 与 Qwen pattern 对齐成本",
            "治理：统一 schema、去重过滤、格式转换、混合比例与 RoPE 对齐试验",
            "原则：先解决可验证任务，再向开放任务扩张",
        ],
        notes="把风险翻译成可执行工程动作，避免讨论停留在现象层。",
    )

    add_bullet_slide(
        prs,
        "12. 方法论总图（建议作为核心页）",
        [
            "L0.5：感知与 Grounding 预训练（15-20M）",
            "L1：任务分解与重组（DAG + 指令复杂化 + 多轨迹覆盖）",
            "L2：Online RL（GRPO/PPO）",
            "L2.5：Entropy 恢复（Entropulse）",
            "L3：关键步骤 DPO + 数据飞轮持续回流",
        ],
        notes="这页是整场汇报的主结论；后续几页都在解释这一流程为何成立。",
    )

    add_bullet_slide(
        prs,
        "13. 方法细节 A：数据飞轮路由",
        [
            "成功轨迹 -> SFT（强化行为先验）",
            "低质量/失败轨迹 -> CT 或反例池（维持分布与鲁棒性）",
            "部分成功轨迹 -> LLM 修正 -> SFT（提升样本利用率）",
            "成功 rollout（不同阶段策略）-> Entropulse 数据池（恢复探索）",
        ],
        notes="强调飞轮价值：不仅是‘更多数据’，而是‘更有效路由’。",
    )

    add_bullet_slide(
        prs,
        "14. 方法细节 B：训练配方建议（可执行版）",
        [
            "Phase 1 Grounding：15-20M 样本，混入 25-30% 通用多模态数据",
            "Phase 2 SFT：500K 轨迹 / 5M steps，关键步骤上采样到 15-20%",
            "Phase 3 Online RL：10,000+ 任务，2k-4k 并发环境",
            "Phase 4 Offline DPO：专打关键步骤 + 参数融合（vertical agents）",
        ],
        notes="给出量级而不是精确数字，强调这是可迭代的 planning baseline。",
    )

    add_bullet_slide(
        prs,
        "15. 方法细节 C：关键步骤学习",
        [
            "关键步骤定义：不可逆操作、分支决策点、最终提交/保存",
            "识别：Verifier 回溯 + 状态差分 + DAG 拓扑（高分支节点）",
            "训练：SFT 上采样 + Offline DPO（正负成对）",
            "收益：比全轨迹偏好学习更 sample-efficient（EvoCUA 经验）",
        ],
        notes="把‘关键步骤’从经验术语变成可标注、可训练、可评估的对象。",
    )

    add_bullet_slide(
        prs,
        "16. 方法细节 D：跨平台冲突与融合策略",
        [
            "冲突根源：UI 分布差异 + 动作语义差异导致梯度 tug-of-war",
            "方案 A（MRPO）：交替平台优化，减少 batch 内冲突",
            "方案 B（UI-TARS-2）：vertical agents 分别训练后参数插值",
            "建议顺序：先 B（稳定、可控）再评估 A（上限潜力）",
        ],
        notes="先拿稳健增益，再追求更高上限，符合工程迭代节奏。",
    )

    add_bullet_slide(
        prs,
        "17. 评测体系：从能力拆解到端到端",
        [
            "Grounding：ScreenSpot / ScreenSpot-Pro（text/icon/widget 分项）",
            "Execution：OSWorld / WAA / AssistGUI（Task SR + Efficiency）",
            "Robustness：异常弹窗、延迟、分辨率变化、失败恢复能力",
            "实践：每 checkpoint 做快速子集 + 每阶段做全量评测",
        ],
        notes="目标是让评测直接驱动训练决策，而不是仅做最终报告指标。",
    )

    add_bullet_slide(
        prs,
        "18. 6-10 个月执行路线图",
        [
            "M1-2：环境与数据基建（A11y、录制、schema、baseline）",
            "M2-4：Grounding 主训练（含 hard synthesis 与负样本）",
            "M3-5：SFT 冷启动与飞轮启动（高质量子集优先）",
            "M4-7：RL + Verifier 扩张（规则优先，LLM judge 兜底）",
            "M6-10：多尺寸训练与跨平台融合（参数插值/MRPO 对比）",
        ],
        notes="每阶段都应设置可验收指标，例如 ScreenSpot-Pro 与 OSWorld 阶段目标。",
    )

    add_bullet_slide(
        prs,
        "19. 最终结论与讨论问题",
        [
            "结论 1：CUA 上限由“数据闭环 x Verifier 质量”共同决定",
            "结论 2：统一动作空间是跨平台扩展的结构性问题",
            "结论 3：Grounding 质量决定 RL 是否真正有效",
            "讨论 Q1：A11y 与纯视觉的最优混合比如何设定？",
            "讨论 Q2：何时从 GUI-first 切换到 code-first 代理？",
        ],
        notes="结尾用问题引导讨论，把汇报转成下一步研究决策会议。",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CUA research methodology PPT.")
    parser.add_argument(
        "--output",
        default="CUA_research_methodology_report.pptx",
        help="Output PPTX file path",
    )
    args = parser.parse_args()

    prs = Presentation()
    prs.slide_width = Inches(13.333)   # 16:9 widescreen
    prs.slide_height = Inches(7.5)

    build_slides(prs)
    prs.save(args.output)
    print(f"[OK] PPT generated: {args.output}")
    print(f"[OK] Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
