from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

# نگهدارنده اطلاعات کاربر
user_states = {}
user_data = {}

# مرحله‌های فلو
STEP_REGION = "region"
STEP_BOREHOLE = "borehole"
STEP_RIG = "rig"
STEP_ANGLE = "angle"
STEP_DATE_YEAR = "date_year"
STEP_DATE_MONTH = "date_month"
STEP_DATE_DAY = "date_day"
STEP_HEADER_DONE = "header_done"


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    شروع فلو گزارش:
    از کاربر منطقه را می‌پرسیم و ساختار داده را ریست می‌کنیم.
    """
    user_id = update.effective_user.id
    user_states[user_id] = STEP_REGION
    user_data[user_id] = {
        "region": None,
        "borehole": None,
        "rig": None,
        "angle_deg": None,
        "date": None,  # به صورت روز/ماه/سال
    }

    await update.message.reply_text(
        "🔸 لطفاً *منطقه* را وارد کنید:",
        parse_mode="Markdown"
    )


async def flow_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هدایت پیام‌های متنی بر اساس مرحله فعلی کاربر
    """
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id not in user_states:
        await update.message.reply_text("برای شروع دستور /start را بزنید.")
        return

    step = user_states[user_id]

    # --- مرحله ۱: منطقه ---
    if step == STEP_REGION:
        user_data[user_id]["region"] = text
        user_states[user_id] = STEP_BOREHOLE

        await update.message.reply_text(
            "🔸 *شماره گمانه* را وارد کنید:",
            parse_mode="Markdown"
        )
        return

    # --- مرحله ۲: شماره گمانه ---
    if step == STEP_BOREHOLE:
        user_data[user_id]["borehole"] = text
        user_states[user_id] = STEP_RIG

        # انتخاب دستگاه حفاری با دکمه
        buttons = [
            [InlineKeyboardButton("DB 1200", callback_data="rig_DB1200")],
            [InlineKeyboardButton("DBC-S15-A", callback_data="rig_DBC")],
        ]
        markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "🔸 *نوع دستگاه حفاری* را انتخاب کنید:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # --- مرحله ۴: زاویه ---
    if step == STEP_ANGLE:
        # فقط عدد قبول کنیم
        try:
            angle_val = float(text.replace(",", "."))
        except ValueError:
            await update.message.reply_text(
                "⛔ لطفاً زاویه را فقط به صورت عدد وارد کنید (مثلاً 45 یا 75.5)."
            )
            return

        user_data[user_id]["angle_deg"] = angle_val
        user_states[user_id] = STEP_DATE_YEAR

        await update.message.reply_text(
            "🔸 سال گزارش را وارد کنید (مثلاً 1404):"
        )
        return

    # --- مرحله ۵: سال ---
    if step == STEP_DATE_YEAR:
        if not text.isdigit():
            await update.message.reply_text("⛔ سال باید فقط عدد باشد. دوباره وارد کنید.")
            return
        year = int(text)
        if year < 1300 or year > 1500:
            await update.message.reply_text("⛔ سال وارد شده نامعتبر است. دوباره وارد کنید.")
            return

        user_data[user_id]["date_year"] = year
        user_states[user_id] = STEP_DATE_MONTH

        await update.message.reply_text("🔸 *ماه* را وارد کنید (عدد 1 تا 12):")
        return

    # --- مرحله ۶: ماه ---
    if step == STEP_DATE_MONTH:
        if not text.isdigit():
            await update.message.reply_text("⛔ ماه باید فقط عدد باشد. دوباره وارد کنید.")
            return
        month = int(text)
        if month < 1 or month > 12:
            await update.message.reply_text("⛔ ماه باید بین 1 و 12 باشد. دوباره وارد کنید.")
            return

        user_data[user_id]["date_month"] = month
        user_states[user_id] = STEP_DATE_DAY

        await update.message.reply_text("🔸 *روز* را وارد کنید (عدد 1 تا 31):")
        return

    # --- مرحله ۷: روز ---
    if step == STEP_DATE_DAY:
        if not text.isdigit():
            await update.message.reply_text("⛔ روز باید فقط عدد باشد. دوباره وارد کنید.")
            return
        day = int(text)
        if day < 1 or day > 31:
            await update.message.reply_text("⛔ روز باید بین 1 و 31 باشد. دوباره وارد کنید.")
            return

        year = user_data[user_id].get("date_year")
        month = user_data[user_id].get("date_month")

        # فرمت نهایی: روز/ماه/سال
        date_str = f"{day:02d}/{month:02d}/{year}"
        user_data[user_id]["date"] = date_str

        # از این به بعد دیگر فیلدهای کمکی date_year و date_month و ... لازم نیست
        user_data[user_id].pop("date_year", None)
        user_data[user_id].pop("date_month", None)

        user_states[user_id] = STEP_HEADER_DONE

        region = user_data[user_id].get("region", "-")
        borehole = user_data[user_id].get("borehole", "-")
        rig = user_data[user_id].get("rig", "-")
        angle = user_data[user_id].get("angle_deg", "-")

        summary = (
            "✅ اطلاعات هدر گزارش تا این مرحله:\n"
            f"• منطقه: {region}\n"
            f"• شماره گمانه: {borehole}\n"
            f"• دستگاه حفاری: {rig}\n"
            f"• زاویه: {angle} درجه\n"
            f"• تاریخ: {date_str}\n\n"
            "در مرحله بعد، اطلاعات شیفت‌ها، متراژها و بقیه موارد اضافه می‌شود."
        )

        await update.message.reply_text(summary)
        return

    # مراحل بعدی (شیفت‌ها، متراژ، گل حفاری، سوخت، توضیحات و ...) را بعداً اینجا ادامه می‌دهیم.
    if step == STEP_HEADER_DONE:
        await update.message.reply_text(
            "هدر گزارش ثبت شده است. در نسخه بعدی ادامه فلو (شیفت‌ها و متراژ) اضافه می‌شود."
        )
        return


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هندل دکمه‌های انتخابی (inline keyboard)
    """
    query = update.callback_query
    await query.answer()  # برای حذف حالت لودینگ

    user_id = query.from_user.id
    data = query.data

    if user_id not in user_states:
        await query.edit_message_text("جلسه قبلی منقضی شده است. دوباره /start را بزنید.")
        return

    # انتخاب دستگاه حفاری
    if data.startswith("rig_"):
        rig_label = "DB 1200" if data == "rig_DB1200" else "DBC-S15-A"
        user_data.setdefault(user_id, {})["rig"] = rig_label

        # بعد از انتخاب دستگاه، می‌رویم سراغ زاویه
        user_states[user_id] = STEP_ANGLE

        await query.edit_message_text(
            "🔸 زاویه حفاری را وارد کنید (فقط عدد)."
        )
        return
