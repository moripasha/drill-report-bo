
# pdf_generator.py
# -*- coding: utf-8 -*-

import os
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# برای فارسیِ چسبیده
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


# =========================
# تنظیمات اصلی
# =========================

GRID_MM = 5.0  # گرید شما: هر خانه 5 میلی‌متر
MM_TO_PT = 72.0 / 25.4  # 1mm -> points

# آفست خیلی مهمه (کالیبراسیون). چون ممکنه عکس/پی‌دی‌اف قالب حاشیه داشته باشه.
# فعلاً این دو تا رو روی صفر گذاشتم؛ اگر 1-2 خانه جابجاست، فقط این دو تا رو تغییر بده.
OFFSET_X_MM = 0.0  # + یعنی نوشته‌ها کمی به چپ می‌روند (چون مبدا راست است)
OFFSET_Y_MM = 0.0  # + یعنی نوشته‌ها کمی پایین می‌آیند

# فونت
FONT_FILE = "Vazirmatn-Regular.ttf"
FONT_NAME = "Vazirmatn"

# قالب پس‌زمینه (بهتر: JPG)
TEMPLATE_IMAGE = "form_template.jpg"

# سایز صفحه (A4 landscape)
PAGE_W, PAGE_H = landscape(A4)

# دیباگ گرید (برای تست)
DEBUG_DRAW_GRID = False


# =========================
# ابزارهای متن
# =========================

def _mm(v: float) -> float:
    return v * MM_TO_PT

def _shape_fa(text: str) -> str:
    """فارسی را چسبیده و درست RTL می‌کند."""
    if text is None:
        return ""
    text = str(text)
    if not text:
        return ""
    if arabic_reshaper is None or get_display is None:
        # اگر پکیج‌ها نصب نبود، حداقل متن را برگردان
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def _num_no_decimal(v):
    """عدد را بدون اعشار چاپ می‌کند."""
    if v is None:
        return ""
    try:
        f = float(str(v).replace(",", "."))
        i = int(round(f))
        return str(i)
    except Exception:
        return str(v)

def grid_xy(col: float, row: float):
    """
    تبدیل مختصات گرید به مختصات PDF.
    مبدا: بالا راست (0,0) در گوشه صفحه
    col به سمت چپ زیاد می‌شود، row به سمت پایین زیاد می‌شود.
    """
    x_mm = (col * GRID_MM) + OFFSET_X_MM
    y_mm = (row * GRID_MM) + OFFSET_Y_MM

    x = PAGE_W - _mm(x_mm)
    y = PAGE_H - _mm(y_mm)
    return x, y

def draw_text(c: canvas.Canvas, col, row, text, font_size=12, bold=False, align="right"):
    """
    align:
      - right: نقطه داده شده، سمت راست متن باشد
      - left:  نقطه داده شده، سمت چپ متن باشد
      - center: وسط
    """
    if text is None:
        return

    s = str(text).strip()
    if not s:
        return

    # فارسی/عربی را شکل بده
    s2 = _shape_fa(s)

    c.setFont(FONT_NAME, font_size)

    x, y = grid_xy(col, row)
    w = c.stringWidth(s2, FONT_NAME, font_size)

    if align == "right":
        c.drawString(x - w, y, s2)
    elif align == "center":
        c.drawString(x - (w / 2.0), y, s2)
    else:  # left
        c.drawString(x, y, s2)

def wrap_text_lines(text: str, max_width_pt: float, font_size: float):
    """متن را بر اساس عرض مجاز line-wrap می‌کند."""
    if not text:
        return []

    t = str(text).replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = t.split("\n")
    out = []

    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            out.append("")
            continue

        # جداکننده‌ی ساده‌ی کلمات
        words = raw.split(" ")
        line = ""
        for w in words:
            cand = (line + " " + w).strip()
            cand_shaped = _shape_fa(cand)
            if pdfmetrics.stringWidth(cand_shaped, FONT_NAME, font_size) <= max_width_pt:
                line = cand
            else:
                if line:
                    out.append(line)
                line = w
        if line:
            out.append(line)

    return out


# =========================
# تولید PDF
# =========================

