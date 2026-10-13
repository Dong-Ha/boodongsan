#!/usr/bin/env python3
"""Build the eight editorial HTML figures and export SVGs with Diagram Design.

Usage:
    python scripts/build_visuals.py --export-helper /path/to/diagram-design/scripts/export_svg.py

Python standard library only. No network calls. All numerical examples are fictional.
The upstream helper is read from the explicit path and invoked for SVG export.
"""
from __future__ import annotations

import argparse
import html
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visuals"
PAPER, INK, MUTED, SOFT, ACCENT = "#f5f5f5", "#2d3142", "#4f5d75", "#5a6580", "#bf4520"
SANS = "'Geist', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', system-ui, sans-serif"
SERIF = "'Instrument Serif', 'Noto Serif', 'Noto Serif KR', serif"
CSS = f"""
* {{ box-sizing: border-box; }}
:root {{ --color-paper:{PAPER}; --color-ink:{INK}; --color-muted:{MUTED}; --color-accent:{ACCENT}; }}
body {{ margin:0; padding:32px 24px; background:{PAPER}; color:{INK}; font-family:{SANS}; line-height:1.7; }}
.frame {{ width:100%; max-width:960px; min-width:0; margin:auto; }}
.eyebrow {{ color:{MUTED}; font-size:12px; margin:0 0 8px; }}
h1 {{ font-family:{SERIF}; font-size:28px; font-weight:400; line-height:1.35; margin:0 0 12px; }}
h2 {{ font-size:20px; margin:0 0 12px; }}
.intro {{ color:{MUTED}; font-size:14px; max-width:820px; margin:0 0 20px; }}
.diagram-container {{ width:100%; overflow-x:auto; }}
svg {{ width:100%; min-width:960px; display:block; }}
a {{ color:#2e5aa8; text-underline-offset:3px; }}
.foot {{ border-top:1px solid #bfc0c0; margin-top:20px; padding-top:12px; font-size:13px; color:{MUTED}; }}
.contents {{ display:flex; flex-wrap:wrap; gap:8px 20px; padding:12px 0 24px; }}
.gallery-section {{ margin:40px 0 56px; break-inside:avoid; }}
.lesson-link {{ font-size:14px; margin-top:12px; }}
@media (max-width:600px) {{ body {{ padding:24px 16px; }} h1 {{ font-size:24px; }} }}
@media print {{ body {{ padding:0; }} .diagram-container {{ overflow-x:visible; }} svg {{ min-width:0; }} .contents {{ display:none; }} .gallery-section {{ break-before:page; margin:0; }} }}
"""


def esc(value):
    return html.escape(str(value), quote=True)


def text(x, y, label, size=12, color=INK, weight=400, anchor="start", serif=False):
    family = SERIF if serif else SANS
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" font-family="{esc(family)}" text-anchor="{anchor}">{esc(label)}</text>')


def rect(x, y, w, h, fill=PAPER, stroke=None, radius=0, **data):
    attrs = f'x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    if stroke:
        attrs += f' stroke="{stroke}" stroke-width="1"'
    if radius:
        attrs += f' rx="{radius}"'
    for key, value in data.items():
        attrs += f' {key.replace("_", "-")}="{esc(value)}"'
    return f'<rect {attrs}/>'


def line(x1, y1, x2, y2, color=MUTED, **extra):
    attrs = " ".join(f'{key.replace("_", "-")}="{esc(value)}"' for key, value in extra.items())
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" {attrs}/>'


def node(x, y, w, h, labels, focal=False, terminal=False):
    color = ACCENT if focal else INK
    fill = "rgba(191,69,32,0.08)" if focal else "#ffffff"
    r = 20 if terminal else 6
    parts = [rect(x, y, w, h, PAPER, radius=r), rect(x, y, w, h, fill, color, r)]
    first = y + h / 2 - 8 * (len(labels) - 1) + 4
    for i, label in enumerate(labels):
        parts.append(text(x + w / 2, first + i * 20, label, weight=600 if i == 0 else 400, anchor="middle"))
    return "".join(parts)


def diamond(cx, cy, w, h, labels, focal=False):
    color = ACCENT if focal else INK
    fill = "rgba(191,69,32,0.08)" if focal else "#ffffff"
    points = f'{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}'
    parts = [f'<polygon points="{points}" fill="{PAPER}"/>',
             f'<polygon points="{points}" fill="{fill}" stroke="{color}" stroke-width="1"/>']
    first = cy - 8 * (len(labels) - 1) + 4
    return "".join(parts + [text(cx, first + i * 20, label, weight=600, anchor="middle") for i, label in enumerate(labels)])


