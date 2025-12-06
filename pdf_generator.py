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
    # کمی بیش‌تر به سمت راست (عدد ستون کمتر)
    "angle": {
        "col": 34,   # قبلاً 37، حالا نزدیک‌تر به سمت راست
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


# (بخش‌های DAY_POSITIONS و DESC_BOX را فعلاً نگه می‌دارم برای بعد،
# ولی چون دیتا به اسم درست نمی‌رسه، فعلاً اثری ندارند)


# ----------------------------------
# تولید PDF
# فعلاً فقط هدر + خروجی دیباگ از کل report_data
# ----------------------------------

def generate_pdf(report_data: dict) -> bytes:
    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # پس‌زمینه: تصویر فرم اصلی
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

    # رسم فیلدهای هدر
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
    # 🍥 دیباگ: چاپ همهٔ key/value های report_data پایین صفحه
    # -------------------------
    c.setFont(FONT_EN, 6)
    y_debug = 20  # کمی بالاتر از لبه پایین
    x_debug = 30

    for k, v in report_data.items():
        line = f"{k}: {v}"
        # طول خط رو کوتاه می‌کنیم که از صفحه نزنه بیرون
        if len(line) > 130:
            line = line[:127] + "..."
        c.drawString(x_debug, y_debug, line)
        y_debug += 8
        if y_debug > 150:  # اگر خیلی زیاد شد، بیشترش رو نمی‌نویسیم
            break

    # پایان
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
