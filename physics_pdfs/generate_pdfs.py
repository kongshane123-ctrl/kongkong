#!/usr/bin/env python3
"""Generate student and teacher PDFs for Lorentz-force demonstrator problem."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (
    Arc,
    Circle,
    FancyArrowPatch,
    FancyBboxPatch,
    Rectangle,
    Wedge,
)
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

OUT = Path("/workspace/physics_pdfs")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

CN_FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
pdfmetrics.registerFont(TTFont("CN", CN_FONT, subfontIndex=0))

plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "DejaVu Sans"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "dejavusans"

# Geometry (m)
R = 0.20
H = 0.16
RHO = (R**2 - H**2) / (2 * H)  # 0.045
CY = -(H + RHO)


def impact_point():
    oc = H + RHO
    qy = -(R**2) / oc
    qx = -math.sqrt(max(R**2 - qy**2, 0.0))
    return qx, qy


def draw_apparatus(ax, *, teacher: bool = False):
    ax.set_aspect("equal")
    ax.set_xlim(-0.40, 0.42)
    ax.set_ylim(-0.44, 0.38)
    ax.axis("off")

    # Interior fill
    ax.add_patch(Circle((0, 0), R, facecolor="#f8fbff", edgecolor="none", zorder=0))

    # ---- Exciting coil (annulus) ----
    coil_outer, coil_inner = 0.305, 0.248
    ax.add_patch(
        Wedge(
            (0, 0),
            coil_outer,
            0,
            360,
            width=coil_outer - coil_inner,
            facecolor="#e8edf4",
            edgecolor="#3d4a5c",
            linewidth=1.8,
            zorder=1,
        )
    )
    # winding section dots
    r_mid = 0.5 * (coil_outer + coil_inner)
    for i in range(28):
        ang = 2 * math.pi * i / 28
        x, y = r_mid * math.cos(ang), r_mid * math.sin(ang)
        ax.plot(x, y, "o", ms=2.0, color="#5a6a7a", zorder=2, markeredgewidth=0)

    ax.annotate(
        "励磁线圈",
        xy=(r_mid * math.cos(0.55), r_mid * math.sin(0.55)),
        xytext=(0.33, 0.20),
        fontsize=11,
        color="#3d4a5c",
        arrowprops=dict(arrowstyle="-", color="#8a97a8", lw=0.9),
        ha="left",
        va="bottom",
    )

    # ---- Glass bulb ----
    ax.add_patch(
        Circle((0, 0), R, facecolor="none", edgecolor="#1d4f91", linewidth=2.2, zorder=3)
    )
    ax.add_patch(
        Circle(
            (0, 0),
            R - 0.005,
            facecolor="none",
            edgecolor="#8eb6e0",
            linewidth=0.7,
            linestyle=(0, (1.2, 1.2)),
            zorder=3,
        )
    )
    ax.annotate(
        "玻璃泡",
        xy=(R * math.cos(0.95), R * math.sin(0.95)),
        xytext=(0.255, 0.295),
        fontsize=11,
        color="#1d4f91",
        arrowprops=dict(arrowstyle="-", color="#6aa3d8", lw=0.9),
        ha="left",
    )

    # Crosshairs
    ax.plot([-R * 1.05, R * 1.05], [0, 0], color="#b7c0cc", lw=0.7, ls=(0, (3, 2)), zorder=2)
    ax.plot([0, 0], [-R * 1.05, R * 1.05], color="#b7c0cc", lw=0.7, ls=(0, (3, 2)), zorder=2)

    # Center O
    ax.plot(0, 0, "o", color="#111827", ms=5, zorder=8)
    ax.text(0.022, 0.018, r"$O$", fontsize=14, color="#111827", zorder=8)

    # Radius R (upper-right)
    ang_r = math.radians(32)
    ax.annotate(
        "",
        xy=(R * math.cos(ang_r), R * math.sin(ang_r)),
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="-|>", color="#1d4f91", lw=1.15, mutation_scale=11),
        zorder=4,
    )
    ax.text(
        0.55 * R * math.cos(ang_r) + 0.012,
        0.55 * R * math.sin(ang_r) + 0.012,
        r"$R$",
        fontsize=13,
        color="#1d4f91",
    )

    # Point P
    ax.plot(0, -H, "o", color="#b91c1c", ms=5.5, zorder=9)
    ax.text(-0.028, -H + 0.012, r"$P$", fontsize=14, color="#b91c1c", ha="right", va="bottom", zorder=9)

    # OP = h (left side)
    ax.annotate(
        "",
        xy=(-0.095, 0),
        xytext=(-0.095, -H),
        arrowprops=dict(arrowstyle="<->", color="#64748b", lw=1.0),
        zorder=4,
    )
    ax.text(-0.115, -H / 2, r"$h$", fontsize=13, color="#475569", ha="right", va="center")

    # Particle gun
    gun_w, gun_h = 0.078, 0.024
    gun = FancyBboxPatch(
        (-gun_w / 2, -H - 0.036),
        gun_w,
        gun_h,
        boxstyle="round,pad=0.001,rounding_size=0.003",
        facecolor="#1f2937",
        edgecolor="#0f172a",
        linewidth=0.9,
        zorder=7,
    )
    ax.add_patch(gun)
    # nozzle hint
    ax.add_patch(
        Rectangle((-0.01, -H - 0.012), 0.02, 0.008, facecolor="#374151", edgecolor="none", zorder=7)
    )
    ax.text(0, -H - 0.058, "粒子枪", fontsize=9.5, ha="center", color="#4b5563")

    # Emission velocity (left)
    ax.annotate(
        "",
        xy=(-0.105, -H),
        xytext=(-0.012, -H),
        arrowprops=dict(arrowstyle="-|>", color="#b91c1c", lw=2.0, mutation_scale=13),
        zorder=10,
    )
    ax.text(-0.112, -H + 0.022, r"$v$", fontsize=12, color="#b91c1c", ha="right")

    if teacher:
        qx, qy = impact_point()

        # Uniform B into page (inside bulb only)
        rng = np.linspace(-0.11, 0.11, 3)
        for xx in rng:
            for yy in rng:
                if xx**2 + yy**2 < (R * 0.72) ** 2 and not (abs(xx) < 0.03 and yy < -0.05):
                    s = 0.011
                    ax.plot([xx - s, xx + s], [yy - s, yy + s], color="#7c3aed", lw=1.15, zorder=4)
                    ax.plot([xx - s, xx + s], [yy + s, yy - s], color="#7c3aed", lw=1.15, zorder=4)
        ax.text(0.125, 0.125, r"$B$（向里）", fontsize=10.5, color="#6d28d9")

        # Orbit center C
        ax.plot(0, CY, "o", color="#166534", ms=5, zorder=8)
        ax.text(0.02, CY - 0.01, r"$C$", fontsize=13, color="#166534", va="top")

        # Full orbit (construction)
        ax.add_patch(
            Circle(
                (0, CY),
                RHO,
                facecolor="none",
                edgecolor="#86efac",
                lw=1.15,
                ls=(0, (4, 2)),
                zorder=4,
            )
        )

        # Physical trajectory P → Q (clockwise arc)
        ang_p = 90.0
        ang_q = math.degrees(math.atan2(qy - CY, qx - 0.0))
        ax.add_patch(
            Arc(
                (0, CY),
                2 * RHO,
                2 * RHO,
                angle=0,
                theta1=ang_q,
                theta2=ang_p,
                color="#dc2626",
                lw=2.4,
                zorder=6,
            )
        )

        # Construction lines
        ax.plot([0, qx], [0, qy], color="#ea580c", lw=1.15, ls=(0, (2, 1.5)), zorder=5)
        ax.plot([0, qx], [CY, qy], color="#166534", lw=1.15, ls=(0, (2, 1.5)), zorder=5)

        # Impact Q
        ax.plot(qx, qy, "o", color="#c2410c", ms=5.5, zorder=9)
        ax.text(qx - 0.02, qy - 0.02, r"$Q$", fontsize=13, color="#c2410c", ha="right", va="top")

        # Right-angle mark at Q (CQ ⟂ OQ)
        u1 = np.array([-qx, -qy])
        u1 /= np.linalg.norm(u1)
        u2 = np.array([-qx, CY - qy])
        u2 /= np.linalg.norm(u2)
        d = 0.016
        p0 = np.array([qx, qy])
        p1 = p0 + d * u1
        p2 = p1 + d * u2
        p3 = p0 + d * u2
        ax.plot(
            [p0[0], p1[0], p2[0], p3[0], p0[0]],
            [p0[1], p1[1], p2[1], p3[1], p0[1]],
            color="#c2410c",
            lw=1.0,
            zorder=7,
        )

        # Velocity at Q (radial outward)
        ax.annotate(
            "",
            xy=(qx * 1.18, qy * 1.18),
            xytext=(qx, qy),
            arrowprops=dict(arrowstyle="-|>", color="#c2410c", lw=1.6, mutation_scale=11),
            zorder=9,
        )

        # rho dimension (right of CP)
        ax.annotate(
            "",
            xy=(0.035, CY),
            xytext=(0.035, -H),
            arrowprops=dict(arrowstyle="<->", color="#166534", lw=0.95),
        )
        ax.text(0.05, (CY - H) / 2, r"$\rho$", fontsize=13, color="#166534", va="center")

        # Clockwise current hint on coil
        theta = np.linspace(0.15, 1.35, 40)
        rr = coil_outer + 0.018
        ax.plot(rr * np.cos(theta), rr * np.sin(theta), color="#334155", lw=1.0, zorder=3)
        ax.annotate(
            "",
            xy=(rr * np.cos(0.15), rr * np.sin(0.15)),
            xytext=(rr * np.cos(0.28), rr * np.sin(0.28)),
            arrowprops=dict(arrowstyle="-|>", color="#334155", lw=1.0, mutation_scale=9),
            zorder=3,
        )
        ax.text(0.34, -0.02, "I 顺时针", fontsize=9.5, color="#334155")

        ax.text(
            0.0,
            -0.405,
            "电流顺时针　·　粒子顺时针偏转　·　于 Q 垂直击中球面（CQ⊥OQ）",
            fontsize=9,
            ha="center",
            color="#64748b",
        )
    else:
        ax.text(
            0.0,
            -0.405,
            "粒子从 P 水平向左进入匀强磁场（装置示意图）",
            fontsize=9.5,
            ha="center",
            color="#64748b",
        )

    return ax


def save_figures():
    fig, ax = plt.subplots(figsize=(5.7, 5.5), dpi=240)
    fig.patch.set_facecolor("white")
    draw_apparatus(ax, teacher=False)
    fig.tight_layout(pad=0.15)
    student_fig = OUT / "fig_student.png"
    fig.savefig(student_fig, dpi=240, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.9, 5.7), dpi=240)
    fig.patch.set_facecolor("white")
    draw_apparatus(ax, teacher=True)
    fig.tight_layout(pad=0.15)
    teacher_fig = OUT / "fig_teacher.png"
    fig.savefig(teacher_fig, dpi=240, bbox_inches="tight", facecolor="white", pad_inches=0.08)
    plt.close(fig)
    return student_fig, teacher_fig


def styles():
    return {
        "title": ParagraphStyle(
            "title",
            fontName="CN",
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            textColor=HexColor("#0f172a"),
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="CN",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=HexColor("#64748b"),
            spaceAfter=8,
        ),
        "h": ParagraphStyle(
            "h",
            fontName="CN",
            fontSize=12,
            leading=18,
            textColor=HexColor("#1d4f91"),
            spaceBefore=7,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="CN",
            fontSize=10.5,
            leading=17.5,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#0f172a"),
            spaceAfter=4,
        ),
        "q": ParagraphStyle(
            "q",
            fontName="CN",
            fontSize=10.5,
            leading=17.5,
            textColor=HexColor("#0f172a"),
            leftIndent=6,
            spaceAfter=3,
        ),
        "ans": ParagraphStyle(
            "ans",
            fontName="CN",
            fontSize=10.5,
            leading=17,
            textColor=HexColor("#166534"),
            leftIndent=6,
            spaceAfter=3,
        ),
        "step": ParagraphStyle(
            "step",
            fontName="CN",
            fontSize=10.5,
            leading=17,
            textColor=HexColor("#0f172a"),
            spaceBefore=4,
            spaceAfter=2,
        ),
        "formula": ParagraphStyle(
            "formula",
            fontName="CN",
            fontSize=11,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor("#0f172a"),
            spaceBefore=2,
            spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor("#94a3b8"),
        ),
        "blank": ParagraphStyle(
            "blank",
            fontName="CN",
            fontSize=10.5,
            leading=20,
            textColor=HexColor("#334155"),
            leftIndent=6,
        ),
        "box": ParagraphStyle(
            "box",
            fontName="CN",
            fontSize=11.5,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor("#14532d"),
            spaceBefore=2,
            spaceAfter=4,
            backColor=HexColor("#f0fdf4"),
            borderPadding=6,
        ),
        "data": ParagraphStyle(
            "data",
            fontName="CN",
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            textColor=HexColor("#334155"),
            leftIndent=6,
            spaceAfter=2,
        ),
    }


PROBLEM = [
    "如图为类似洛伦兹力演示仪的简化模型。圆形励磁线圈中通有电流 I，可在半径 R = 0.20 m 的球形玻璃泡内产生方向垂直于线圈平面的匀强磁场；磁感应强度 B 的大小与电流 I 成正比。改变 I 的大小和方向，即可控制 B 的大小和方向。",
    "在玻璃泡中心 O 的正下方 P 处固定一粒子枪，可发射比荷 q/m = 1.0×10⁴ C/kg 的带正电粒子束；O、P 间距 h = 0.16 m。粒子加速前初速度视为零，经电压 U 加速后（加速距离很短），从 P 点沿水平向左垂直射入磁场。",
    "当加速电压 U = 2.0 V 时，发现粒子恰好垂直打在玻璃泡上。（忽略粒子间相互作用、重力，且不考虑击中后的反弹。）",
]

QUESTIONS = [
    "（1）试判断此时励磁线圈中电流的方向（顺时针 / 逆时针）。",
    "（2）求此时匀强磁感应强度 B 的大小。",
]

GIVEN = (
    "已知量：R = 0.20 m，h = 0.16 m，q/m = 1.0×10⁴ C/kg，U = 2.0 V；粒子带正电，从 P 水平向左入射。"
)


def header_bar(story, st, title, badge):
    story.append(Paragraph(title, st["title"]))
    story.append(Paragraph(badge, st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.3, color=HexColor("#1d4f91"), spaceAfter=6))


def add_problem(story, st, fig_path, fig_caption, fig_width_cm=10.2):
    story.append(Paragraph("一、题目", st["h"]))
    for p in PROBLEM:
        story.append(Paragraph(p, st["body"]))
    story.append(Paragraph(GIVEN, st["data"]))
    story.append(Paragraph("二、装置示意图", st["h"]))
    # keep aspect ~1:0.96 from source figures
    fig_h = fig_width_cm * 0.96
    img = Image(str(fig_path), width=fig_width_cm * cm, height=fig_h * cm)
    img.hAlign = "CENTER"
    story.append(img)
    story.append(Paragraph(fig_caption, st["footer"]))
    story.append(Paragraph("三、求解", st["h"]))
    for q in QUESTIONS:
        story.append(Paragraph(q, st["q"]))


def build_student(fig_path: Path):
    path = OUT / "洛伦兹力演示仪_学生版.pdf"
    art = ART / "洛伦兹力演示仪_学生版.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm,
        title="洛伦兹力演示仪模型 · 学生版",
    )
    st = styles()
    story = []
    header_bar(story, st, "第 14 题　洛伦兹力演示仪模型", "学生版　·　满分 8 分　·　请独立完成")
    add_problem(
        story,
        st,
        fig_path,
        "图 1　洛伦兹力演示仪简化模型（学生用图）",
        fig_width_cm=9.6,
    )
    story.append(PageBreak())
    header_bar(story, st, "第 14 题　答题纸", "学生版　·　请将答案与过程写在本页")
    story.append(Paragraph("四、答题区", st["h"]))
    story.append(Paragraph("（1）电流方向：____________________", st["blank"]))
    story.append(Paragraph("（2）B = ____________________ T", st["blank"]))
    story.append(Paragraph("解题过程", st["h"]))
    for _ in range(18):
        story.append(
            HRFlowable(width="100%", thickness=0.45, color=HexColor("#e2e8f0"), spaceBefore=14)
        )
    doc.build(story)
    art.write_bytes(path.read_bytes())
    return path, art


def build_teacher(fig_path: Path):
    path = OUT / "洛伦兹力演示仪_教师版.pdf"
    art = ART / "洛伦兹力演示仪_教师版.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
        title="洛伦兹力演示仪模型 · 教师版",
    )
    st = styles()
    story = []
    header_bar(
        story,
        st,
        "第 14 题　洛伦兹力演示仪模型",
        "教师版　·　含标准答案、图示解析与评分参考　·　满分 8 分",
    )
    add_problem(
        story,
        st,
        fig_path,
        "图 1　装置与轨迹解析图（紫色 × 表示 B 向里；红弧为粒子轨迹；Q 处直角表示 CQ⊥OQ）",
        fig_width_cm=9.4,
    )

    story.append(PageBreak())
    header_bar(
        story,
        st,
        "第 14 题　参考答案与解析",
        "教师版　·　请勿发给学生",
    )
    story.append(Paragraph("四、参考答案", st["h"]))
    story.append(Paragraph("【最终答案】（1）顺时针；（2）B = 4/9 T（约 0.444 T）", st["box"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor("#bbf7d0"), spaceAfter=4))

    story.append(Paragraph("五、详细解析", st["h"]))

    story.append(Paragraph("<b>步骤 1　判断磁场方向与电流方向（2 分）</b>", st["step"]))
    story.append(
        Paragraph(
            "正粒子从 P 水平向左入射。为满足“垂直打在球面”的几何条件，圆周运动圆心 C 须在 P 正下方，"
            "故入射瞬间洛伦兹力指向下方。由左手定则：四指指向速度（向左），拇指向下，则磁场垂直纸面向里。"
            "线圈中产生向里磁场的电流方向为顺时针。",
            st["body"],
        )
    )
    story.append(Paragraph("结论：（1）电流方向为顺时针。", st["ans"]))

    story.append(Paragraph("<b>步骤 2　由几何条件求轨道半径 ρ（3 分）</b>", st["step"]))
    story.append(
        Paragraph(
            "“垂直打在玻璃泡上”：击中点 Q 处速度沿球面法向（沿 OQ）。粒子做匀速圆周运动，速度又垂直于轨道半径 CQ，故 CQ ⊥ OQ，从而",
            st["body"],
        )
    )
    story.append(Paragraph("OC² = R² + ρ²", st["formula"]))
    story.append(
        Paragraph(
            "又 C 在 P 正下方，CP = ρ，OP = h，故 OC = h + ρ。代入得",
            st["body"],
        )
    )
    story.append(Paragraph("(h + ρ)² = R² + ρ²　⇒　ρ = (R² − h²)/(2h)", st["formula"]))
    story.append(
        Paragraph(
            "代入 R = 0.20 m，h = 0.16 m：ρ = (0.040 − 0.0256)/0.32 = 0.045 m",
            st["formula"],
        )
    )

    story.append(Paragraph("<b>步骤 3　由加速电压求入射速率（1 分）</b>", st["step"]))
    story.append(Paragraph("动能定理：qU = ½mv²", st["formula"]))
    story.append(
        Paragraph(
            "v = √(2U·q/m) = √(2×2×1.0×10⁴) = 200 m/s",
            st["formula"],
        )
    )

    story.append(Paragraph("<b>步骤 4　求磁感应强度 B（2 分）</b>", st["step"]))
    story.append(Paragraph("洛伦兹力提供向心力：ρ = mv/(qB)", st["formula"]))
    story.append(
        Paragraph(
            "B = v/[(q/m)ρ] = 200/(1.0×10⁴×0.045) = 200/450 = 4/9 T",
            st["formula"],
        )
    )
    story.append(Paragraph("结论：（2）B = 4/9 T。", st["ans"]))

    story.append(Paragraph("六、评分参考（建议）", st["h"]))
    story.append(
        Paragraph(
            "（1）电流方向正确得 2 分；仅写对 B 向里或定则分析正确可酌情给 1 分。<br/>"
            "（2）正确写出几何关系 ρ = (R²−h²)/(2h)（或等价推导）得 3 分；"
            "算出 ρ = 0.045 m 得 1 分；动能定理求出 v = 200 m/s 得 1 分；"
            "正确得到 B = 4/9 T 得 1 分。数值计算小错但思路正确可酌情扣分。",
            st["body"],
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "教学提示：本题关键是把“垂直打在玻璃泡上”翻译成 CQ⊥OQ，从而把电磁问题转化为圆的几何问题。",
            st["footer"],
        )
    )
    doc.build(story)
    art.write_bytes(path.read_bytes())
    return path, art


def pdf_preview(pdf_path: Path, out_prefix: str):
    import fitz

    doc = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
        p = OUT / f"{out_prefix}_p{i+1}.png"
        pix.save(str(p))
        paths.append(p)
        (ART / p.name).write_bytes(p.read_bytes())
    return paths


def main():
    student_fig, teacher_fig = save_figures()
    (ART / "fig_student.png").write_bytes(student_fig.read_bytes())
    (ART / "fig_teacher.png").write_bytes(teacher_fig.read_bytes())

    s_pdf, _ = build_student(student_fig)
    t_pdf, _ = build_teacher(teacher_fig)

    sp = pdf_preview(s_pdf, "preview_student")
    tp = pdf_preview(t_pdf, "preview_teacher")

    print("OK")
    print("student_fig", student_fig)
    print("teacher_fig", teacher_fig)
    print("student_pdf", s_pdf)
    print("teacher_pdf", t_pdf)
    print("previews", sp + tp)


if __name__ == "__main__":
    main()
