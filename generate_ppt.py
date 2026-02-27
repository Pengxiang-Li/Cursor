#!/usr/bin/env python3
"""
CUA 技术调研报告 PPT 生成脚本
面向资深 CUA 研究员，分析现有工作方法论
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import copy

# ============================================================
# Color Palette (Light professional theme)
# ============================================================
BG_DARK       = RGBColor(0xFA, 0xFA, 0xFC)  # Near-white background
BG_CARD       = RGBColor(0xF0, 0xF2, 0xF7)  # Light gray card
ACCENT_BLUE   = RGBColor(0x2D, 0x5B, 0xE3)  # Primary accent (deeper blue)
ACCENT_CYAN   = RGBColor(0x00, 0x9B, 0x8D)  # Secondary accent (teal)
ACCENT_ORANGE = RGBColor(0xE8, 0x6A, 0x17)  # Warning/highlight
ACCENT_PURPLE = RGBColor(0x7C, 0x4D, 0xFF)  # Tertiary accent
ACCENT_PINK   = RGBColor(0xD6, 0x33, 0x6C)  # Quaternary accent
TEXT_WHITE     = RGBColor(0x1A, 0x1A, 0x2E)  # Primary text (dark)
TEXT_LIGHT     = RGBColor(0x3D, 0x3D, 0x56)  # Secondary text
TEXT_DIM       = RGBColor(0x78, 0x78, 0x96)  # Dim text
DIVIDER        = RGBColor(0xD8, 0xDC, 0xE6)  # Divider lines
GREEN          = RGBColor(0x1B, 0x9E, 0x4B)  # Success
RED            = RGBColor(0xDC, 0x35, 0x45)  # Error

SLIDE_WIDTH  = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_WIDTH
prs.slide_height = SLIDE_HEIGHT


# ============================================================
# Helper Functions
# ============================================================
def add_bg(slide, color=BG_DARK):
    """Fill slide background with solid color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape(slide, left, top, width, height, fill_color=None, line_color=None, line_width=Pt(0)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape


def add_rounded_rect(slide, left, top, width, height, fill_color=BG_CARD):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = RGBColor(0xDE, 0xE1, 0xEB)
    shape.line.width = Pt(1)
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=Pt(14),
                 color=TEXT_WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Arial"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_multi_text(slide, left, top, width, height, lines, default_size=Pt(14),
                   default_color=TEXT_WHITE, line_spacing=Pt(24)):
    """
    lines: list of dicts with keys: text, size, color, bold, alignment
    """
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line_info in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line_info.get("text", "")
        p.font.size = line_info.get("size", default_size)
        p.font.color.rgb = line_info.get("color", default_color)
        p.font.bold = line_info.get("bold", False)
        p.font.name = line_info.get("font", "Arial")
        p.alignment = line_info.get("alignment", PP_ALIGN.LEFT)
        if "spacing" in line_info:
            p.space_after = line_info["spacing"]
        else:
            p.space_after = Pt(4)
    return txBox


def add_section_header(slide, number, title, subtitle=""):
    add_bg(slide, color=RGBColor(0xF5, 0xF7, 0xFB))
    add_shape(slide, Inches(0), Inches(0), Inches(0.08), SLIDE_HEIGHT, fill_color=ACCENT_BLUE)

    add_text_box(slide, Inches(0.8), Inches(1.5), Inches(2), Inches(1.2),
                 f"PART {number}", font_size=Pt(20), color=ACCENT_BLUE, bold=True)

    add_text_box(slide, Inches(0.8), Inches(2.5), Inches(11), Inches(1.5),
                 title, font_size=Pt(44), color=TEXT_WHITE, bold=True)

    if subtitle:
        add_text_box(slide, Inches(0.8), Inches(4.2), Inches(11), Inches(1),
                     subtitle, font_size=Pt(18), color=TEXT_LIGHT)

    add_shape(slide, Inches(0.8), Inches(5.5), Inches(3), Inches(0.04), fill_color=ACCENT_BLUE)


def add_page_number(slide, num, total):
    add_text_box(slide, Inches(12.2), Inches(7.0), Inches(1), Inches(0.4),
                 f"{num}/{total}", font_size=Pt(10), color=TEXT_DIM, alignment=PP_ALIGN.RIGHT)


def add_top_bar(slide, title, subtitle=""):
    add_bg(slide)
    add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.9), fill_color=RGBColor(0xFF, 0xFF, 0xFF))
    add_shape(slide, Inches(0), Inches(0.88), SLIDE_WIDTH, Inches(0.03), fill_color=ACCENT_BLUE)
    add_text_box(slide, Inches(0.6), Inches(0.15), Inches(8), Inches(0.6),
                 title, font_size=Pt(22), color=TEXT_WHITE, bold=True)
    if subtitle:
        add_text_box(slide, Inches(9), Inches(0.18), Inches(4), Inches(0.6),
                     subtitle, font_size=Pt(12), color=TEXT_DIM, alignment=PP_ALIGN.RIGHT)


def add_card(slide, left, top, width, height, title, bullets, title_color=ACCENT_BLUE,
             bullet_color=TEXT_LIGHT, title_size=Pt(16), bullet_size=Pt(12)):
    card = add_rounded_rect(slide, left, top, width, height)
    lines = [{"text": title, "size": title_size, "color": title_color, "bold": True, "spacing": Pt(8)}]
    for b in bullets:
        if isinstance(b, dict):
            lines.append(b)
        else:
            lines.append({"text": f"  {b}", "size": bullet_size, "color": bullet_color})
    add_multi_text(slide, left + Inches(0.2), top + Inches(0.15),
                   width - Inches(0.4), height - Inches(0.3), lines)
    return card


def make_table(slide, left, top, width, rows_data, col_widths, header_color=ACCENT_BLUE):
    """
    rows_data: list of lists of strings. First row is header.
    col_widths: list of Inches values
    """
    n_rows = len(rows_data)
    n_cols = len(rows_data[0])
    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, Inches(0.4 * n_rows))
    table = table_shape.table

    for ci, cw in enumerate(col_widths):
        table.columns[ci].width = cw

    for ri, row in enumerate(rows_data):
        for ci, cell_text in enumerate(row):
            cell = table.cell(ri, ci)
            cell.text = cell_text
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11) if ri > 0 else Pt(12)
                p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if ri == 0 else TEXT_LIGHT
                p.font.bold = (ri == 0)
                p.font.name = "Arial"
            if ri == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0x2D, 0x5B, 0xE3)
                for p in cell.text_frame.paragraphs:
                    p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if ri % 2 == 1 else RGBColor(0xF0, 0xF2, 0xF7)
    return table_shape


