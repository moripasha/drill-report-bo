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
# ثبت فونت فارسی (Vazirmatn-Regular.ttf در ریشه پروژه)
# ----------------------------------

pdfmetrics.registerFont(
    TTFont("VazirFA", "Vazirmatn-Regular.ttf")
)

FONT_FA = "VazirFA"      # برای متن‌های فارسی
FONT_EN = "Helvetica"    # برای متن‌های لاتین/عدد


# ----------------------------------
# ابزارهای کمکی برای متن فارسی
# ----------------------------------

def rtl_text(text: str) -> str:
    """
    متن فارسی را reshape + bidi می‌کند
    تا حروف به هم چسبیده و راست به چپ نمایش داده شوند.
    """
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
# تنظیمات گرید مفهومی روی صفحه A4 افقی
# ----------------------------------

GRID_COLS = 50
GRID_ROWS = 60


def grid_to_xy(col: int, row: int, width: float, height: float,
               margin_x: float = 0, margin_y: float = 0):
    """
    col, row : شماره ستون از راست و ردیف از بالا
    خروجی : مختصات x, y روی PDF (مرکز آن خانه)
    """

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
# موقعیت ۵ فیلد هدر روی فرم
# فقط اگر لازم شد جا به جا می‌کنیم
# ----------------------------------

HEADER_POSITIONS = {
    # منطقه – فارسی → راست‌چین و RTL
    "region": {
        "col": 5,
        "row": 8,
        "align": "right",
        "font": FONT_FA,
        "size": 11,   # بزرگ‌تر از قبل
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
    "angle": {
        "col": 40,
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
# تولید PDF
# ----------------------------------

def generate_pdf(report_data: dict) -> bytes:
    """
    فعلاً فقط ۵ فیلد هدر را روی فرم اصلی چاپ می‌کند.
    report_data همان user_data[user_id] است.
    """

    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # -------------------------
    # پس‌زمینه: فرم اصلی به صورت تصویر
    # -------------------------
    bg = ImageReader("form_template.jpg")
    c.drawImage(bg, 0, 0, width=width, height=height)

    # -------------------------
    # گرفتن مقادیر خام از report_data
    # -------------------------
    region_raw = _txt(report_data.get("region"))
    borehole_raw = _txt(report_data.get("borehole"))
    rig_raw = _txt(report_data.get("rig"))

    # زاویه: هرچی داده شده، فقط عددش رو نگه می‌داریم
    angle_raw = report_data.get("angle_deg")
    if angle_raw is None:
        angle_raw = report_data.get("angle")
    angle_display = ""
    if angle_raw not in (None, ""):
        s = _txt(angle_raw)
        # فقط اولین دنباله رقم‌ها (مثلاً از "30.0" یا "30 درجه" → "30")
        m = re.search(r"(\d+)", s)
        if m:
            angle_display = f"{m.group(1)} درجه"
        else:
            # اگر اصلاً عدد پیدا نشد، بی‌خیال می‌شیم
            angle_display = ""

    # تاریخ: فرض ورودی سال/ماه/روز → خروجی روز/ماه/سال
    date_raw = _txt(report_data.get("date"))
    date_display = date_raw
    if date_raw and "/" in date_raw:
        parts = date_raw.split("/")
        if len(parts) == 3:
            # اگر قسمت اول 4 رقمی بود یعنی سال است
            if len(parts[0]) == 4:
                y, mth, d = parts
                date_display = f"{d}/{mth}/{y}"

    # فقط مقدارها
    header_values = {
        "region": region_raw,
        "borehole": borehole_raw,
        "rig": rig_raw,
        "angle": angle_display,
        "date": date_display,
    }

    # -------------------------
    # نوشتن فیلدهای هدر روی فرم
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

        # اگر فارسی/RTL باشد، reshape + bidi
        if is_rtl:
            text = rtl_text(raw_text)
        else:
            text = raw_text

        c.setFont(font_name, font_size)

        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)

    # پایان صفحه
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
