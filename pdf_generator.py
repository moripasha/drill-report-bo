# pdf_generator.py
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

import arabic_reshaper
from bidi.algorithm import get_display

# -------------------------------
# تنظیمات صفحه و گرید
# -------------------------------

PAGE_SIZE = landscape(A4)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

# گرید ذهنی (بر اساس تقسیم‌بندی ۵ میلی‌متری توی فرم کاغذی)
GRID_COLS = 50   # ستون از راست به چپ
GRID_ROWS = 60   # ردیف از بالا به پایین
MARGIN_X = 20
MARGIN_Y = 20


def grid_to_xy(col: float, row: float):
    """
    col: ستون از سمت راست (۰ یعنی نزدیک‌ترین ستون به لبه‌ی راست فرم)
    row: ردیف از بالا
    خروجی: مختصات x, y در PDF
    """
    cell_w = (PAGE_WIDTH - 2 * MARGIN_X) / GRID_COLS
    cell_h = (PAGE_HEIGHT - 2 * MARGIN_Y) / GRID_ROWS

    # مبدأ از گوشه‌ی بالا-چپ صفحه است ولی ما محور x را از راست در نظر گرفته‌ایم
    x = PAGE_WIDTH - MARGIN_X - (col + 0.5) * cell_w
    y = PAGE_HEIGHT - MARGIN_Y - (row + 0.5) * cell_h
    return x, y


# -------------------------------
# فونت و نوشتن فارسی
# -------------------------------

FONT_NAME = "Vazirmatn"


def register_font():
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return
    font_path = os.path.join(os.path.dirname(__file__), "Vazirmatn-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))


def fa_shape(text: str) -> str:
    """شکل‌دهی و bidi برای فارسی/مخلوط"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def draw_fa(c: canvas.Canvas, x: float, y: float, text: str, size: int = 12):
    """نوشتن متن فارسی (یا مخلوط) با سایز مشخص"""
    c.setFont(FONT_NAME, size)
    shaped = fa_shape(text)
    c.drawString(x, y, shaped)


def draw_en(c: canvas.Canvas, x: float, y: float, text: str, size: int = 12):
    """نوشتن متن انگلیسی/عدد ساده بدون reshaper"""
    c.setFont(FONT_NAME, size)
    c.drawString(x, y, str(text))


# -------------------------------
# مختصات فیلدها روی فرم
# -------------------------------

# هدر (مختصات براساس گریدی که قبلاً تعیین کرده بودیم)
POS_REGION = (5, 8)     # منطقه
POS_BOREHOLE = (16, 8)  # شماره گمانه
POS_RIG = (31, 8)       # دستگاه حفاری
POS_ANGLE = (38, 8)     # زاویه
POS_DATE = (45, 8)      # تاریخ

# ستون شیفت روز در جدول پارامترهای حفاری
# اگر دیدی هنوز یک ستون چپ/راست است، فقط این عدد را یکی دو واحد کم/زیاد کن.
DAY_COL = 11

POS_DAY_START = (DAY_COL, 11)    # متراژ شروع
POS_DAY_END = (DAY_COL, 12.3)    # متراژ پایان
POS_DAY_LEN = (DAY_COL, 13.3)    # متراژ هر شیفت
POS_DAY_SIZE = (DAY_COL, 14.3)   # سایز حفاری
POS_DAY_MUD = (DAY_COL, 15.3)    # نوع گل حفاری
POS_DAY_WATER = (DAY_COL, 16.3)  # آب مصرفی
POS_DAY_DIESEL = (DAY_COL, 17.3) # گازوئیل


def format_mud_list(muds):
    if not muds:
        return ""
    return " + ".join(muds)


# -------------------------------
# تابع اصلی تولید PDF
# -------------------------------

def generate_pdf(report_data: dict, output_path: str = "daily_drilling_report.pdf") -> str:
    """
    report_data همان user_data[user_id] در bot_flow.py است.
    """
    register_font()
    c = canvas.Canvas(output_path, pagesize=PAGE_SIZE)

    # پس‌زمینه‌ی فرم
    template_jpg = os.path.join(os.path.dirname(__file__), "form_template.jpg")
    if os.path.exists(template_jpg):
        bg = ImageReader(template_jpg)
        c.drawImage(bg, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    # ------------ هدر ------------
    region = report_data.get("region") or ""
    borehole = report_data.get("borehole") or ""
    rig = report_data.get("rig") or ""
    angle = report_data.get("angle_deg")
    date_str = report_data.get("date") or ""

    if region:
        x, y = grid_to_xy(*POS_REGION)
        draw_fa(c, x, y, str(region), size=13)

    if borehole:
        x, y = grid_to_xy(*POS_BOREHOLE)
        # شماره گمانه معمولاً انگلیسی است
        draw_en(c, x, y, borehole, size=13)

    if rig:
        x, y = grid_to_xy(*POS_RIG)
        draw_en(c, x, y, rig, size=13)

    if angle is not None:
        x, y = grid_to_xy(*POS_ANGLE)
        txt = f"{int(round(angle))} درجه"
        draw_fa(c, x, y, txt, size=13)

    if date_str:
        x, y = grid_to_xy(*POS_DATE)
        # تاریخ به صورت روز/ماه/سال از bot_flow می‌آید
        draw_en(c, x, y, date_str, size=13)

    # ------------ شیفت روز در جدول پارامترها ------------
    shifts = report_data.get("shifts", {})
    day = shifts.get("day", {})

    if day.get("start") is not None:
        x, y = grid_to_xy(*POS_DAY_START)
        draw_fa(c, x, y, f"{day['start']} متر")

    if day.get("end") is not None:
        x, y = grid_to_xy(*POS_DAY_END)
        draw_fa(c, x, y, f"{day['end']} متر")

    if day.get("length") is not None:
        x, y = grid_to_xy(*POS_DAY_LEN)
        draw_fa(c, x, y, f"{day['length']:.2f} متر")

    if day.get("size"):
        x, y = grid_to_xy(*POS_DAY_SIZE)
        draw_en(c, x, y, str(day["size"]))

    mud_text = format_mud_list(day.get("mud") or [])
    if mud_text:
        x, y = grid_to_xy(*POS_DAY_MUD)
        draw_fa(c, x, y, mud_text)

    if day.get("water") is not None:
        x, y = grid_to_xy(*POS_DAY_WATER)
        draw_fa(c, x, y, f"{day['water']} لیتر")

    if day.get("diesel") is not None:
        x, y = grid_to_xy(*POS_DAY_DIESEL)
        draw_fa(c, x, y, f"{day['diesel']} لیتر")

    # فعلاً توضیحات و پرسنل را روی فرم نمی‌ریزیم
    # تا مطمئن شویم ستون‌ها و متن‌ها کاملاً درست شده‌اند.

    c.showPage()
    c.save()
    return output_path