TOTAL_SLIDES = 26

# ============================================================
# SLIDE 1: Title Slide
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
add_bg(slide)

add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), fill_color=ACCENT_BLUE)
add_shape(slide, Inches(0), SLIDE_HEIGHT - Inches(0.06), SLIDE_WIDTH, Inches(0.06), fill_color=ACCENT_BLUE)

add_multi_text(slide, Inches(1.5), Inches(1.8), Inches(10), Inches(4), [
    {"text": "CUA 技术调研报告", "size": Pt(52), "color": ACCENT_BLUE, "bold": True, "spacing": Pt(12)},
    {"text": "Computer Use Agent — 现有方法论深度分析", "size": Pt(24), "color": ACCENT_CYAN, "spacing": Pt(30)},
    {"text": "基于 Mobile-Agent-v3.5 / Mano / EvoCUA / UI-TARS-2 / AgentCPM / Computer-RL / DART-GUI",
     "size": Pt(14), "color": TEXT_LIGHT, "spacing": Pt(8)},
    {"text": "的系统性技术路线对比与方法论提炼", "size": Pt(14), "color": TEXT_LIGHT, "spacing": Pt(30)},
])

add_shape(slide, Inches(1.5), Inches(5.3), Inches(4), Inches(0.04), fill_color=ACCENT_BLUE)

add_multi_text(slide, Inches(1.5), Inches(5.6), Inches(10), Inches(1.5), [
    {"text": "目标: 从数据工程、训练范式、RL策略、基础设施四个维度", "size": Pt(14), "color": TEXT_DIM},
    {"text": "       系统性提炼 CUA 领域的核心方法论", "size": Pt(14), "color": TEXT_DIM},
])

add_page_number(slide, 1, TOTAL_SLIDES)

# ============================================================
# SLIDE 2: Agenda
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "AGENDA", "讲解流程")

sections = [
    ("01", "调研概览", "调研范围、7大代表性工作概览与核心维度", ACCENT_BLUE),
    ("02", "数据工程方法论", "数据类型体系、采集策略矩阵、数据飞轮与质量控制", ACCENT_CYAN),
    ("03", "训练范式", "多阶段训练流程、SFT关键技巧、输出格式设计", ACCENT_PURPLE),
    ("04", "RL 策略", "算法选择、Reward设计层级、Entropy Collapse与跨平台策略", ACCENT_ORANGE),
    ("05", "基础设施", "环境体系、Verifier层级设计、开源数据与缺口分析", ACCENT_PINK),
    ("06", "核心方法论总结", "五大核心洞察、通用技术路线图", GREEN),
]
for i, (num, title, desc, color) in enumerate(sections):
    y = Inches(1.2) + Inches(i * 0.95)
    add_shape(slide, Inches(0.6), y, Inches(0.06), Inches(0.7), fill_color=color)
    add_text_box(slide, Inches(0.9), y + Inches(0.02), Inches(0.6), Inches(0.35),
                 num, font_size=Pt(22), color=color, bold=True)
    add_text_box(slide, Inches(1.8), y + Inches(0.02), Inches(3), Inches(0.35),
                 title, font_size=Pt(18), color=TEXT_WHITE, bold=True)
    add_text_box(slide, Inches(5.0), y + Inches(0.05), Inches(7.5), Inches(0.6),
                 desc, font_size=Pt(13), color=TEXT_LIGHT)

add_page_number(slide, 2, TOTAL_SLIDES)

# ============================================================
# SLIDE 3: Part 1 Section Header
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "01", "调研概览",
                   "7 大代表性工作 × 4 维度系统性对比")
add_page_number(slide, 3, TOTAL_SLIDES)

# ============================================================
# SLIDE 4: Surveyed Works Overview
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "调研范围: 7 大代表性工作", "Part 01 — 概览")

rows = [
    ["工作", "基座模型", "平台", "核心贡献", "OSWorld SR"],
    ["UI-TARS-2", "Seed 1.6 (多尺寸)", "全平台", "Data Flywheel + PPO + 参数插值", "SOTA"],
    ["Computer-RL", "GLM-4V", "Desktop", "API-GUI Paradigm + Entropulse", "SOTA-class"],
    ["EvoCUA", "OpenCUA/Qwen3-VL", "Desktop", "RFT多轮迭代 + 关键步骤DPO", "55 (OSW)"],
    ["Mobile-Agent-v3.5", "自研", "全平台", "DAG探索 + MRPO + 世界模型", "—"],
    ["Mano", "UI-TARS-1.5-7B", "Desktop", "Explorer + Action Desp + 闭环", "—"],
    ["AgentCPM", "MiniCPM-V 8B", "Android", "12M Grounding预训练 + GRPO", "—"],
    ["DART-GUI", "UI-TARS-1.5-7B", "Desktop", "4大自适应策略 + Experience Pool", "—"],
]
col_w = [Inches(2.0), Inches(2.0), Inches(1.3), Inches(5.3), Inches(1.5)]
make_table(slide, Inches(0.6), Inches(1.2), Inches(12.1), rows, col_w)

add_text_box(slide, Inches(0.6), Inches(6.6), Inches(11), Inches(0.6),
             "共性: 所有SOTA方案均采用 多阶段训练(Grounding→SFT→RL) + 数据闭环 + 多层Verifier",
             font_size=Pt(13), color=ACCENT_CYAN, bold=True)

add_page_number(slide, 4, TOTAL_SLIDES)

# ============================================================
# SLIDE 5: Analysis Dimensions
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "分析维度: CUA 系统全景", "Part 01 — 概览")

dims = [
    ("数据工程", "Grounding数据 + 轨迹数据 + Agent增强数据\n采集策略 × 质量控制 × 数据飞轮", ACCENT_BLUE, Inches(0.5)),
    ("训练范式", "CT → SFT → RL 多阶段渐进\nCoT格式 × 数据配比 × 关键步骤策略", ACCENT_CYAN, Inches(3.7)),
    ("RL 策略", "GRPO/PPO/DPO 算法选择\nReward层级 × Entropy管理 × 跨平台优化", ACCENT_ORANGE, Inches(6.9)),
    ("基础设施", "沙盒环境 × Verifier体系 × A11y工具链\n并发调度 × 数据格式统一", ACCENT_PURPLE, Inches(10.1)),
]
for title, desc, color, x in dims:
    card = add_rounded_rect(slide, x, Inches(1.5), Inches(2.8), Inches(4.5), fill_color=BG_CARD)
    add_shape(slide, x, Inches(1.5), Inches(2.8), Inches(0.06), fill_color=color)
    add_multi_text(slide, x + Inches(0.2), Inches(1.8), Inches(2.4), Inches(4), [
        {"text": title, "size": Pt(20), "color": color, "bold": True, "spacing": Pt(16)},
        {"text": desc, "size": Pt(13), "color": TEXT_LIGHT, "spacing": Pt(6)},
    ])

