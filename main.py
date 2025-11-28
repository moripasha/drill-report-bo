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

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# توابع فلو را از bot_flow می‌آوریم
from bot_flow import start_flow, flow_router, handle_callback


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start تلگرام"""
    await update.message.reply_text(
        "سلام 👋\n"
        "ربات گزارش روزانه حفاری فعال است.\n"
        "برای شروع ثبت گزارش بنویس:\n\n"
        "شروع"
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت همه پیام‌های متنی"""
    text = (update.message.text or "").strip()

    if text == "شروع":
        await start_flow(update, context)
    else:
        await flow_router(update, context)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start_cmd))

    # همه متن‌ها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # دکمه‌های شیشه‌ای (inline keyboard)
    app.add_handler(CallbackQueryHandler(handle_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
