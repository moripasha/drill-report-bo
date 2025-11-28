from telegram import Update
from telegram.ext import ContextTypes

# نگهدارنده اطلاعات کاربر
user_states = {}
user_data = {}

# مرحله‌های فلو
STEP_REGION = "region"
STEP_BOREHOLE = "borehole"
STEP_RIG = "rig"


async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = STEP_REGION
    user_data[user_id] = {}

    await update.message.reply_text("🔸 لطفاً *منطقه* را وارد کن:",
                                    parse_mode="Markdown")


async def flow_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_states:
        await update.message.reply_text("برای شروع بنویس: شروع")
        return

    step = user_states[user_id]

    # --- مرحله ۱: منطقه ---
    if step == STEP_REGION:
        user_data[user_id]["region"] = text
        user_states[user_id] = STEP_BOREHOLE
        await update.message.reply_text("🔸 *شماره گمانه* را وارد کن:",
                                        parse_mode="Markdown")
        return

    # --- مرحله ۲: شماره گمانه ---
    if step == STEP_BOREHOLE:
        user_data[user_id]["borehole"] = text
        user_states[user_id] = STEP_RIG

        # انتخاب دستگاه حفاری
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
