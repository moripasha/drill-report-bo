from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# -------------------------------
# تنظیمات گرید مفهومی فرم
# -------------------------------

# تعداد ستون‌ها و ردیف‌ها در مدل ذهنی ما
# فعلاً 50x60 می‌گذاریم که راحت همه چیز جا بشود
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


# مختصات هدر بر اساس چیزی که تو دادی
HEADER_POSITIONS = {
    "region":   {"col": 5,  "row": 8, "align": "right"},  # منطقه (فارسی → راست چین)
    "borehole": {"col": 16, "row": 8, "align": "left"},   # شماره گمانه (لاتین/عدد → چپ چین)
    "rig":      {"col": 31, "row": 8, "align": "left"},
    "angle":    {"col": 40, "row": 8, "align": "left"},
    "date":     {"col": 45, "row": 8, "align": "left"},
}


def _txt(v):
    if v is None:
        return ""
    return str(v)


def generate_pdf(report_data: dict) -> bytes:
    """
    نسخه تست: فقط هدر را روی فرم اصلی چاپ می‌کند.
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
    # حتماً یک فایل form_template.jpg در ریشه پروژه بگذار
    # (اسکن همین فرم)
    bg = ImageReader("form_template.jpg")
    c.drawImage(bg, 0, 0, width=width, height=height)

    # -------------------------
    # داده‌های هدر از report_data
    # -------------------------
    region = _txt(report_data.get("region"))
    borehole = _txt(report_data.get("borehole"))
    rig = _txt(report_data.get("rig"))

    angle = report_data.get("angle_deg")
    if angle is None:
        angle = report_data.get("angle")
    angle_str = f"{angle} درجه" if angle not in (None, "") else ""

    date_str = _txt(report_data.get("date"))

    header_values = {
        "region": f"منطقه: {region}",
        "borehole": f"شماره گمانه: {borehole}",
        "rig": f"دستگاه حفاری: {rig}",
        "angle": f"زاویه: {angle_str}",
        "date": f"تاریخ: {date_str}",
    }

    # فونت برای تست
    c.setFont("Helvetica", 9)

    # -------------------------
    # نوشتن ۵ فیلد روی فرم
    # -------------------------
    for key, cfg in HEADER_POSITIONS.items():
        text = header_values.get(key, "")
        if not text:
            continue

        col = cfg["col"]
        row = cfg["row"]
        align = cfg.get("align", "left")

        x, y = grid_to_xy(col, row, width, height)

        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)

    # پایان و خروجی
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
