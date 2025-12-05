from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

# -------------------------------
# تنظیمات گرید مفهومی فرم
# -------------------------------

# تعداد ستون‌ها و ردیف‌ها در مدل ذهنی ما
# عددها رو طوری انتخاب کردم که مختصات تو (تا حدود 45 در ستون) جا بشه
GRID_COLS = 50
GRID_ROWS = 60


def grid_to_xy(col: int, row: int, width: float, height: float,
               margin_x: float = 20, margin_y: float = 20):
    """
    col, row : شماره ستون از راست و ردیف از بالا (همونی که خودت گفتی)
    خروجی : مختصات x, y روی PDF
    """
    usable_w = width - 2 * margin_x
    usable_h = height - 2 * margin_y

    cell_w = usable_w / GRID_COLS
    cell_h = usable_h / GRID_ROWS

    # چون ستون‌ها رو از راست می‌شمریم، x رو از سمت راست حساب می‌کنیم
    x = width - margin_x - (col + 0.5) * cell_w
    # ردیف‌ها از بالا به پایین
    y = height - margin_y - (row + 0.5) * cell_h

    return x, y


# موقعیت هدر بر اساس گریدی که تو دادی
HEADER_POSITIONS = {
    "region": {"col": 5, "row": 8, "align": "right"},  # RGN فارسی → راست‌چین
    "borehole": {"col": 16, "row": 8, "align": "left"},  # BH انگلیسی/عددی
    "rig": {"col": 31, "row": 8, "align": "left"},
    "angle": {"col": 40, "row": 8, "align": "left"},
    "date": {"col": 45, "row": 8, "align": "left"},
}


def _txt(v):
    if v is None:
        return ""
    return str(v)


def split_text(text: str, max_len: int = 90):
    if not text:
        return []
    lines = []
    cur = ""
    for ch in text:
        cur += ch
        if len(cur) >= max_len and ch in (" ", "،", ".", "؛", ","):
            lines.append(cur.strip())
            cur = ""
    if cur.strip():
        lines.append(cur.strip())
    return lines


