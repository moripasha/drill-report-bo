from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import arabic_reshaper
from bidi.algorithm import get_display
import re


# ----------------------------------
# فونت فارسی (فایل Vazirmatn-Regular.ttf در ریشه ریپو)
# ----------------------------------

pdfmetrics.registerFont(
    TTFont("VazirFA", "Vazirmatn-Regular.ttf")
)

FONT_FA = "VazirFA"      # برای متن‌های فارسی / ترکیبی
FONT_EN = "Helvetica"    # برای متن‌های لاتین/عدد


# ----------------------------------
# ابزارهای کمکی
# ----------------------------------

def rtl_text(text: str) -> str:
    """متن فارسی را reshape + bidi می‌کند (چسبیده و راست‌به‌چپ)."""
    if not text:
        return ""
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    bidi = get_display(reshaped)
    return bidi


def _txt(v):
    if v is None:
        return ""
    return str(v)


def pick(report_data, *names):
    """اولین کلید موجود در report_data از بین names را برمی‌گرداند."""
    for n in names:
        if n in report_data and report_data[n] not in (None, ""):
            return report_data[n]
    return ""


# ----------------------------------
# گرید مفهومی روی A4 افقی
# ----------------------------------

GRID_COLS = 50
GRID_ROWS = 60


def grid_to_xy(col, row, width, height, margin_x=0, margin_y=0):
    """
    col, row : شماره ستون از راست و ردیف از بالا (می‌تواند float هم باشد)
    خروجی : مختصات x, y روی PDF (مرکز آن خانه)
    """

    # جلوگیری از این‌که col/row از محدوده خارج بشن
    if col < 0:
        col = 0
    if row < 0:
        row = 0
    if col > GRID_COLS - 1:
        col = GRID_COLS - 1
    if row > GRID_ROWS - 1:
        row = GRID_ROWS - 1

    usable_w = width - 2 * margin_x
    usable_h = height - 2 * margin_y

    cell_w = usable_w / GRID_COLS
    cell_h = usable_h / GRID_ROWS

    # ستون‌ها از راست به چپ
    x = width - margin_x - (col + 0.5) * cell_w
    # ردیف‌ها از بالا به پایین
    y = height - margin_y - (row + 0.5) * cell_h

    return x, y


# ----------------------------------
# موقعیت فیلدهای هدر
# ----------------------------------

HEADER_POSITIONS = {
    # منطقه – فارسی → راست‌چین و RTL
    "region": {
        "col": 5,
        "row": 8,
        "align": "right",
        "font": FONT_FA,
        "size": 11,
        "rtl": True,
    },
    # شماره گمانه – لاتین → چپ‌چین
    "borehole": {
        "col": 16,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 11,
        "rtl": False,
    },
    # دستگاه حفاری – لاتین
    "rig": {
        "col": 31,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 11,
        "rtl": False,
    },
    # زاویه – فارسی با «درجه» → راست‌چین و RTL
    # کمی آورده شده سمت راست که از کادر «مورخ» خارج بشود
    "angle": {
        "col": 37,  # قبلاً 40 بود، حالا می‌آریم سمت راست‌تر
        "row": 8,
        "align": "right",
        "font": FONT_FA,
        "size": 11,
        "rtl": True,
    },
    # تاریخ – روز/ماه/سال → چپ‌چین، LTR
    "date": {
        "col": 45,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 11,
        "rtl": False,
    },
}


# ----------------------------------
# موقعیت مقادیر شیفت روز (DAY_*)
# (مقادیر رو تو ستون «شیفت روز» چاپ می‌کنیم؛ همه راست‌چین RTL)
# ----------------------------------

DAY_POSITIONS = {
    "day_start": {
        "col": 14,
        "row": 11,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": " متر",
    },
    "day_end": {
        "col": 14,
        "row": 12.3,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": " متر",
    },
    "day_len": {
        "col": 14,
        "row": 13.3,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": " متر",
    },
    "day_size": {
        "col": 14,
        "row": 14.3,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": "",  # BQ / NQ / HQ / PQ
    },
    "day_mud": {
        "col": 14,
        "row": 15.3,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": "",  # ترکیب سوپرمیکس+...
    },
    "day_water": {
        "col": 14,
        "row": 15.8,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": " لیتر",
    },
    "day_diesel": {
        "col": 14,
        "row": 17.2,
        "align": "right",
        "font": FONT_FA,
        "size": 10,
        "rtl": True,
        "unit": " لیتر",
    },
}