def arrow(x1, y1, x2, y2, accent=False):
    assert x1 == x2 or y1 == y2, "Only orthogonal connectors"
    return line(x1, y1, x2, y2, ACCENT if accent else MUTED,
                marker_end="url(#arrow-accent)" if accent else "url(#arrow)")


def label(x, y, w, value):
    # Caller supplies a 16px mask located 8px away from its connector.
    return rect(x, y, w, 16, PAPER) + text(x + w / 2, y + 12, value, color=SOFT, weight=500, anchor="middle")


def legend(items, note):
    parts = [line(40, 544, 920, 544, "#bfc0c0")]
    x = 40
    for name, fill, stroke in items:
        parts += [rect(x, 556, 12, 12, fill, stroke), text(x + 20, 568, name, color=MUTED)]
        x += 176
    parts.append(text(40, 592, note, color=MUTED))
    return "".join(parts)


def shell(slug, title, desc, body):
    return (f'<svg viewBox="0 0 960 600" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-labelledby="{slug}-title {slug}-desc">'
            f'<title id="{slug}-title">{esc(title)}</title><desc id="{slug}-desc">{esc(desc)}</desc>'
            '<defs>'
            f'<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>'
            f'<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>'
            '<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#2e5aa8"/></marker>'
            '</defs>' + rect(0, 0, 960, 600) + body + '</svg>')


def page(title, eyebrow, intro, svg, lesson):
    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{esc(title)}</title><style>{CSS}</style></head>