add_text_box(slide, Inches(0.5), Inches(6.3), Inches(12), Inches(0.8),
             "核心命题: 数据闭环 > 模型架构；RL是性能跃迁的关键，但瓶颈在环境与Verifier",
             font_size=Pt(14), color=ACCENT_ORANGE, bold=True)

add_page_number(slide, 5, TOTAL_SLIDES)

# ============================================================
# SLIDE 6: Part 2 Section Header - Data Engineering
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "02", "数据工程方法论",
                   "从数据类型、采集策略到数据飞轮的系统性分析")
add_page_number(slide, 6, TOTAL_SLIDES)

# ============================================================
# SLIDE 7: Data Types Taxonomy
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "数据类型体系: 三大支柱", "Part 02 — 数据工程")

add_card(slide, Inches(0.4), Inches(1.2), Inches(3.9), Inches(5.5),
         "Grounding 数据", [
             "定位能力基础，所有工作的第一步",
             "",
             {"text": "AgentCPM: 12M样本(含50%通用)", "size": Pt(11), "color": ACCENT_CYAN},
             {"text": "Mobile-Agent-v3.5:", "size": Pt(11), "color": ACCENT_CYAN},
             "  · Hard Grounding Synthesis",
             "  · Infeasible负样本(多模型共识)",
             "  · Critic模型从轨迹挖掘",
             "",
             {"text": "关键: 负样本增强拒答能力", "size": Pt(12), "color": ACCENT_ORANGE, "bold": True},
         ], title_color=ACCENT_BLUE)

add_card(slide, Inches(4.6), Inches(1.2), Inches(3.9), Inches(5.5),
         "Trajectory 轨迹数据", [
             "模型学会\"怎么做\"的核心",
             "",
             {"text": "采集方式 (混合生产):", "size": Pt(11), "color": ACCENT_CYAN},
             "  · DAG自动化探索 (MA-v3.5)",
             "  · DFS探索+LLM评审 (Mano)",
             "  · 虚拟环境生成 (MA-v3.5)",
             "  · In-Situ人工标注 (UI-TARS-2)",
             "  · 教程驱动合成 (AgentTrek)",
             "",
             {"text": "关键: Cold-start质量>数量", "size": Pt(12), "color": ACCENT_ORANGE, "bold": True},
         ], title_color=ACCENT_CYAN)

add_card(slide, Inches(8.8), Inches(1.2), Inches(4.1), Inches(5.5),
         "Agent 增强数据", [
             "让模型\"会思考\"的关键",
             "",
             {"text": "统一CoT合成 (MA-v3.5):", "size": Pt(11), "color": ACCENT_CYAN},
             "  Observation → Memory →",
             "  Reflection → Thought → Action",
             "",
             {"text": "世界模型监督 (MA-v3.5):", "size": Pt(11), "color": ACCENT_CYAN},
             "  预测\"动作后界面如何变化\"",
             "",
             {"text": "Action Desp (Mano): +2.8分", "size": Pt(11), "color": ACCENT_CYAN},
             "",
             {"text": "关键: CoT结构设计显著影响性能", "size": Pt(12), "color": ACCENT_ORANGE, "bold": True},
         ], title_color=ACCENT_PURPLE)

add_page_number(slide, 7, TOTAL_SLIDES)

# ============================================================
# SLIDE 8: Data Collection Strategies Matrix
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "数据采集策略矩阵", "Part 02 — 数据工程")

rows = [
    ["策略", "代表工作", "优势", "劣势", "产出效率"],
    ["DAG自动化探索", "Mobile-Agent-v3.5", "可控 + Checkpoint验证\n失败轨迹可截断重用", "需人工建DAG", "高 (自动)"],
    ["DFS深度探索", "Mano Explorer", "自动发现功能路径\nClaudeWq评审质量", "循环路径风险", "高 (自动)"],
    ["虚拟环境生成", "Mobile-Agent-v3.5", "精确长轨迹\n无验证码干扰", "需开发虚拟环境", "极高"],
    ["In-Situ标注", "UI-TARS-2", "Think-aloud真实推理\n分布最真实", "人力成本高", "低 (人工)"],
    ["教程驱动合成", "AgentTrek", "利用海量教程\n自然语言对齐好", "教程≠最优路径", "中 (半自动)"],
    ["多模型Teacher", "Computer-RL", "模型间方差互补\n分层难度覆盖", "API成本", "中 (自动)"],
    ["In-policy标注", "UI-TARS-2", "On-policy分布一致\n人工accept/override", "需成熟基座", "低 (人机)"],
]
col_w = [Inches(1.8), Inches(2.0), Inches(3.0), Inches(2.3), Inches(1.5)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.3), rows, col_w)

add_text_box(slide, Inches(0.5), Inches(6.5), Inches(12), Inches(0.7),
             "方法论: 自动化为主体(70-80%) + 人工标注为兜底(10-20%) + 开源数据补充(10%)",
             font_size=Pt(14), color=ACCENT_CYAN, bold=True)

add_page_number(slide, 8, TOTAL_SLIDES)

# ============================================================
# SLIDE 9: Data Flywheel
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "数据飞轮: 从一次性采集到持续迭代", "Part 02 — 数据工程")

add_card(slide, Inches(0.4), Inches(1.2), Inches(6), Inches(2.6),
         "UI-TARS-2 Data Flywheel", [
             {"text": "RL Rollout → Verifier V(s) 验证", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "  V(s)=高 → SFT 数据集 (正循环)", "size": Pt(13), "color": GREEN},
             {"text": "  V(s)=低 → CT 数据集 (也不浪费)", "size": Pt(13), "color": ACCENT_ORANGE},
             {"text": "核心: 模型既是学习者，也是数据生产者", "size": Pt(12), "color": ACCENT_CYAN, "bold": True},
         ], title_color=ACCENT_BLUE)

add_card(slide, Inches(6.8), Inches(1.2), Inches(6), Inches(2.6),
         "Mano 闭环循环", [
             {"text": "Online RL 成功轨迹 → 直接加入SFT迭代", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "中间有错但最终成功 →", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "  LLM生成草稿 + 人工专家修正 → SFT", "size": Pt(13), "color": GREEN},
             {"text": "核心: 错误轨迹也有修复价值", "size": Pt(12), "color": ACCENT_CYAN, "bold": True},
         ], title_color=ACCENT_PURPLE)