def generate_pdf(report_data: dict) -> bytes:
    """
    report_data = همون user_data[user_id] توی bot_flow
    خروجی: بایت‌های PDF
    """

    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # عنوان بالا (اختیاری – برای دمو)
    c.setFont("Helvetica-Bold", 14)
    title = "گزارش روزانه عملکرد حفاری (پیمانکار: GEOKAN)"
    c.drawString(40, height - 30, title)

    # -------------------------
    # هدر بر اساس گرید تو
    # -------------------------
    region = _txt(report_data.get("region"))
    borehole = _txt(report_data.get("borehole"))
    rig = _txt(report_data.get("rig"))
    angle = report_data.get("angle_deg")
    angle_str = f"{angle} درجه" if angle is not None else ""
    date_str = _txt(report_data.get("date"))

    header_values = {
        "region": f"منطقه: {region}",
        "borehole": f"شماره گمانه: {borehole}",
        "rig": f"دستگاه حفاری: {rig}",
        "angle": f"زاویه: {angle_str}",
        "date": f"تاریخ: {date_str}",
    }

    c.setFont("Helvetica", 10)

    for key, cfg in HEADER_POSITIONS.items():
        col = cfg["col"]
        row = cfg["row"]
        align = cfg.get("align", "left")
        x, y = grid_to_xy(col, row, width, height)

        text = header_values.get(key, "")
        if not text:
            continue

        if align == "right":
            c.drawRightString(x, y, text)
        else:
            c.drawString(x, y, text)

    # -------------------------
    # بقیهٔ محتوا (شیفت‌ها و توضیحات)
    # این قسمت هنوز گریدی نیست و ساده روی صفحه چیده شده
    # هدف فعلی: فقط تست هدر با گرید
    # -------------------------

    shifts = report_data.get("shifts", {})
    day = shifts.get("day", {}) or {}
    night = shifts.get("night", {}) or {}

    # نقطه شروع جدول پایین‌تر از هدر
    y_table = height - 120

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_table, "مشخصات شیفت‌ها")
    y_table -= 15
    c.setLineWidth(0.7)
    c.line(40, y_table, width - 40, y_table)
    y_table -= 18

    col1_x = 50
    col2_x = 220
    col3_x = 420

    c.setFont("Helvetica-Bold", 10)
    c.drawString(col2_x, y_table, "شیفت روز")
    c.drawString(col3_x, y_table, "شیفت شب")
    y_table -= 14
    c.setFont("Helvetica", 9)

    def fmt_len(v):
        if v is None:
            return ""
        try:
            return f"{float(v):.2f} متر"
        except Exception:
            return _txt(v)

    def fmt_num(v, unit=""):
        if v is None:
            return ""
        try:
            s = f"{float(v):.2f}"
        except Exception:
            s = _txt(v)
        return f"{s} {unit}".strip()

    def fmt_list(lst):
        if not lst:
            return ""
        return "، ".join(lst)

    rows = [
        ("متراژ شروع",        fmt_num(day.get("start"), "متر"),   fmt_num(night.get("start"), "متر")),
        ("متراژ پایان",       fmt_num(day.get("end"), "متر"),     fmt_num(night.get("end"), "متر")),
        ("متراژ شیفت",        fmt_len(day.get("length")),         fmt_len(night.get("length"))),
        ("سایز حفاری",        _txt(day.get("size")),              _txt(night.get("size"))),
        ("نوع گل حفاری",      fmt_list(day.get("mud")),           fmt_list(night.get("mud"))),
        ("آب مصرفی",          fmt_num(day.get("water"), "لیتر"),  fmt_num(night.get("water"), "لیتر")),
        ("گازوئیل",           fmt_num(day.get("diesel"), "لیتر"), fmt_num(night.get("diesel"), "لیتر")),
    ]

    for label, day_val, night_val in rows:
        c.drawString(col1_x, y_table, label + " :")
        c.drawString(col2_x, y_table, day_val)
        c.drawString(col3_x, y_table, night_val)
        y_table -= 14

    y_table -= 8
    c.line(40, y_table, width - 40, y_table)
    y_table -= 12

    # نیروی انسانی
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col1_x, y_table, "نیروی انسانی:")
    y_table -= 14
    c.setFont("Helvetica", 9)

    c.drawString(col1_x, y_table, "مسئول شیفت روز:")
    c.drawString(col2_x, y_table, fmt_list(day.get("supervisors")))
    y_table -= 12

    c.drawString(col1_x, y_table, "پرسنل کمکی روز:")
    c.drawString(col2_x, y_table, fmt_list(day.get("helpers")))
    y_table -= 12

    c.drawString(col1_x, y_table, "سرپرست کارگاه روز:")
    c.drawString(col2_x, y_table, fmt_list(day.get("workshop_bosses")))
    y_table -= 16

    c.drawString(col1_x, y_table, "مسئول شیفت شب:")
    c.drawString(col3_x, y_table, fmt_list(night.get("supervisors")))
    y_table -= 12

    c.drawString(col1_x, y_table, "پرسنل کمکی شب:")
    c.drawString(col3_x, y_table, fmt_list(night.get("helpers")))
    y_table -= 12

    c.drawString(col1_x, y_table, "سرپرست کارگاه شب:")
    c.drawString(col3_x, y_table, fmt_list(night.get("workshop_bosses")))
    y_table -= 20

    # جمع‌بندی
    total_len = (day.get("length") or 0) + (night.get("length") or 0)
    total_water = (day.get("water") or 0) + (night.get("water") or 0)
    total_diesel = (day.get("diesel") or 0) + (night.get("diesel") or 0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_table, "جمع‌بندی روز:")
    y_table -= 14
    c.setFont("Helvetica", 9)
    c.drawString(40, y_table, f"مجموع متراژ حفاری: {total_len:.2f} متر")
    y_table -= 12
    c.drawString(40, y_table, f"مجموع آب مصرفی: {total_water:.2f} لیتر")
    y_table -= 12
    c.drawString(40, y_table, f"مجموع گازوئیل مصرفی: {total_diesel:.2f} لیتر")
    y_table -= 20

    # توضیحات
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y_table, "توضیحات:")
    y_table -= 10

    box_x = 40
    box_y = 80
    box_w = width - 80
    box_h = y_table - box_y

    c.setLineWidth(0.7)
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    d_notes = _txt(day.get("notes")).strip()
    n_notes = _txt(night.get("notes")).strip()

    note_lines = []
    if d_notes:
        note_lines.append("شیفت روز:")
        note_lines.extend(split_text(d_notes, max_len=110))
        note_lines.append("")
    if n_notes:
        note_lines.append("شیفت شب:")
        note_lines.extend(split_text(n_notes, max_len=110))

    c.setFont("Helvetica", 9)
    text_y = box_y + box_h - 16
    for line in note_lines:
        if text_y < box_y + 10:
            break
        c.drawString(box_x + 8, text_y, line)
        text_y -= 11

    # امضاها
    c.setFont("Helvetica", 9)
    sig_y = 55
    c.drawString(40, sig_y, "امضاء مسئول شیفت روز: ........................")
    c.drawString(300, sig_y, "امضاء مسئول شیفت شب: ........................")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
