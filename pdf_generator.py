from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ----------------------------------
# ثبت فونت فارسی (Vazirmatn-Regular.ttf در ریشه پروژه)
# ----------------------------------

# توجه: فایل Vazirmatn-Regular.ttf باید در همین مسیر ریشه ریپو باشد
# (همون جایی که bot_flow.py و main.py هستند)
pdfmetrics.registerFont(
    TTFont("VazirFA", "Vazirmatn-Regular.ttf")
)

FONT_FA = "VazirFA"     # برای متن‌های فارسی
FONT_EN = "Helvetica"   # برای متن‌های انگلیسی/عددی


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
# موقعیت ۵ فیلد هدر روی فرم (بر اساس مختصات خودت)
# ----------------------------------

HEADER_POSITIONS = {
    # منطقه – فارسی → راست‌چین
    "region": {
        "col": 5,
        "row": 8,
        "align": "right",
        "font": FONT_FA,
        "size": 9,
    },
    # شماره گمانه – حروف/عدد لاتین → چپ‌چین
    "borehole": {
        "col": 16,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 9,
    },
    # دستگاه حفاری – لاتین
    "rig": {
        "col": 31,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 9,
    },
    # زاویه – فقط مقدار عددی (مثلاً 40)
    "angle": {
        "col": 40,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 9,
    },
    # تاریخ – مثلاً 1403/09/15
    "date": {
        "col": 45,
        "row": 8,
        "align": "left",
        "font": FONT_EN,
        "size": 9,
    },
}


def _txt(v):
    if v is None:
        return ""
    return str(v)


def generate_pdf(report_data: dict) -> bytes:
    """
    نسخه‌ی تست: فقط ۵ فیلد هدر را روی فرم اصلی چاپ می‌کند.
    report_data همان دیکشنری user_data[user_id] است که در bot_flow نگه می‌داری.
    """

    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # -------------------------
    # پس‌زمینه: فرم اصلی به صورت تصویر
    # -------------------------
    # فایل form_template.jpg باید در ریشه ریپو باشد
    bg = ImageReader("form_template.jpg")
    c.drawImage(bg, 0, 0, width=width, height=height)

    # -------------------------
    # گرفتن مقادیر از report_data
    # -------------------------
    region = _txt(report_data.get("region"))
    borehole = _txt(report_data.get("borehole"))
    rig = _txt(report_data.get("rig"))

    angle = report_data.get("angle_deg")
    if angle is None:
        angle = report_data.get("angle")
    angle_val = _txt(angle)

    date_str = _txt(report_data.get("date"))

    # 🔴 فقط مقدارها، بدون تیتر «منطقه»، «شماره گمانه» و ...
    header_values = {
        "region": region,
        "borehole": borehole,
        "rig": rig,
        "angle": angle_val,
        "date": date_str,
    }

    # -------------------------
    # نوشتن فیلدهای هدر روی فرم
    # -------------------------
    for key, cfg in HEADER_POSITIONS.items():
        text = header_values.get(key, "")
        if not text:
            continue

        col = cfg["col"]
        row = cfg["row"]
        align = cfg.get("align", "left")
        font_name = cfg.get("font", FONT_EN)
        font_size = cfg.get("size", 9)

        x, y = grid_to_xy(col, row, width, height)

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