add_card(slide, Inches(0.4), Inches(4.1), Inches(6), Inches(2.6),
         "Computer-RL Entropulse", [
             {"text": "RL Phase 1 所有成功Rollout (~130K步)", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "  → 不同训练阶段Policy生成, 天然多样性", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "  → SFT一轮恢复Entropy → 继续RL", "size": Pt(13), "color": GREEN},
             {"text": "核心: RL产出的数据反哺SFT", "size": Pt(12), "color": ACCENT_CYAN, "bold": True},
         ], title_color=ACCENT_ORANGE)

add_card(slide, Inches(6.8), Inches(4.1), Inches(6), Inches(2.6),
         "EvoCUA 迭代式RFT", [
             {"text": "5K轨迹冷启动 → 多轮RFT → 51分", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "减少数据也能51分 → +DPO → 55分", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "每个query平均4-5条正确轨迹", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "核心: 迭代质量 > 一次性堆量", "size": Pt(12), "color": ACCENT_CYAN, "bold": True},
         ], title_color=ACCENT_PINK)

add_page_number(slide, 9, TOTAL_SLIDES)

# ============================================================
# SLIDE 10: Data Scale Reference
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "数据规模参考与 Cold-Start 洞察", "Part 02 — 数据工程")

rows = [
    ["阶段", "AgentCPM", "Computer-RL", "EvoCUA", "Mano"],
    ["Grounding预训练", "12M (含50%通用)", "—", "—", "—"],
    ["SFT轨迹", "55K轨迹/470K步", "180K步", "5K轨迹(冷启动)", "混合比 10%/70%/20%"],
    ["通用数据混合", "50%", "0%", "50%", "0%"],
    ["RL Task数", "—", "~8,000", "~3,000-5,000", "—"],
    ["RL 环境并发", "—", "数千", "2,000-4,000", "—"],
]
col_w = [Inches(2.0), Inches(2.5), Inches(2.5), Inches(2.5), Inches(2.6)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.1), rows, col_w)

add_card(slide, Inches(0.4), Inches(4.5), Inches(12.5), Inches(2.5),
         "Cold-Start 关键洞察", [
             {"text": "1. 质量 > 数量: Computer-RL仅180K步完成可用cold-start; EvoCUA 5K轨迹→51分", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "2. 全部通过Verifier验证; 多个强模型作为Teacher取最优 (Computer-RL Model Pool)", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "3. 按难度分层采集: Easy→直接采集 / Medium→SFT后模型采样 / Hard→多模型反复尝试", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "4. 每个query多条轨迹 > 更多query: 同一任务不同解法提供更好的policy space覆盖 (EvoCUA)", "size": Pt(13), "color": ACCENT_ORANGE, "bold": True},
             {"text": "5. 通用数据混合防止mode collapse: AgentCPM 50%, Qwen基座可降至25-30%", "size": Pt(13), "color": TEXT_LIGHT},
         ], title_color=GREEN)

add_page_number(slide, 10, TOTAL_SLIDES)

# ============================================================
# SLIDE 11: Part 3 Section Header - Training
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "03", "训练范式",
                   "从持续预训练到多阶段对齐的方法论提炼")
add_page_number(slide, 11, TOTAL_SLIDES)

# ============================================================
# SLIDE 12: Multi-Stage Training Overview
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "多阶段训练范式: 各工作对比", "Part 03 — 训练范式")

rows = [
    ["工作", "Stage 1", "Stage 2", "Stage 3", "Stage 4+"],
    ["UI-TARS-2", "CT (Seed1.6基座)", "SFT (高占比轨迹)", "Multi-turn PPO", "参数插值融合"],
    ["Computer-RL", "BC (180K步)", "Online GRPO", "Entropulse (SFT)", "Online GRPO P2"],
    ["AgentCPM", "Grounding (12M)", "SFT (6.9M)", "GRPO", "—"],
    ["Mobile-Agent-v3.5", "Pretrain (跨平台)", "SFT (CoT轨迹)", "MRPO", "—"],
    ["Mano", "— (基于UI-TARS-1.5)", "SFT (混合)", "Offline RL", "Online RL + 闭环"],
    ["EvoCUA", "— (基于OpenCUA)", "Cold-start SFT", "多轮RFT", "DPO (关键步骤)"],
    ["DART-GUI", "— (基于UI-TARS-1.5)", "—", "Step-wise GRPO", "—"],
]
col_w = [Inches(2.0), Inches(2.5), Inches(2.5), Inches(2.6), Inches(2.5)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.1), rows, col_w)

add_card(slide, Inches(0.4), Inches(5.3), Inches(12.5), Inches(1.5),
         "共性模式", [
             {"text": "感知/Grounding → SFT对齐 → RL优化  是所有SOTA的通用路径", "size": Pt(14), "color": ACCENT_CYAN},
             {"text": "差异在于: CT是否必要取决于基座能力; RL后是否需要entropy恢复; 多平台是否需要分别训练后融合", "size": Pt(12), "color": TEXT_LIGHT},
         ], title_color=ACCENT_BLUE)

add_page_number(slide, 12, TOTAL_SLIDES)

# ============================================================
# SLIDE 13: SFT Key Techniques
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "SFT 关键技巧矩阵", "Part 03 — 训练范式")

rows = [
    ["技巧", "来源", "效果", "要点"],
    ["In-policy标注", "UI-TARS-2", "训练-推理分布一致", "模型Rollout→人工accept/override"],
    ["历史帧策略", "Mano", "最优性能平衡", "前2帧截图 + 全部历史文本摘要"],
    ["CoT Warm-up", "AgentCPM", "引导推理能力", "早期混5%纯CoT数据,逐步增加轨迹"],
    ["Action Desp", "Mano", "+2.8分", "Thought和Action间加一句话摘要"],
    ["World Model", "MA-v3.5", "提升前瞻性", "训练预测\"动作后界面变化\""],
    ["关键步骤上采样", "EvoCUA", "SFT中15-20%", "识别决定性步骤: Verifier回溯/状态变化"],
    ["通用数据混合", "AgentCPM", "防mode collapse", "基座弱50%, 基座强25-30%"],
]
col_w = [Inches(2.0), Inches(1.6), Inches(2.0), Inches(6.5)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.1), rows, col_w)

add_page_number(slide, 13, TOTAL_SLIDES)

# ============================================================
# SLIDE 14: Output Format Design
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "输出格式设计: CoT 结构对比", "Part 03 — 训练范式")