# ----------------------------------
# محدودهٔ کادر توضیحات (کل فرم)
# بالا راست: 28,11 - بالا چپ: 54,11 - پایین راست: 28,25 - پایین چپ: 54,25
# ----------------------------------

DESC_BOX = {
    "top_right": (28, 11),
    "top_left": (54, 11),
    "bottom_right": (28, 25),
    "bottom_left": (54, 25),
    "font": FONT_FA,
    "size": 10,
    "leading": 12,  # فاصله بین خطوط
}


# ----------------------------------
# رندر پاراگراف RTL داخل یک باکس
# ----------------------------------

def draw_rtl_paragraph(c, text, x_right, y_top, width, font_name, font_size, leading):
    """
    متن فارسی را با word-wrap داخل مستطیل از بالا به پایین رسم می‌کند.
    x_right, y_top : گوشهٔ بالا-راست
    width : عرض باکس
    """
    if not text:
        return

    words = text.split()
    lines = []
    current = ""

    for w in words:
        tentative = (current + " " + w).strip()
        display_line = rtl_text(tentative)
        line_width = pdfmetrics.stringWidth(display_line, font_name, font_size)

        if line_width <= width or not current:
            current = tentative
        else:
            lines.append(current)
            current = w

    if current:
        lines.append(current)

    c.setFont(font_name, font_size)

    for i, line in enumerate(lines):
        display_line = rtl_text(line)
        y = y_top - i * leading
        c.drawRightString(x_right, y, display_line)


# ----------------------------------
# تولید PDF
# ----------------------------------