def generate_pdf(report_data: dict, output_path: str):
    """
    report_data ساختار همان user_data است.
    """
    # فونت را رجیستر کن
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        if not os.path.exists(FONT_FILE):
            raise FileNotFoundError(f"Font file not found: {FONT_FILE}")
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))

    c = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))

    # پس‌زمینه
    if not os.path.exists(TEMPLATE_IMAGE):
        raise FileNotFoundError(f"Template image not found: {TEMPLATE_IMAGE}")

    c.drawImage(TEMPLATE_IMAGE, 0, 0, width=PAGE_W, height=PAGE_H, mask="auto")

    # گرید دیباگ
    if DEBUG_DRAW_GRID:
        c.setLineWidth(0.2)
        step = _mm(GRID_MM)
        # خطوط عمودی
        x = 0
        while x <= PAGE_W:
            c.line(x, 0, x, PAGE_H)
            x += step
        # خطوط افقی
        y = 0
        while y <= PAGE_H:
            c.line(0, y, PAGE_W, y)
            y += step

    # -----------------------
    # هدر (مختصات شما)
    # -----------------------
    # توجه: اینجا فقط مقدار چاپ می‌شود، نه "region:" و غیره
    # مختصات: RGN 5,8  BH 16,8  RIG 31,8  ANG 40,8  DATE 45,8

    region = report_data.get("region", "")
    borehole = report_data.get("borehole", "")
    rig = report_data.get("rig", "")
    ang = report_data.get("angle_deg", "")
    date = report_data.get("date", "")

    draw_text(c, 5, 8, region, font_size=13, align="right")
    draw_text(c, 16, 8, borehole, font_size=13, align="center")  # گمانه معمولاً وسط بهتره
    draw_text(c, 31, 8, rig, font_size=13, align="center")

    # زاویه: فقط عدد + " درجه" و یکم راست‌تر
    ang_txt = ""
    if ang not in (None, ""):
        ang_txt = f"{_num_no_decimal(ang)} درجه"
    # اینجا col رو کمی کمتر می‌کنیم یعنی به راست نزدیک‌تر (چون مبدا راست است)
    draw_text(c, 39.2, 8, ang_txt, font_size=13, align="center")

    # تاریخ: روز/ماه/سال (همون چیزی که خودت گفتی)
    draw_text(c, 45, 8, date, font_size=13, align="center")

    # -----------------------
    # مقادیر شیفت روز (مختصات جدید شما)
    # -----------------------
    # D start 14,11
    # D end   14,12.3
    # D len   14,13.3
    # D size  14,14.3
    # D mud   14,15.3
    # D water 14,15.8
    # D diesel14,17.2

    shifts = report_data.get("shifts", {})
    day = shifts.get("day", {})
    night = shifts.get("night", {})

    # اگر شیفت روز وجود دارد
    if day.get("start") is not None:
        draw_text(c, 14, 11, _num_no_decimal(day.get("start")), font_size=12, align="center")
        draw_text(c, 14, 12.3, _num_no_decimal(day.get("end")), font_size=12, align="center")
        draw_text(c, 14, 13.3, _num_no_decimal(day.get("length")), font_size=12, align="center")
        draw_text(c, 14, 14.3, str(day.get("size") or ""), font_size=12, align="center")

        mud = day.get("mud") or []
        mud_txt = " + ".join(mud) if mud else ""
        # گل‌ها معمولاً طولانی میشن؛ کمی کوچکتر
        draw_text(c, 14, 15.3, mud_txt, font_size=10.5, align="center")

        draw_text(c, 14, 15.8, _num_no_decimal(day.get("water")), font_size=12, align="center")
        draw_text(c, 14, 17.2, _num_no_decimal(day.get("diesel")), font_size=12, align="center")

    # -----------------------
    # توضیحات + پرسنل (باکس شما)
    # باکس: TR 28,11  TL 54,11  BR 28,25  BL 54,25
    # -----------------------
    box_tr = (28, 11)
    box_tl = (54, 11)
    box_br = (28, 25)
    box_bl = (54, 25)

    # عرض و ارتفاع باکس به points
    x_right, y_top = grid_xy(box_tr[0], box_tr[1])
    x_left, _ = grid_xy(box_tl[0], box_tl[1])
    _, y_bottom = grid_xy(box_br[0], box_br[1])

    box_w = abs(x_left - x_right)
    box_h = abs(y_top - y_bottom)

    # پدینگ داخل باکس
    pad = _mm(2)  # 2mm
    usable_w = box_w - 2 * pad

    # اگر شیفت شب هم باشد، باکس را نصف کن
    has_day = bool(day.get("start") is not None)
    has_night = bool(night.get("start") is not None)

    # فونت توضیحات
    notes_font = 11.5
    line_h = notes_font * 1.35

    def draw_notes_block(block_top_y, block_bottom_y, shift_key):
        sh = shifts.get(shift_key, {})
        notes = (sh.get("notes") or "").strip()

        # متن توضیحات
        lines = wrap_text_lines(notes, usable_w, notes_font)

        # شروع نوشتن از بالا به پایین
        cur_y = block_top_y - pad - notes_font
        for ln in lines:
            if cur_y < block_bottom_y + pad + (line_h * 2):
                break
            # داخل باکس از سمت راست، align right
            # برای draw_text ما col/row می‌خواهد؛ اینجا مستقیم drawString می‌زنیم دقیق‌تر:
            s = _shape_fa(ln)
            w = pdfmetrics.stringWidth(s, FONT_NAME, notes_font)
            c.setFont(FONT_NAME, notes_font)
            c.drawString(x_right + pad + (usable_w - w), cur_y, s)
            cur_y -= line_h

        # خط پرسنل (پایین هر باکس)
        sup = "، ".join(sh.get("supervisors") or [])
        helpers = "، ".join(sh.get("helpers") or [])
        bosses = "، ".join(sh.get("workshop_bosses") or [])

        people_line = f"مسئول شیفت: {sup or '-'} / پرسنل کمکی: {helpers or '-'} / سرپرست کارگاه: {bosses or '-'}"
        people_line_s = _shape_fa(people_line)
        c.setFont(FONT_NAME, 10.5)

        # پایینِ باکس
        py = block_bottom_y + pad
        pw = pdfmetrics.stringWidth(people_line_s, FONT_NAME, 10.5)
        if pw > usable_w:
            # اگر خیلی طولانی شد، کوچیک‌تر
            c.setFont(FONT_NAME, 9.5)
            pw = pdfmetrics.stringWidth(people_line_s, FONT_NAME, 9.5)

        c.drawString(x_right + pad + (usable_w - pw), py, people_line_s)

    # محاسبه محدوده باکس
    top_y = max(y_top, y_bottom)
    bottom_y = min(y_top, y_bottom)

    if has_day and has_night:
        mid_y = (top_y + bottom_y) / 2.0
        # روز بالا، شب پایین
        draw_notes_block(top_y, mid_y, "day")
        draw_notes_block(mid_y, bottom_y, "night")
    elif has_day:
        draw_notes_block(top_y, bottom_y, "day")
    elif has_night:
        draw_notes_block(top_y, bottom_y, "night")

    c.showPage()
    c.save()
    return output_path