add_card(slide, Inches(0.4), Inches(1.2), Inches(4.0), Inches(5.5),
         "Mobile-Agent-v3.5 (五段式)", [
             {"text": "[Observation]", "size": Pt(13), "color": ACCENT_BLUE, "bold": True},
             "  当前界面状态观察",
             {"text": "[Memory]", "size": Pt(13), "color": ACCENT_BLUE, "bold": True},
             "  记住关键信息(价格/天气等)",
             {"text": "[Reflection & Progress]", "size": Pt(13), "color": ACCENT_BLUE, "bold": True},
             "  反思 + 任务进度追踪",
             {"text": "[Thought]", "size": Pt(13), "color": ACCENT_BLUE, "bold": True},
             "  推理下一步动作",
             {"text": "[Conclusion/Action]", "size": Pt(13), "color": ACCENT_BLUE, "bold": True},
             "  执行具体操作",
             "",
             {"text": "最完整, 适合SFT阶段", "size": Pt(12), "color": ACCENT_ORANGE},
         ], title_color=ACCENT_BLUE)

add_card(slide, Inches(4.7), Inches(1.2), Inches(3.9), Inches(5.5),
         "Mano (三段式 + Desp)", [
             {"text": "<think>", "size": Pt(13), "color": ACCENT_PURPLE, "bold": True},
             "  分析 + 规划 + 反思",
             {"text": "</think>", "size": Pt(13), "color": ACCENT_PURPLE, "bold": True},
             "",
             {"text": "<summary>", "size": Pt(13), "color": GREEN, "bold": True},
             "  一句话摘要下一步",
             {"text": "  \"Move the mouse to...\"", "size": Pt(11), "color": TEXT_DIM},
             {"text": "</summary>", "size": Pt(13), "color": GREEN, "bold": True},
             "",
             {"text": "<action>", "size": Pt(13), "color": ACCENT_ORANGE, "bold": True},
             "  drag(start_box=...)",
             {"text": "</action>", "size": Pt(13), "color": ACCENT_ORANGE, "bold": True},
             "",
             {"text": "Action Desp单项+2.8分", "size": Pt(12), "color": ACCENT_ORANGE, "bold": True},
         ], title_color=ACCENT_PURPLE)

add_card(slide, Inches(8.9), Inches(1.2), Inches(4.0), Inches(5.5),
         "Computer-RL (代码式)", [
             {"text": "Thought:", "size": Pt(13), "color": ACCENT_CYAN, "bold": True},
             "  自然语言推理过程",
             "",
             {"text": "```python", "size": Pt(13), "color": GREEN, "bold": True},
             {"text": "click(x=520, y=340)", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "type_text('Hello')", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "hotkey('ctrl', 's')", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "# App-specific API", "size": Pt(12), "color": TEXT_DIM},
             {"text": "sheet.set_cell('A1',v)", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "```", "size": Pt(13), "color": GREEN, "bold": True},
             "",
             {"text": "统一GUI+API, 复用代码能力", "size": Pt(12), "color": ACCENT_ORANGE, "bold": True},
         ], title_color=ACCENT_CYAN)

add_page_number(slide, 14, TOTAL_SLIDES)

# ============================================================
# SLIDE 15: Part 4 Section Header - RL
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "04", "RL 策略",
                   "从算法选择到 Entropy 管理的方法论提炼")
add_page_number(slide, 15, TOTAL_SLIDES)

# ============================================================
# SLIDE 16: RL Algorithm Landscape
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "RL 算法选择: 各工作实践对比", "Part 04 — RL 策略")

rows = [
    ["算法", "使用者", "特点", "适用场景"],
    ["Step-level GRPO", "Computer-RL, AgentCPM\nDART-GUI", "无Value Network, 显存低\n适合VLM", "主力Online RL"],
    ["PPO (增强版)", "UI-TARS-2", "更稳定, 需额外Value Model\n+Value Pretraining", "大规模多轮RL"],
    ["MRPO", "Mobile-Agent-v3.5", "交替多平台优化\n解决梯度冲突", "跨平台联合训练"],
    ["Offline DPO", "EvoCUA, Mano", "无需环境交互\n成本低", "关键步骤专项优化"],
    ["多轮RFT", "EvoCUA", "迭代式rejection sampling\n逐轮提升", "数据有限时"],
]
col_w = [Inches(2.0), Inches(2.5), Inches(4.0), Inches(3.6)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.1), rows, col_w)

add_card(slide, Inches(0.4), Inches(5.2), Inches(12.5), Inches(1.6),
         "推荐路线", [
             {"text": "Step-GRPO (主力) → Entropulse (恢复entropy) → GRPO/PPO (继续) → Offline DPO (关键步骤专项)",
              "size": Pt(14), "color": ACCENT_CYAN, "bold": True},
             {"text": "UI-TARS-2证明PPO比GRPO在该领域更稳定, 但GRPO显存友好; 实际选择取决于资源",
              "size": Pt(12), "color": TEXT_LIGHT},
         ], title_color=ACCENT_BLUE)

add_page_number(slide, 16, TOTAL_SLIDES)

# ============================================================
# SLIDE 17: Reward Design Hierarchy
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "Reward 设计: 四层级体系", "Part 04 — RL 策略")

tiers = [
    ("Tier 1: Rule-based Verifier", "最精确, 范围窄",
     ["文件系统状态检查", "文档结构解析 (Computer-RL: SpreadsheetBench)", 
      "系统配置读取", "OSWorld execution scripts", "JS脚本查询runtime (UI-TARS-2)"],
     ACCENT_BLUE, Inches(0.4)),
    ("Tier 2: Screenshot-diff", "中等精度",
     ["前后截图关键区域比对", "OCR验证文本变化", "像素级比较"],
     ACCENT_CYAN, Inches(3.4)),
    ("Tier 3: LLM-as-Judge", "灵活, 精度依赖prompt",
     ["任务指令 + 初始/最终截图", "→ 成功/失败 + 评分",
      "EvoCUA: 全部模型生成verifier",
      "UI-TARS-2: Ground-truth匹配"],
     ACCENT_ORANGE, Inches(6.4)),
    ("Tier 4: Generative ORM", "自训练, 最灵活",
     ["UI-TARS-2独创", "输入: 历史文本 + 最近5帧截图",
      "输出: 标量评分", "模型自身训练为Reward Model"],
     ACCENT_PURPLE, Inches(9.4)),
]
for title, subtitle, bullets, color, x in tiers:
    add_rounded_rect(slide, x, Inches(1.2), Inches(2.8), Inches(4.5), fill_color=BG_CARD)
    add_shape(slide, x, Inches(1.2), Inches(2.8), Inches(0.06), fill_color=color)
    lines = [
        {"text": title, "size": Pt(14), "color": color, "bold": True, "spacing": Pt(4)},
        {"text": subtitle, "size": Pt(11), "color": TEXT_DIM, "spacing": Pt(12)},
    ]
    for b in bullets:
        lines.append({"text": f"  · {b}", "size": Pt(11), "color": TEXT_LIGHT})
    add_multi_text(slide, x + Inches(0.15), Inches(1.4), Inches(2.5), Inches(4), lines)