<body><main class="frame"><p class="eyebrow">{esc(eyebrow)} · BOODONGSAN</p><h1>{esc(title)}</h1><p class="intro">{esc(intro)}</p>
<div class="diagram-container" tabindex="0" aria-label="가로로 스크롤하여 전체 그림 보기">{svg}</div>
<p class="foot">관련 강의: <a href="../../lessons/{lesson}">{esc(lesson)}</a><br>Diagram Design 방식 · 2026-10-13 · 시스템 글꼴 · 외부 리소스 요청 없음</p></main></body></html>'''


def area():
    parts = [text(40, 68, "공급면적 80㎡ = 전용 59㎡ + 주거공용 21㎡", 14, weight=600),
             text(40, 100, "가상 면적의 포함 관계입니다. 도형 크기는 실제 면적 비율이나 평면도를 뜻하지 않습니다.", color=MUTED),
             rect(80, 160, 560, 280, "rgba(45,49,66,0.025)", MUTED, 8),
             rect(104, 152, 224, 16, PAPER), text(112, 164, "공급면적 / 두 면적의 합", weight=500),
             rect(112, 224, 320, 160, "rgba(191,69,32,0.08)", ACCENT, 8),
             rect(128, 216, 176, 16, PAPER), text(136, 228, "전용면적 / 59㎡", color=ACCENT, weight=500),
             text(272, 292, "우리 세대가 쓰는 공간", 14, weight=600, anchor="middle"),
             text(272, 324, "방·거실·주방 등", color=MUTED, anchor="middle"),
             rect(464, 224, 144, 160, "rgba(45,49,66,0.05)", INK, 8),
             text(536, 264, "주거공용 21㎡", weight=600, anchor="middle"),
             text(536, 296, "계단·복도 등", color=MUTED, anchor="middle"),
             text(536, 328, "함께 쓰는 공간", color=MUTED, anchor="middle"),
             rect(680, 256, 200, 112, "rgba(45,49,66,0.02)", MUTED, 8, stroke_dasharray="4,3"),
             text(780, 292, "서비스면적", 14, weight=600, anchor="middle"),
             text(780, 324, "발코니 등 별도 구분", color=MUTED, anchor="middle"),
             text(80, 492, "비교할 때는 전용면적과 공급면적을 서로 섞지 않습니다.", 14, weight=600)]
    return "".join(parts) + legend([("전용 공간", "rgba(191,69,32,0.08)", ACCENT), ("공급 범위", "rgba(45,49,66,0.025)", MUTED)], "근거: 1강 · 숫자는 학습용 가정 · 광고 평형의 면적 기준을 확인하세요.")


def waterfall(names, values, roles, maximum, unit, topnote, bottomnote, assumption):
    assert len(names) == 4
    base, top, barw = 448, 168, 128
    xs = [112, 304, 496, 688]
    k = (base - top) / float(maximum)
    yy = lambda v: round(base - float(v) * k)
    parts = [text(40, 68, topnote, 14, weight=600), text(40, 100, assumption, color=MUTED), text(80, 132, f"단위: {unit}", color=MUTED)]
    tick_steps = 5 if maximum == Decimal("125") else 4
    for step in range(tick_steps + 1):
        value = maximum * Decimal(step) / tick_steps
        y = yy(value)
        parts += [line(80, y, 880, y, "rgba(45,49,66,0.10)"), text(68, y+4, f"{value:g}", color=MUTED, anchor="end")]
    parts += [line(80, top, 80, base, "#bfc0c0"), line(80, base, 880, base, "#bfc0c0")]
    running = Decimal(values[0])
    for i, (name, value, role) in enumerate(zip(names, values, roles)):
        number = Decimal(value)
        before = running
        after = number if role == "total" else before + number
        if i and role == "delta":
            running = after
        elif role == "total":
            if i:
                assert running == number
            running = number
        low, high = (Decimal(0), number) if role == "total" else (min(before, after), max(before, after))
        y, height = yy(high), yy(low) - yy(high)
        focal = i == 3
        stroke = ACCENT if focal else (INK if role == "total" else MUTED)
        fill = "rgba(191,69,32,0.12)" if focal else ("rgba(45,49,66,0.08)" if role == "total" else (PAPER if number < 0 else "rgba(79,93,117,0.15)"))
        parts += [rect(xs[i], y, barw, height, PAPER),
                  rect(xs[i], y, barw, height, fill, stroke, data_role=role, data_value=value, data_name=name)]
        label_y = yy(low) + 12 if role == "delta" and number < 0 else y - 8
        # The literal value matches data-value exactly; unit is named on the axis.
        parts.append(text(xs[i]+barw/2, label_y, value, color=stroke, weight=500, anchor="middle"))
        parts.append(text(xs[i]+barw/2, 480, name, color=stroke, weight=600, anchor="middle"))
        if i < 3:
            parts.append(line(xs[i]+barw, yy(running), xs[i+1], yy(running), "rgba(45,49,66,0.55)", data_carry=str(running)))
    parts.append(text(80, 520, bottomnote, 14, weight=600))
    return "".join(parts) + legend([("합계", "rgba(45,49,66,0.08)", INK), ("차감", PAPER, MUTED), ("더하는 금액", "rgba(79,93,117,0.15)", MUTED)], "가상 계산 · 월 비용과 초기 현금은 서로 다른 계산입니다.")


def lease():
    parts = [text(40, 60, "대항력과 우선변제권은 갖춰야 할 조건이 있습니다.", 14, weight=600)]
    # Connections and branch masks are painted before nodes.
    parts += [arrow(224, 128, 224, 164), arrow(344, 216, 488, 216), arrow(224, 268, 224, 424),
              arrow(652, 256, 652, 320), arrow(652, 384, 652, 432),
              label(380, 192, 64, "완료"), label(232, 332, 88, "미완료"),
              node(104, 80, 240, 48, ["주택 임대차를 확인"]),
              diamond(224, 216, 240, 104, ["집을 인도받고", "전입신고를 마쳤나요?"]),
              node(104, 424, 240, 64, ["요건부터 확인", "전입신고만으로 끝나지 않음"], terminal=True),
              node(488, 176, 328, 80, ["대항력", "일반적으로 다음 날부터"], focal=True),
              node(488, 320, 328, 64, ["확정일자도 함께 확인", "계약서의 날짜를 공적으로 확인"]),
              node(488, 432, 328, 64, ["대항요건 + 확정일자", "우선변제권의 요건·순위 확인"], terminal=True)]
    return "".join(parts) + legend([("권리의 조건", "#ffffff", INK), ("핵심 시점", "rgba(191,69,32,0.08)", ACCENT)], "4강·공식 법령 참조 · 반환보증은 별도 심사·절차 · 전액 회수를 보장하는 그림이 아닙니다.")


def grouped_bars(values, names, maximum, unit, group_a, group_b, footnote):
    base, top = 448, 168
    k = (base-top)/maximum
    xs = [112, 288, 560, 736]
    parts = [text(280, 88, group_a, 14, weight=600, anchor="middle"),
             text(704, 88, group_b, 14, weight=600, anchor="middle"), text(80, 128, f"단위: {unit}", color=MUTED)]
    for step in range(5):
        v = maximum*step/4
        y = round(base - v*k)
        parts += [line(80, y, 880, y, "rgba(45,49,66,0.10)"), text(68, y+4, f"{v:g}", color=MUTED, anchor="end")]
    parts += [line(80, top, 80, base, "#bfc0c0"), line(80, base, 880, base, "#bfc0c0")]
    for i, (v, name) in enumerate(zip(values, names)):
        h = round(v*k)
        focal = i == max(range(4), key=lambda j: values[j])
        color = ACCENT if focal else MUTED
        fill = "rgba(191,69,32,0.12)" if focal else "rgba(79,93,117,0.15)"
        parts += [rect(xs[i], base-h, 112, h, PAPER), rect(xs[i], base-h, 112, h, fill, color, data_value=v, data_name=name),
                  text(xs[i]+56, base-h-12, f"{v:g}{unit}", color=color, weight=500, anchor="middle"),
                  text(xs[i]+56, 480, name, weight=600, anchor="middle")]
    parts.append(text(80, 520, footnote, 14, weight=600))
    return "".join(parts) + legend([("같은 기준으로 비교", "rgba(79,93,117,0.15)", MUTED), ("비교의 핵심", "rgba(191,69,32,0.12)", ACCENT)], "숫자·집·이동 조건은 학습용 가정입니다. 실제 사례는 조회일과 출처를 함께 기록하세요.")


def subscription():
    parts = [text(40, 68, "가상 분양가 6억원 / 계약금 10% · 중도금 60% · 잔금 30%", 14, weight=600),
             text(40, 104, "납부 시점도 가정입니다. 실제 비율·회차·일정·대출 조건은 공고에서 확인합니다.", color=MUTED),
             line(112, 320, 880, 320, MUTED)]
    x_for = lambda month: 144 + month/24*640
    for month in [0, 6, 12, 18, 24]:
        x = x_for(month)
        parts += [line(x, 312, x, 328, MUTED), text(x+12, 352, f"{month}개월", color=MUTED)]
    # Event spacing represents the declared 0, 6 and 24 month offsets honestly.
    for month, name, amount, yy in [(0, "계약금", "6,000만원", 216), (6, "중도금", "3억6,000만원", 424), (24, "잔금", "1억8,000만원", 216)]:
        x = x_for(month)
        focal = month == 0
        color = ACCENT if focal else INK
        parts += [line(x, 320, x, yy+28 if yy < 320 else yy-28, MUTED),
                  f'<circle cx="{x}" cy="320" r="{6 if focal else 4}" fill="{color}"/>',
                  text(x, yy, name, 14, color, 600, "middle"), text(x, yy+24, amount, color=color, anchor="middle")]
    parts.append(text(40, 512, "중도금 대출이 있어도 잔금 대출과 부대비용은 따로 확인합니다.", 14, weight=600))
    return "".join(parts) + legend([("처음 필요한 계약금", ACCENT, ACCENT), ("이후의 납부 단계", INK, INK)], "가상 일정·금액 · 중도금은 실제로 여러 회차일 수 있음 · 8강의 공고 읽기 실습과 함께 봅니다.")


def decision():
    parts = [text(40, 56, "가격 점수보다 필수 조건과 확인 상태를 먼저 봅니다.", 14, weight=600)]
    parts += [arrow(480, 120, 480, 156), arrow(356, 200, 280, 200), arrow(480, 244, 480, 316),
              arrow(356, 360, 280, 360), arrow(480, 404, 480, 464),
              label(288, 176, 60, "아니오"), label(488, 268, 56, "예"),
              label(288, 336, 60, "아니오"), label(488, 416, 56, "예"),
              node(360, 72, 240, 48, ["후보 집 한 곳"], terminal=True),
              diamond(480, 200, 248, 88, ["필수 조건과", "자금을 충족하나요?"], focal=True),
              node(80, 168, 200, 64, ["보류", "조건 또는 예산 재검토"], terminal=True),
              diamond(480, 360, 248, 88, ["중요한 자료를", "확인했나요?"]),
              node(80, 328, 200, 64, ["추가 확인", "근거 없이 점수 채우지 않기"], terminal=True),
              node(360, 464, 240, 56, ["계속 검토", "다음 확인 단계로 이동"], terminal=True)]
    return "".join(parts) + legend([("조건에 따른 분기", "#ffffff", INK), ("첫 판단", "rgba(191,69,32,0.08)", ACCENT)], "계속 검토는 매수 추천·대출 승인·계약 완료를 뜻하지 않습니다. 10강의 판단문을 작성하세요.")


FIGURES = [
    ("01-area", "전용·공급·서비스면적", "Nested", "공급면적 안에 전용면적과 주거공용면적이 포함되고 서비스면적은 별도로 구분됨을 설명합니다.", "전용 59㎡와 공급 80㎡는 다른 기준의 숫자입니다.", "01-basics.md", area),
    ("02-rent-cost", "전세와 월세의 비용 비교", "Waterfall", "같은 집에 자기자금을 쓰고 연 기회비용 4%를 가정하면 월 비교 비용이 100만원에서 106.7만원으로 바뀌는 계산입니다.", "전세 3억원과 보증금 5,000만원·월세 90만원을 비교합니다. 전액 자기자금, 연 기회비용 4%, 다른 비용은 같다고 가정합니다. 기회비용은 현금 출금액이 아닙니다. 소수점 한 자리로 반올림합니다.", "02-price-and-rent.md", lambda: waterfall(["전세 비용", "보증금 감소 효과", "월세 추가", "월세 비용"], ["100", "-83.3", "+90", "106.7"], ["total", "delta", "delta", "total"], Decimal("125"), "만원/월", "보증금에 묶이는 돈이 줄고, 월세 지출이 더해집니다.", "월세 선택의 비용 = 보증금 기회비용 16.7 + 월세 90 = 106.7", "가상 사례 / 전액 자기자금 / 연 기회비용 4% / 관리비 등 동일 / 소수점 한 자리 반올림")),
    ("03-cash-budget", "집값보다 먼저 자금 계산", "Waterfall", "보유 현금 3억원에서 비상자금 0.3억원을 남기고 가정 대출 3억원을 더하면 조달 자금은 5.7억원이며 총 필요 6.2억원보다 0.5억원 부족합니다.", "현금 3억원, 비상자금 3,000만원, 대출 3억원을 가정합니다. 집값 6억원과 부대비용 2,000만원도 가상값입니다. 대출 승인을 뜻하지 않습니다.", "03-budget-and-loans.md", lambda: waterfall(["보유 현금", "비상자금 제외", "가정 대출", "조달 가능 합계"], ["3", "-0.3", "+3", "5.7"], ["total", "delta", "delta", "total"], Decimal("6"), "억원", "현금 전부를 집에 넣지 않고, 남겨둘 돈부터 뺍니다.", "총 필요 6.2억원 − 조달 가능 5.7억원 = 부족 0.5억원", "가상 집값 6억원 + 부대비용 0.2억원 / 대출 3억원은 승인 한도가 아닙니다.")),
    ("04-lease-rights", "보증금 보호의 조건", "Flowchart", "주택 인도와 전입신고를 갖추면 일반적으로 다음 날 대항력이 생기고 확정일자를 함께 갖추면 우선변제권의 요건과 순위를 확인하는 흐름입니다.", "주택임대차의 일반적인 개념 흐름입니다. 개별 권리 순서, 조세채권, 다른 임차인, 보증 가입·이행 조건은 4강과 공식 원문에서 따로 확인합니다.", "04-documents-and-lease.md", lease),
    ("05-average-trap", "평균가격 상승의 함정", "Bar", "A월에는 소형 4억원 거래 두 건, B월에는 소형 4억원과 대형 8억원 거래가 있어 평균이 4억원에서 6억원으로 높아져도 소형 가격은 변하지 않는 가상 사례입니다.", "거래된 집의 구성만 달라져도 평균가격이 오를 수 있습니다. 단지·면적·층·시점을 맞춘 비교가 필요합니다.", "05-data-and-market.md", lambda: grouped_bars([4, 4, 4, 8], ["소형 1", "소형 2", "소형", "대형"], 8, "억원", "A월 / 평균 4억원", "B월 / 평균 6억원", "평균은 50% 상승했지만, 비교한 소형 거래 가격은 4억원으로 같습니다.")),
    ("06-commute", "역까지 거리보다 전체 이동시간", "Bar", "A는 역까지 5분과 나머지 50분으로 총 55분, B는 역까지 12분과 나머지 30분으로 총 42분인 가상 출퇴근 사례입니다.", "두 집에서 같은 목적지까지 이동한다고 가정합니다. 기타 이동에는 대기·승차·환승·목적지까지 도보가 들어갑니다.", "06-location-and-visit.md", lambda: grouped_bars([5, 50, 12, 30], ["집→역 도보", "기타 이동", "집→역 도보", "기타 이동"], 60, "분", "A집 / 전체 55분", "B집 / 전체 42분", "역에는 A가 가깝지만, 같은 목적지까지는 B가 13분 빠릅니다.")),
    ("07-payment-timeline", "분양 대금은 날짜마다 필요합니다", "Timeline", "가상 6억원 분양의 계약금 6천만원, 중도금 3억6천만원, 잔금 1억8천만원을 가상 0·6·24개월 시점에 표시합니다.", "비율과 시간 모두 학습용 가정입니다. 실제 공고에서 납부 회차·일정·대출 실행·상환·부대비용을 확인하세요.", "08-subscription-and-public-housing.md", subscription),
    ("08-decision", "계속 검토·보류·추가 확인", "Flowchart", "필수 조건과 자금을 충족하지 않으면 보류하고 중요한 자료가 없으면 추가 확인하며 두 조건이 확인되면 계속 검토하는 판단 흐름입니다.", "입지나 가격 점수를 매기기 전에 필수 조건과 자금, 중요한 자료를 확인합니다. 실제 매수 여부를 자동 판정하는 도구가 아닙니다.", "10-capstone.md", decision),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-helper", type=Path, required=True)
    args = parser.parse_args()
    helper = args.export_helper.resolve()
    if not helper.is_file():
        parser.error("export helper does not exist")
    (OUT / "html").mkdir(parents=True, exist_ok=True)
    (OUT / "svg").mkdir(parents=True, exist_ok=True)
    gallery_sections, gallery_links = [], []
    for slug, title, kind, desc, intro, lesson, build in FIGURES:
        svg = shell(slug, title, desc, build())
        source = OUT / "html" / f"{slug}.html"
        target = OUT / "svg" / f"{slug}.svg"
        source.write_text(page(title, kind, intro, svg, lesson), encoding="utf-8")
        subprocess.run([sys.executable, str(helper), str(source), str(target), "--system-fonts"], check=True)
        exported = target.read_text(encoding="utf-8")
        # XML declaration is valid in the standalone export, not inside an HTML page.
        if exported.startswith("<?xml"):
            exported = exported.split("?>", 1)[1]
        gallery_links.append(f'<a href="#{slug}">{esc(title)}</a>')
        gallery_sections.append(f'<section class="gallery-section" id="{slug}"><h2>{esc(title)}</h2><p class="intro">{esc(intro)}</p><div class="diagram-container" tabindex="0" aria-label="가로로 스크롤하여 전체 그림 보기">{exported}</div><p class="lesson-link"><a href="../lessons/{lesson}">관련 강의 읽기</a> · <a href="html/{slug}.html">그림 하나만 보기</a></p></section>')
    gallery = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>처음 배우는 부동산 — 그림 8개</title><style>{CSS}</style></head><body><main class="frame"><p class="eyebrow">VISUAL NOTES · BOODONGSAN</p><h1>처음 배우는 부동산, 그림으로 이해하기</h1><p class="intro">각 그림은 한 가지 개념을 설명합니다. 금액·면적·이동시간·납부 일정은 가상 예제이며, 관련 강의에서 실습과 공식 출처를 함께 읽을 수 있습니다.</p><nav class="contents" aria-label="그림 목차">{' '.join(gallery_links)}</nav>{''.join(gallery_sections)}<footer class="foot">Diagram Design 방식 · 기본 밝은 색상 · 시스템 글꼴 · 외부 리소스 요청 없음<br>교재: <a href="../README.md">Dong-Ha/boodongsan</a> · 제작 방식과 출처는 visuals/README.md와 DESIGN.md 참조</footer></main></body></html>'''
    (OUT / "index.html").write_text(gallery, encoding="utf-8")
    print(f"Built {len(FIGURES)} HTML figures, {len(FIGURES)} SVG figures, and a self-contained gallery.")


if __name__ == "__main__":
    main()