def generate_pdf(report_data: dict) -> bytes:
    """
    فعلاً:
      - هدر (منطقه، گمانه، دستگاه، زاویه، تاریخ)
      - مقادیر شیفت روز (متراژها، سایز، گل، آب، گازوئیل)
      - توضیحات (روز/شب) داخل یک کادر بزرگ
    """
    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # -------------------------
    # پس‌زمینه: تصویر فرم اصلی
    # -------------------------
    bg = ImageReader("form_template.jpg")
    c.drawImage(bg, 0, 0, width=width, height=height)

    # -------------------------
    # هدر: مقادیر خام
    # -------------------------
    region_raw = _txt(report_data.get("region"))
    borehole_raw = _txt(report_data.get("borehole"))
    rig_raw = _txt(report_data.get("rig"))

    # زاویه: فقط عدد + «درجه»
    angle_raw = report_data.get("angle_deg")
    if angle_raw is None:
        angle_raw = report_data.get("angle")
    angle_display = ""
    if angle_raw not in (None, ""):
        s = _txt(angle_raw)
        m = re.search(r"(\d+)", s)
        if m:
            angle_display = f"{m.group(1)} درجه"

    # تاریخ: اگر ورودی سال/ماه/روز بود → روز/ماه/سال
    date_raw = _txt(report_data.get("date"))
    date_display = date_raw
    if date_raw and "/" in date_raw:
        parts = date_raw.split("/")
        if len(parts) == 3 and len(parts[0]) == 4:
            y, mth, d = parts
            date_display = f"{d}/{mth}/{y}"

    header_values = {
        "region": region_raw,
        "borehole": borehole_raw,
        "rig": rig_raw,
        "angle": angle_display,
        "date": date_display,
    }

    # -------------------------
    # رسم فیلدهای هدر
    # -------------------------
    for key, cfg in HEADER_POSITIONS.items():
        raw_text = header_values.get(key, "")
        if not raw_text:
            continue

        col = cfg["col"]
        row = cfg["row"]
        align = cfg.get("align", "left")
        font_name = cfg.get("font", FONT_EN)
        font_size = cfg.get("size", 11)
        is_rtl = cfg.get("rtl", False)

        x, y = grid_to_xy(col, row, width, height)

        if is_rtl:
            text = rtl_text(raw_text)
        else:
            text = raw_text

        c.setFont(font_name, font_size)

        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)

    # -------------------------
    # شیفت روز: مقدارها را از report_data می‌خوانیم
    # (نام کلیدها را تخمینی چندتایی گرفتیم تا یکی‌شان بخورد)
    # -------------------------

    day_start_val = pick(report_data, "day_start", "day_start_m", "day_shift_start")
    day_end_val = pick(report_data, "day_end", "day_end_m", "day_shift_end")
    day_len_val = pick(report_data, "day_len", "day_length", "day_advance")
    day_size_val = pick(report_data, "day_size")
    day_mud_val = pick(report_data, "day_mud", "day_mud_mix")
    day_water_val = pick(report_data, "day_water", "day_water_l")
    day_diesel_val = pick(report_data, "day_diesel", "day_diesel_l")

    day_values = {
        "day_start": day_start_val,
        "day_end": day_end_val,
        "day_len": day_len_val,
        "day_size": day_size_val,
        "day_mud": day_mud_val,
        "day_water": day_water_val,
        "day_diesel": day_diesel_val,
    }

    for key, cfg in DAY_POSITIONS.items():
        raw_val = day_values.get(key, "")
        if raw_val in (None, ""):
            continue

        s = _txt(raw_val)
        unit = cfg.get("unit", "")

        # اگر واحد قبلاً داخل رشته نیست، اضافه‌اش کن
        if unit and unit.strip() not in s:
            s = s + unit

        col = cfg["col"]
        row = cfg["row"]
        align = cfg.get("align", "right")
        font_name = cfg.get("font", FONT_FA)
        font_size = cfg.get("size", 10)
        is_rtl = cfg.get("rtl", True)

        x, y = grid_to_xy(col, row, width, height)

        if is_rtl:
            text = rtl_text(s)
        else:
            text = s

        c.setFont(font_name, font_size)

        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)

    # -------------------------
    # توضیحات: یک کادر مشترک برای روز و شب
    # اگر فقط یکی پر باشد، کل کادر برای همان
    # اگر هر دو باشند، نصف بالا روز، نصف پایین شب
    # -------------------------

    # سعی می‌کنیم براساس نام‌های احتمالی پیدا کنیم
    day_desc = pick(report_data, "day_description", "day_desc", "day_notes")
    night_desc = pick(report_data, "night_description", "night_desc", "night_notes")

    (col_tr, row_tr) = DESC_BOX["top_right"]
    (col_tl, row_tl) = DESC_BOX["top_left"]
    (col_br, row_br) = DESC_BOX["bottom_right"]
    (col_bl, row_bl) = DESC_BOX["bottom_left"]

    x_right_top, y_top = grid_to_xy(col_tr, row_tr, width, height)
    x_left_top, _ = grid_to_xy(col_tl, row_tl, width, height)
    _, y_bottom = grid_to_xy(col_br, row_br, width, height)

    box_width = x_right_top - x_left_top
    if box_width < 0:
        box_width = -box_width

    font_name = DESC_BOX["font"]
    font_size = DESC_BOX["size"]
    leading = DESC_BOX["leading"]

    # تنها روز یا تنها شب
    if day_desc and not night_desc:
        draw_rtl_paragraph(
            c,
            day_desc,
            x_right_top - 5,  # کمی فاصله از خط
            y_top - 5,
            box_width - 10,
            font_name,
            font_size,
            leading,
        )
    elif night_desc and not day_desc:
        draw_rtl_paragraph(
            c,
            night_desc,
            x_right_top - 5,
            y_top - 5,
            box_width - 10,
            font_name,
            font_size,
            leading,
        )
    elif day_desc and night_desc:
        # نصف بالا برای روز، نصف پایین برای شب
        mid_y = (y_top + y_bottom) / 2

        draw_rtl_paragraph(
            c,
            "توضیحات شیفت روز: " + day_desc,
            x_right_top - 5,
            y_top - 5,
            box_width - 10,
            font_name,
            font_size,
            leading,
        )

        draw_rtl_paragraph(
            c,
            "توضیحات شیفت شب: " + night_desc,
            x_right_top - 5,
            mid_y + 5,
            box_width - 10,
            font_name,
            font_size,
            leading,
        )

    # -------------------------
    # پایان
    # -------------------------
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
