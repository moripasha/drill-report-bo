from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# نگهدارنده اطلاعات کاربر
user_states = {}
user_data = {}

# مرحله‌های فلو
STEP_REGION = "region"
STEP_BOREHOLE = "borehole"
STEP_RIG = "rig"


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فلو گزارش: سوال منطقه"""
    user_id = update.effective_user.id
    user_states[user_id] = STEP_REGION
    user_data[user_id] = {}

    await update.message.reply_text(
        "🔸 لطفاً *منطقه* را وارد کن:",
        parse_mode="Markdown"
    )


async def flow_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هدایت پیام‌های متنی بر اساس مرحله فعلی"""
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id not in user_states:
        await update.message.reply_text("برای شروع دستور /start را بزن.")
        return

    step = user_states[user_id]

    # --- مرحله ۱: منطقه ---
    if step == STEP_REGION:
        user_data[user_id]["region"] = text
        user_states[user_id] = STEP_BOREHOLE

        await update.message.reply_text(
            "🔸 *شماره گمانه* را وارد کن:",
            parse_mode="Markdown"
        )
        return

    # --- مرحله ۲: شماره گمانه ---
    if step == STEP_BOREHOLE:
        user_data[user_id]["borehole"] = text
        user_states[user_id] = STEP_RIG

        # انتخاب دستگاه حفاری
        buttons = [
            [InlineKeyboardButton("DB 1200", callback_data="rig_DB1200")],
            [InlineKeyboardButton("DBC-S15-A", callback_data="rig_DBC")]
        ]
        markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "🔸 *نوع دستگاه حفاری* را انتخاب کن:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # در مراحل بعدی اینجا ادامه می‌دیم (زاویه، تاریخ، شیفت، ...)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل دکمه‌های انتخابی (inline keyboard)"""
    query = update.callback_query
    await query.answer()  # برای حذف لودینگ

    user_id = query.from_user.id
    data = query.data

    if user_id not in user_states:
        await query.edit_message_text("جلسه‌ی قبلی منقضی شده. بنویس: شروع")
        return

    # انتخاب دستگاه حفاری
    if data.startswith("rig_"):
        rig_label = "DB 1200" if data == "rig_DB1200" else "DBC-S15-A"
        user_data.setdefault(user_id, {})["rig"] = rig_label

        # فعلاً فقط تست: اطلاعات جمع‌شده تا این مرحله را نشان می‌دهیم
        region = user_data[user_id].get("region", "-")
        borehole = user_data[user_id].get("borehole", "-")

        text = (
            "✅ تا اینجا اطلاعات زیر ثبت شد:\n"
            f"• منطقه: {region}\n"
            f"• شماره گمانه: {borehole}\n"
            f"• دستگاه حفاری: {rig_label}\n\n"
            "در مرحله بعد زاویه، تاریخ، شیفت و بقیه موارد را اضافه می‌کنیم."
        )

        await query.edit_message_text(text)
        return