add_text_box(slide, Inches(0.5), Inches(5.9), Inches(12), Inches(0.8),
             "Verifier构建优先级: 文件管理(低) → 文本编辑(低) → 终端(低) → 浏览器(中) → Office(中) → 设置(中) → IDE(高)",
             font_size=Pt(12), color=ACCENT_ORANGE)
add_text_box(slide, Inches(0.5), Inches(6.4), Inches(12), Inches(0.5),
             "核心洞察: Computer-RL ~8000个可编程Verifier是其成功关键; EvoCUA证明纯模型生成Verifier也可行",
             font_size=Pt(12), color=ACCENT_CYAN, bold=True)

add_page_number(slide, 17, TOTAL_SLIDES)

# ============================================================
# SLIDE 18: Entropy Collapse & Solutions
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "Entropy Collapse 与解决方案", "Part 04 — RL 策略")

add_card(slide, Inches(0.4), Inches(1.2), Inches(6), Inches(2.5),
         "问题: RL 后期 Entropy 下降", [
             {"text": "Computer-RL: 训练~180步后性能触顶, Entropy显著下降", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "模型变得过于自信且单一 (Mode Collapse)", "size": Pt(13), "color": RED},
             {"text": "探索能力丧失 → 无法发现更优策略", "size": Pt(13), "color": RED},
         ], title_color=RED)

add_card(slide, Inches(6.8), Inches(1.2), Inches(6), Inches(2.5),
         "解决方案 1: Entropulse (Computer-RL)", [
             {"text": "收集RL阶段所有成功Rollout (~130K步)", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "→ 用这些数据做一轮SFT", "size": Pt(13), "color": GREEN},
             {"text": "→ 强行恢复Entropy + 保持高成功率", "size": Pt(13), "color": GREEN},
             {"text": "→ 继续RL, 突破Phase 1天花板 → SOTA", "size": Pt(13), "color": ACCENT_CYAN, "bold": True},
         ], title_color=GREEN)

add_card(slide, Inches(0.4), Inches(4.0), Inches(4), Inches(2.8),
         "解决方案 2: Value Pretraining", [
             {"text": "来源: UI-TARS-2", "size": Pt(12), "color": TEXT_DIM},
             {"text": "先固定Policy, 离线训练Value模型至收敛", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "解决初始偏差导致的训练崩溃", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "+ Decoupled GAE:", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "  解耦长序列Advantage计算", "size": Pt(12), "color": TEXT_LIGHT},
         ], title_color=ACCENT_PURPLE)

add_card(slide, Inches(4.7), Inches(4.0), Inches(4), Inches(2.8),
         "解决方案 3: 自适应策略", [
             {"text": "来源: DART-GUI", "size": Pt(12), "color": TEXT_DIM},
             {"text": "1. Dynamic Rollout Number", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "2. Dynamic Trajectory Length", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "3. High-Entropy Step Selection", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "   只对高熵step算loss", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "4. Distribution Alignment", "size": Pt(13), "color": ACCENT_CYAN},
         ], title_color=ACCENT_ORANGE)

add_card(slide, Inches(9.0), Inches(4.0), Inches(3.8), Inches(2.8),
         "解决方案 4: Experience Pool", [
             {"text": "来源: DART-GUI", "size": Pt(12), "color": TEXT_DIM},
             {"text": "预先为困难任务采集成功轨迹", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "若当前batch全部失败:", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "  → 从池中补一条正样本", "size": Pt(13), "color": GREEN},
             {"text": "保证正负样本共存", "size": Pt(13), "color": GREEN},
         ], title_color=ACCENT_PINK)

add_page_number(slide, 18, TOTAL_SLIDES)

# ============================================================
# SLIDE 19: Cross-Platform Training Strategies
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "跨平台训练策略", "Part 04 — RL 策略")

add_card(slide, Inches(0.4), Inches(1.2), Inches(3.9), Inches(3.0),
         "问题: 梯度冲突", [
             {"text": "Mobile-Agent-v3.5 发现:", "size": Pt(13), "color": TEXT_DIM},
             {"text": "手机/PC/Web轨迹混在一个Batch", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "→ 动作空间和界面逻辑差异大", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "→ 严重的梯度冲突 (Tug-of-war)", "size": Pt(13), "color": RED, "bold": True},
         ], title_color=RED)

add_card(slide, Inches(4.6), Inches(1.2), Inches(3.9), Inches(3.0),
         "方案A: MRPO交替训练", [
             {"text": "来源: Mobile-Agent-v3.5", "size": Pt(12), "color": TEXT_DIM},
             {"text": "Win → macOS → Linux", "size": Pt(14), "color": ACCENT_BLUE, "bold": True},
             {"text": "不同Training Stage专注", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "单一设备家族周期性迭代", "size": Pt(13), "color": TEXT_LIGHT},
         ], title_color=ACCENT_BLUE)

add_card(slide, Inches(8.8), Inches(1.2), Inches(4.1), Inches(3.0),
         "方案B: 参数插值 (推荐)", [
             {"text": "来源: UI-TARS-2", "size": Pt(12), "color": TEXT_DIM},
             {"text": "分别训练 Vertical Agents", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "(Browsing/GUI/Game/SDK各一)", "size": Pt(12), "color": TEXT_DIM},
             {"text": "θ_merge = Σ α_k · θ_k", "size": Pt(16), "color": ACCENT_CYAN, "bold": True},
             {"text": "保留各领域峰值性能", "size": Pt(13), "color": GREEN},
         ], title_color=GREEN)

add_card(slide, Inches(0.4), Inches(4.5), Inches(12.4), Inches(2.2),
         "Token-ID Transport: 训练-推理对齐 (Mobile-Agent-v3.5)", [
             {"text": "问题: 环境端返回文本动作, Tokenizer编码可能有多义性, 直接用文本回传算Loss导致Log-prob错位",
              "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "方案: 直接打包回传生成时的Token IDs, 确保训练和推理的绝对一致",
              "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "EvoCUA 也指出: OpenCUA模型和Qwen3-VL的pattern差异大, 需要工程对齐(如RoPE)",
              "size": Pt(13), "color": ACCENT_ORANGE},
         ], title_color=ACCENT_ORANGE)

