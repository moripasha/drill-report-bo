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

from bot_flow import start_flow, flow_router, handle_callback, user_data
import pdf_generator

TOKEN = os.getenv("BOT_TOKEN")


async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_data:
        await update.message.reply_text("هنوز هیچ گزارشی برای شما ثبت نشده.")
        return

    report = user_data[user_id]

    shifts = report.get("shifts", {})
    day = shifts.get("day", {}) or {}
    night = shifts.get("night", {}) or {}

    # حداقل یکی از شیفت‌ها باید متراژ داشته باشد
    if not day.get("start") and not night.get("start"):
        await update.message.reply_text("گزارش ناقص است. ابتدا حداقل یک شیفت را کامل ثبت کن.")
        return

    pdf_bytes = pdf_generator.generate_pdf(report)

    await update.message.reply_document(
        document=pdf_bytes,
        filename="daily_drilling_report.pdf",
        caption="📄 گزارش روزانه حفاری",
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_flow))
    app.add_handler(CommandHandler("pdf", send_pdf))  # دستور تولید PDF
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, flow_router))

    app.run_polling()


if __name__ == "__main__":
    main()
