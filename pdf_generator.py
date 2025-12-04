from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


def _txt(v):
    """برای تبدیل None به رشته خالی و جلوگیری از خراب شدن متن."""
    if v is None:
        return ""
    return str(v)


def split_text(text: str, max_len: int = 90):
    """
    یک wrap خیلی ساده بر اساس طول کاراکتر.
    برای دمو کاملاً کافی است.
    """
    if not text:
        return []

    lines = []
    current = ""
    for ch in text:
        current += ch
        # وقتی طول خط از max_len گذشت و به یک جداکننده رسیدیم، خط را می‌بندیم
        if len(current) >= max_len and ch in (" ", "،", ".", "؛", ","):
            lines.append(current.strip())
            current = ""
    if current.strip():
        lines.append(current.strip())
    return lines


def generate_pdf(report_data: dict) -> bytes:
    """
    report_data همان user_data[user_id] است که در bot_flow نگه می‌داریم.
    خروجی: بایت‌های PDF برای ارسال در تلگرام.
    """

    buffer = BytesIO()

    # صفحه A4 افقی
    page_size = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page_size)
    width, height = page_size

    # حاشیه‌ها
    margin_x = 40
    margin_y = 40

    # عنوان اصلی بالا
    title = "گزارش روزانه عملکرد حفاری (پیمانکار: GEOKAN)"
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, height - margin_y, title)

    # هدر: منطقه، گمانه، دستگاه، زاویه، تاریخ
    c.setFont("Helvetica", 11)
    y = height - margin_y - 25

    region = _txt(report_data.get("region"))
    borehole = _txt(report_data.get("borehole"))
    rig = _txt(report_data.get("rig"))
    angle = report_data.get("angle_deg")
    angle_str = f"{angle} درجه" if angle is not None else ""
    date_str = _txt(report_data.get("date"))

    # ردیف اول هدر
    c.drawString(margin_x, y, f"منطقه: {region}")
    c.drawString(margin_x + 260, y, f"شماره گمانه: {borehole}")
    y -= 18

    # ردیف دوم هدر
    c.drawString(margin_x, y, f"دستگاه حفاری: {rig}")
    c.drawString(margin_x + 260, y, f"زاویه: {angle_str}")
    y -= 18

    # ردیف سوم هدر
    c.drawString(margin_x, y, f"تاریخ: {date_str}")
    y -= 15

    # خط جداکننده
    c.line(margin_x, y, width - margin_x, y)
    y -= 10

    # داده‌های شیفت‌ها
    shifts = report_data.get("shifts", {})
    day = shifts.get("day", {}) or {}
    night = shifts.get("night", {}) or {}

    # عنوان جدول پارامترهای حفاری
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "مشخصات شیفت‌ها")
    y -= 5
    c.setLineWidth(0.8)
    c.line(margin_x, y, width - margin_x, y)
    y -= 15

    # جدول ساده برای شیفت روز و شب کنار هم (روش ۱: روبه‌روی عنوان‌ها)
    c.setFont("Helvetica-Bold", 10)

    col1_x = margin_x + 10          # ستون عنوان فارسی
    col2_x = margin_x + 140         # مقدار شیفت روز
    col3_x = margin_x + 330         # مقدار شیفت شب

    c.drawString(col2_x, y, "شیفت روز")
    c.drawString(col3_x, y, "شیفت شب")
    y -= 15
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

    # ردیف‌ها: همان عناوینی که در فرم اصلی هستند
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
        c.drawString(col1_x, y, label + " :")
        c.drawString(col2_x, y, day_val)
        c.drawString(col3_x, y, night_val)
        y -= 14

    y -= 5
    c.line(margin_x, y, width - margin_x, y)
    y -= 10

    # مسئول / کمکی / سرپرست کارگاه (روز / شب)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(col1_x, y, "نیروی انسانی:")
    y -= 14
    c.setFont("Helvetica", 9)

    c.drawString(col1_x, y, "مسئول شیفت روز:")
    c.drawString(col2_x, y, fmt_list(day.get("supervisors")))
    y -= 12

    c.drawString(col1_x, y, "پرسنل کمکی روز:")
    c.drawString(col2_x, y, fmt_list(day.get("helpers")))
    y -= 12

    c.drawString(col1_x, y, "سرپرست کارگاه روز:")
    c.drawString(col2_x, y, fmt_list(day.get("workshop_bosses")))
    y -= 16

    c.drawString(col1_x, y, "مسئول شیفت شب:")
    c.drawString(col3_x, y, fmt_list(night.get("supervisors")))
    y -= 12

    c.drawString(col1_x, y, "پرسنل کمکی شب:")
    c.drawString(col3_x, y, fmt_list(night.get("helpers")))
    y -= 12

    c.drawString(col1_x, y, "سرپرست کارگاه شب:")
    c.drawString(col3_x, y, fmt_list(night.get("workshop_bosses")))
    y -= 20

    # جمع‌بندی پایین جدول (مجموع متراژ، آب، گازوئیل)
    total_len = (day.get("length") or 0) + (night.get("length") or 0)
    total_water = (day.get("water") or 0) + (night.get("water") or 0)
    total_diesel = (day.get("diesel") or 0) + (night.get("diesel") or 0)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_x, y, "جمع‌بندی روز:")
    y -= 14
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, y, f"مجموع متراژ حفاری: {total_len:.2f} متر")
    y -= 12
    c.drawString(margin_x, y, f"مجموع آب مصرفی: {total_water:.2f} لیتر")
    y -= 12
    c.drawString(margin_x, y, f"مجموع گازوئیل مصرفی: {total_diesel:.2f} لیتر")
    y -= 20

    # کادر بزرگ توضیحات
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y, "توضیحات:")
    y -= 10

    box_x = margin_x
    box_y = margin_y + 70
    box_w = width - 2 * margin_x
    box_h = y - box_y

    # مستطیل توضیحات
    c.setLineWidth(0.8)
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    # متن توضیحات (شیفت روز + شیفت شب) داخل کادر
    d_notes = _txt(day.get("notes")).strip()
    n_notes = _txt(night.get("notes")).strip()

    notes_lines = []
    if d_notes:
        notes_lines.append("شیفت روز:")
        notes_lines.extend(split_text(d_notes, max_len=110))
        notes_lines.append("")
    if n_notes:
        notes_lines.append("شیفت شب:")
        notes_lines.extend(split_text(n_notes, max_len=110))

    c.setFont("Helvetica", 9)
    text_y = box_y + box_h - 16
    for line in notes_lines:
        if text_y < box_y + 10:
            break
        c.drawString(box_x + 8, text_y, line)
        text_y -= 11

    # محل امضاها (خالی می‌گذاریم که دستی پر بشود)
    c.setFont("Helvetica", 9)
    sig_y = margin_y + 30
    c.drawString(margin_x, sig_y, "امضاء مسئول شیفت روز: .......................")
    c.drawString(margin_x + 260, sig_y, "امضاء مسئول شیفت شب: .......................")

    # پایان صفحه
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