add_page_number(slide, 19, TOTAL_SLIDES)

# ============================================================
# SLIDE 20: Part 5 Section Header - Infrastructure
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "05", "基础设施与数据生态",
                   "环境体系、开源数据版图与缺口分析")
add_page_number(slide, 20, TOTAL_SLIDES)

# ============================================================
# SLIDE 21: Environment Architecture
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "环境分层体系与 Verifier 架构", "Part 05 — 基础设施")

add_card(slide, Inches(0.4), Inches(1.2), Inches(4.0), Inches(2.5),
         "Layer 1: 数据采集环境", [
             {"text": "50-100 VM 并发", "size": Pt(14), "color": ACCENT_CYAN, "bold": True},
             {"text": "Win11×30 + macOS×10 + Ubuntu×10", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "截图+A11y提取+动作录制/回放", "size": Pt(12), "color": TEXT_LIGHT},
         ], title_color=ACCENT_BLUE)

add_card(slide, Inches(4.7), Inches(1.2), Inches(4.0), Inches(2.5),
         "Layer 2: RL 沙盒", [
             {"text": "2,000-4,000 并发", "size": Pt(14), "color": ACCENT_ORANGE, "bold": True},
             {"text": "Docker/VM快照池, 快速重置<10s", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "DART-GUI: 四模块完全解耦异步", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "Env/Rollout/DataMgr/Trainer", "size": Pt(12), "color": TEXT_DIM},
         ], title_color=ACCENT_ORANGE)

add_card(slide, Inches(9.0), Inches(1.2), Inches(3.8), Inches(2.5),
         "Layer 3: 虚拟渲染环境", [
             {"text": "状态完全可控", "size": Pt(14), "color": GREEN, "bold": True},
             {"text": "Web渲染虚拟桌面应用", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "Verifier天然精确 (MA-v3.5)", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "适用Office/表单/设置类任务", "size": Pt(12), "color": TEXT_DIM},
         ], title_color=GREEN)

add_card(slide, Inches(0.4), Inches(4.0), Inches(6.1), Inches(2.8),
         "A11y 工具链对比", [
             {"text": "Windows: pywinauto + UIA API          成熟度: 高", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "macOS:   macapptree + AX API          成熟度: 中", "size": Pt(13), "color": TEXT_LIGHT},
             {"text": "Linux:   pyatspi2 + AT-SPI             成熟度: 中低", "size": Pt(13), "color": TEXT_LIGHT},
             "",
             {"text": "Mano: A11y Tree + OmniParse混合最稳健", "size": Pt(12), "color": ACCENT_CYAN},
             {"text": "Computer-RL: 纯视觉(移除A11y)也可行", "size": Pt(12), "color": ACCENT_ORANGE},
         ], title_color=ACCENT_PURPLE)

add_card(slide, Inches(6.8), Inches(4.0), Inches(6.0), Inches(2.8),
         "分布式训练架构 (DART-GUI参考)", [
             {"text": "四模块完全解耦异步:", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "  Env Cluster: 并行Docker (K8s)", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "  Rollout Service: vLLM多worker推理", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "  Data Manager: MySQL管理轨迹/调度", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "  Trainer: FSDP (verl) 异步GRPO更新", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "核心: 单条轨迹为最小调度单元, near on-policy", "size": Pt(12), "color": ACCENT_ORANGE},
         ], title_color=ACCENT_CYAN)

add_page_number(slide, 21, TOTAL_SLIDES)

# ============================================================
# SLIDE 22: Open-Source Dataset Landscape
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "开源数据集版图", "Part 05 — 基础设施")

rows = [
    ["类型", "数据集", "规模", "平台"],
    ["Grounding", "OS-ATLAS / GroundCUA / Jedi", "13M+ / 3.56M / 4M", "跨平台"],
    ["Desktop轨迹", "GUI-360° / OpenCUA / ScaleCUA", "1.2M步 / 22K轨迹 / 大规模", "Win / 3OS / 6OS"],
    ["Web轨迹", "Mind2Web / WebLINX / GUIAct", "2K+ / 100K / 127K-1.26M", "Web"],
    ["Mobile轨迹", "AITW / Rico / AMEX / AndroidControl", "715K / 66K / 104K / 15K", "Android"],
    ["GUI QA", "ScreenQA / GUI-Xplore / GUI-World", "86K / 32K / 12K+视频", "Mixed"],
    ["Benchmark", "OSWorld / WAA / ScreenSpot-Pro", "369 / 154+ / 1.59K", "Desktop"],
]
col_w = [Inches(1.8), Inches(4.5), Inches(3.5), Inches(2.3)]
make_table(slide, Inches(0.5), Inches(1.15), Inches(12.1), rows, col_w)

add_card(slide, Inches(0.4), Inches(4.8), Inches(12.5), Inches(2.2),
         "数据缺口分析", [
             {"text": "        Windows    macOS    Linux     Web      Mobile", "size": Pt(12), "color": TEXT_DIM},
             {"text": "感知     充足       中等     稀缺      充足     充足", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "Grounding 充足      中等     稀缺      充足     充足", "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "轨迹     充足       稀缺     稀缺      充足     充足", "size": Pt(12), "color": ACCENT_ORANGE},
             {"text": "端到端   中等       极缺     极缺      中等     充足", "size": Pt(12), "color": RED},
             {"text": "核心缺口: macOS/Linux轨迹、代码级动作、跨应用工作流、失败/自纠正轨迹",
              "size": Pt(12), "color": ACCENT_CYAN, "bold": True},
         ], title_color=RED)

add_page_number(slide, 22, TOTAL_SLIDES)

# ============================================================
# SLIDE 23: Part 6 Section Header - Methodology Summary
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_section_header(slide, "06", "核心方法论总结",
                   "从现有工作中提炼的五大核心洞察")
add_page_number(slide, 23, TOTAL_SLIDES)

# ============================================================
# SLIDE 24: Five Core Insights
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "五大核心方法论洞察", "Part 06 — 总结")

