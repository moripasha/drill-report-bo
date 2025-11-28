import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# توکن ربات از متغیر محیطی
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# توابع فلو را از bot_flow می‌آوریم
from bot_flow import start_flow, flow_router, handle_callback


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    دستور /start
    اینجا هم خوشامد می‌گوییم هم فلو گزارش را شروع می‌کنیم.
    """
    await update.message.reply_text(
        "سلام. به ربات ثبت گزارش روزانه حفاری شرکت ژئوکان خوش آمدید 🌍"
    )

    # شروع فلو: از مرحله «منطقه» شروع می‌کنیم
    await start_flow(update, context)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    تمام پیام‌های متنی (غیر دستوری) از اینجا رد می‌شوند
    و به فلو اصلی هدایت می‌گردند.
    """
    await flow_router(update, context)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است. لطفاً در Railway متغیر BOT_TOKEN را ست کن.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستور /start
    app.add_handler(CommandHandler("start", start_cmd))

    # همه متن‌ها (به جز /start و سایر کامندها)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # دکمه‌های شیشه‌ای (inline keyboard)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # اجرای ربات با روش polling
    app.run_polling()


if __name__ == "__main__":
    main()
