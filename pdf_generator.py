# pdf_generator.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import os

# -------------------------------
# تنظیمات صفحه و گرید
# -------------------------------
PAGE_SIZE = landscape(A4)  # A4 افقی
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

# این گرید فقط برای محاسبه‌ی مختصات است (نه چاپ خطوط)
GRID_COLS = 50   # تعداد خانه‌های فرضی افقی
GRID_ROWS = 60   # تعداد خانه‌های فرضی عمودی
MARGIN_X = 20    # حاشیه چپ و راست
MARGIN_Y = 20    # حاشیه بالا و پایین


def grid_to_xy(col: float, row: float):
    """
    col: شماره ستون از سمت راست، صفر یعنی نزدیک‌ترین ستون به لبه‌ی راست فرم
    row: شماره ردیف از بالا
    خروجی: مختصات x,y در سیستم PDF
    """
    cell_w = (PAGE_WIDTH - 2 * MARGIN_X) / GRID_COLS
    cell_h = (PAGE_HEIGHT - 2 * MARGIN_Y) / GRID_ROWS

    # از راست به چپ و از بالا به پایین
    x = PAGE_WIDTH - MARGIN_X - (col + 0.5) * cell_w
    y = PAGE_HEIGHT - MARGIN_Y - (row + 0.5) * cell_h
    return x, y


# -------------------------------
# ثبت فونت فارسی
# -------------------------------
FONT_NAME = "Vazirmatn"

def register_font():
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return
    # فرض می‌کنیم فایل فونت در ریشه‌ی ریپو کنار این فایل است
    font_path = os.path.join(os.path.dirname(__file__), "Vazirmatn-Regular.ttf")
    pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))


# -------------------------------
# مختصات فیلدها روی فرم
# (بر اساس گرید ۵۰×۶۰؛ ممکنه بعداً فقط عدد ستون‌ها کمی فاین‌تیون شوند)
# -------------------------------

# هدر
POS_REGION = (5, 8)    # منطقه
POS_BOREHOLE = (16, 8) # شماره گمانه
POS_RIG = (31, 8)      # دستگاه حفاری
POS_ANGLE = (36, 8)    # زاویه
POS_DATE = (45, 8)     # تاریخ

# ستون شیفت روز در جدول پارامترهای حفاری
# اگر اعداد هنوز در ستون شیفت شب افتادند:
#   برای رفتن به "راست‌تر"  => مقدار DAY_COL را کوچکتر کن (مثلاً 10 یا 9)
#   برای رفتن به "چپ‌تر"   => مقدار DAY_COL را بزرگ‌تر کن
DAY_COL = 11

POS_DAY_START = (DAY_COL, 11)   # متراژ شروع
POS_DAY_END = (DAY_COL, 12.3)   # متراژ پایان
POS_DAY_LEN = (DAY_COL, 13.3)   # متراژ هر شیفت
POS_DAY_SIZE = (DAY_COL, 14.3)  # سایز حفاری
POS_DAY_MUD = (DAY_COL, 15.3)   # نوع گل حفاری
POS_DAY_WATER = (DAY_COL, 16.3) # آب مصرفی
POS_DAY_DIESEL = (DAY_COL, 17.3)# گازوئیل


# -------------------------------
# متن‌سازی از داده‌های شیفت
# -------------------------------

def format_mud_list(muds):
    if not muds:
        return ""
    return " + ".join(muds)


def build_shift_staff_line(shift_data, label):
    """
    خط پرسنل برای چاپ زیر توضیحات (فعلاً فقط به صورت متن آماده؛
    اگر خواستی روی فرم جای خاصی بذاریم، بعداً مختصات می‌دیم.)
    """
    sup = "، ".join(shift_data.get("supervisors") or [])
    helpers = "، ".join(shift_data.get("helpers") or [])
    bosses = "، ".join(shift_data.get("workshop_bosses") or [])

    parts = []
    if sup:
        parts.append(f"مسئول شیفت: {sup}")
    if helpers:
        parts.append(f"پرسنل کمکی: {helpers}")
    if bosses:
        parts.append(f"سرپرست کارگاه: {bosses}")

    if not parts:
        return ""

    return f"{label} - " + " / ".join(parts)


# -------------------------------
# تابع اصلی تولید PDF
# -------------------------------

def generate_pdf(report_data: dict, output_path: str = "daily_drilling_report.pdf") -> str:
    """
    report_data همان user_data[user_id] از bot_flow.py است.
    خروجی: مسیر فایل ساخته شده.
    """
    register_font()

    c = canvas.Canvas(output_path, pagesize=PAGE_SIZE)

    # پس‌زمینه: فرم اصلی
    template_path_jpg = os.path.join(os.path.dirname(__file__), "form_template.jpg")
    if os.path.exists(template_path_jpg):
        bg = ImageReader(template_path_jpg)
        c.drawImage(bg, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
    else:
        # اگر به هر دلیل JPG نبود، می‌توان بعداً روی PDF اصلی کار کرد
        pass

    c.setFont(FONT_NAME, 12)

    # -------- هدر --------
    region = report_data.get("region") or ""
    borehole = report_data.get("borehole") or ""
    rig = report_data.get("rig") or ""
    angle = report_data.get("angle_deg")
    date_str = report_data.get("date") or ""

    if region:
        x, y = grid_to_xy(*POS_REGION)
        c.drawString(x, y, str(region))

    if borehole:
        x, y = grid_to_xy(*POS_BOREHOLE)
        c.drawString(x, y, str(borehole))

    if rig:
        x, y = grid_to_xy(*POS_RIG)
        c.drawString(x, y, str(rig))

    if angle is not None:
        # بدون اعشار و با کلمه درجه
        x, y = grid_to_xy(*POS_ANGLE)
        c.drawString(x, y, f"{int(round(angle))} درجه")

    if date_str:
        x, y = grid_to_xy(*POS_DATE)
        c.drawString(x, y, date_str)

    # -------- شیفت روز در جدول پارامترها --------
    shifts = report_data.get("shifts", {})
    day = shifts.get("day", {})

    if day.get("start") is not None:
        x, y = grid_to_xy(*POS_DAY_START)
        c.drawString(x, y, f"{day['start']} متر")

    if day.get("end") is not None:
        x, y = grid_to_xy(*POS_DAY_END)
        c.drawString(x, y, f"{day['end']} متر")

    if day.get("length") is not None:
        x, y = grid_to_xy(*POS_DAY_LEN)
        c.drawString(x, y, f"{day['length']:.2f} متر")

    if day.get("size"):
        x, y = grid_to_xy(*POS_DAY_SIZE)
        c.drawString(x, y, str(day['size']))

    mud_text = format_mud_list(day.get("mud") or [])
    if mud_text:
        x, y = grid_to_xy(*POS_DAY_MUD)
        c.drawString(x, y, mud_text)

    if day.get("water") is not None:
        x, y = grid_to_xy(*POS_DAY_WATER)
        c.drawString(x, y, f"{day['water']} لیتر")

    if day.get("diesel") is not None:
        x, y = grid_to_xy(*POS_DAY_DIESEL)
        c.drawString(x, y, f"{day['diesel']} لیتر")

    # (فعلاً توضیحات و پرسنل شیفت را فقط در متن تلگرام نشان می‌دهیم؛
    #  برای جایگذاری دقیق روی فرم، بعد از نهایی شدن ستون‌های جدول، مختصات
    #  کادر توضیحات را هم از روی همان گرید ۵ میلی‌متری می‌گیریم.)

    c.showPage()
    c.save()
    return output_path