insights = [
    ("1", "数据闭环 > 模型架构",
     "UI-TARS-2 Data Flywheel / Computer-RL Entropulse / Mano闭环\n数据管线的迭代效率决定最终性能", ACCENT_BLUE),
    ("2", "RL 是跃迁关键, 瓶颈在环境+Verifier",
     "所有SOTA均在SFT后做RL; EvoCUA需2K-4K并发环境\nComputer-RL配备~8000个可编程Verifier", ACCENT_CYAN),
    ("3", "Cold-Start 质量 > 数量",
     "Computer-RL 180K步 / EvoCUA 5K轨迹即可启动\n关键: Verifier过滤 + 多Teacher + 分层难度", ACCENT_ORANGE),
    ("4", "Grounding 是基础瓶颈",
     "AgentCPM 12M预训练 / ScreenSpot-Pro SOTA仅18.9%\n桌面元素更密更小, 需Hard Synthesis+负样本", ACCENT_PURPLE),
    ("5", "统一动作空间尚未解决",
     "Mobile/Web/Desktop仍割裂\nComputer-RL的API-GUI Paradigm (Python代码) 是当前最优方案", ACCENT_PINK),
]
for i, (num, title, desc, color) in enumerate(insights):
    y = Inches(1.15) + Inches(i * 1.18)
    add_rounded_rect(slide, Inches(0.4), y, Inches(12.5), Inches(1.05), fill_color=BG_CARD)
    add_shape(slide, Inches(0.4), y, Inches(0.08), Inches(1.05), fill_color=color)

    add_text_box(slide, Inches(0.7), y + Inches(0.05), Inches(0.4), Inches(0.4),
                 num, font_size=Pt(20), color=color, bold=True)
    add_text_box(slide, Inches(1.3), y + Inches(0.05), Inches(4.5), Inches(0.4),
                 title, font_size=Pt(16), color=TEXT_WHITE, bold=True)
    add_text_box(slide, Inches(1.3), y + Inches(0.45), Inches(11.3), Inches(0.55),
                 desc, font_size=Pt(11), color=TEXT_LIGHT)

add_page_number(slide, 24, TOTAL_SLIDES)

# ============================================================
# SLIDE 25: Unified Methodology Roadmap
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_top_bar(slide, "通用技术路线图: 从现有工作提炼", "Part 06 — 总结")

stages = [
    ("Phase 0\n基建", "环境集群 + A11y工具链\nVerifier体系 + 数据格式\n统一动作空间设计", ACCENT_BLUE, Inches(0.3)),
    ("Phase 1\nGrounding", "15-20M样本\nOS-ATLAS+GroundCUA\n+Hard Synthesis\n+30%通用防退化", ACCENT_CYAN, Inches(2.9)),
    ("Phase 2\nSFT", "Cold-start: 100-200K步\n多Teacher+Verifier过滤\n+CoT+ActionDesp\n+25%通用防collapse", ACCENT_PURPLE, Inches(5.5)),
    ("Phase 3\nOnline RL", "Step-GRPO/PPO\n2K-4K并发环境\nRule→LLM→ORM reward\n+Entropulse循环", ACCENT_ORANGE, Inches(8.1)),
    ("Phase 4\n融合", "Offline DPO(关键步骤)\n参数插值/MRPO\n数据飞轮持续运转\nModel Merge", ACCENT_PINK, Inches(10.7)),
]
for title, desc, color, x in stages:
    add_rounded_rect(slide, x, Inches(1.2), Inches(2.3), Inches(3.5), fill_color=BG_CARD)
    add_shape(slide, x, Inches(1.2), Inches(2.3), Inches(0.06), fill_color=color)
    add_multi_text(slide, x + Inches(0.15), Inches(1.45), Inches(2.0), Inches(3.2), [
        {"text": title, "size": Pt(15), "color": color, "bold": True, "spacing": Pt(10)},
        {"text": desc, "size": Pt(11), "color": TEXT_LIGHT},
    ])

for i in range(4):
    x = Inches(2.7) + Inches(2.6) * i
    add_text_box(slide, x, Inches(2.6), Inches(0.3), Inches(0.3),
                 "→", font_size=Pt(20), color=ACCENT_BLUE, bold=True)

add_card(slide, Inches(0.3), Inches(5.0), Inches(12.5), Inches(1.8),
         "贯穿全流程的数据飞轮", [
             {"text": "采集 → 训练(SFT/RL) → Rollout → Verifier验证 → 数据回收 → 质量过滤 → 路由", "size": Pt(13), "color": ACCENT_CYAN},
             {"text": "高质量成功轨迹 → SFT    |  低质量/失败 → CT    |  成功但有错 → LLM修正→SFT    |  成功Rollout → Entropy恢复",
              "size": Pt(12), "color": TEXT_LIGHT},
             {"text": "每个query多轨迹 > 更多query  |  迭代质量 > 一次性堆量  |  通用数据混合25-30%防collapse",
              "size": Pt(12), "color": ACCENT_ORANGE},
         ], title_color=GREEN)

add_page_number(slide, 25, TOTAL_SLIDES)

# ============================================================
# SLIDE 26: Closing
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

add_shape(slide, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.06), fill_color=ACCENT_BLUE)
add_shape(slide, Inches(0), SLIDE_HEIGHT - Inches(0.06), SLIDE_WIDTH, Inches(0.06), fill_color=ACCENT_BLUE)

add_multi_text(slide, Inches(1.5), Inches(1.5), Inches(10), Inches(5), [
    {"text": "Thank You", "size": Pt(52), "color": ACCENT_BLUE, "bold": True, "spacing": Pt(16)},
    {"text": "CUA 技术调研报告", "size": Pt(24), "color": ACCENT_CYAN, "spacing": Pt(30)},
    {"text": "核心结论", "size": Pt(18), "color": TEXT_WHITE, "bold": True, "spacing": Pt(12)},
    {"text": "1. 数据闭环驱动 > 模型架构创新", "size": Pt(15), "color": TEXT_LIGHT, "spacing": Pt(4)},
    {"text": "2. RL 是性能跃迁关键，瓶颈在环境与 Verifier 而非算法", "size": Pt(15), "color": TEXT_LIGHT, "spacing": Pt(4)},
    {"text": "3. Cold-Start 质量优先，Verifier 过滤 + 多 Teacher + 分层难度", "size": Pt(15), "color": TEXT_LIGHT, "spacing": Pt(4)},
    {"text": "4. Grounding 是基础瓶颈，需 Hard Synthesis + 负样本增强", "size": Pt(15), "color": TEXT_LIGHT, "spacing": Pt(4)},
    {"text": "5. API-GUI Paradigm 是统一动作空间的当前最优方案", "size": Pt(15), "color": TEXT_LIGHT, "spacing": Pt(4)},
])

add_shape(slide, Inches(1.5), Inches(6.5), Inches(4), Inches(0.04), fill_color=ACCENT_BLUE)

add_page_number(slide, 26, TOTAL_SLIDES)

# ============================================================
# Save
# ============================================================
output_path = "/workspace/CUA_Research_Report.pptx"
prs.save(output_path)
print(f"PPT saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
