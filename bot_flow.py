خیلی خوب گرفتی اشکال رو، دقیقاً همون دو جا گیره 👌
بیا این‌ها رو درست کنیم:

1. بعد از گل حفاری:
الان فقط وقتی دکمه‌ی «اتمام انتخاب» رو بزنی می‌ره سراغ آب مصرفی. تو اگر فقط گل‌ها رو بزنی و هیچی رو نزنی، طبیعیه اتفاقی نمیفته. من تو متن و منطق، این رو واضح‌تر کردم که:

برای ادامه حتماً باید «اتمام انتخاب» رو بزنی

هر گل رو دوباره بزنی حذف می‌شه (ویرایش انتخاب‌ها)



2. بعد متراژ (طول شیفت):
دیگه اون «برای ادامه، هرچیزی بفرستید» رو حذف کردم.
الان به‌محض این‌که متراژ پایان رو وارد کنی:

خودش طول شیفت رو حساب می‌کنه

همون‌جا نتیجه رو نشون می‌ده

هم‌زمان دکمه‌های سایز حفاری (BQ/NQ/HQ/PQ) میاد پایینش → یعنی دکمه، نه تایپ.




این یعنی هم UX بهتر، هم دقیق‌تر مطابق خواسته تو.

همیشه طبق قانون، کل فایل bot_flow.py رو جدید می‌دم 👇
برو تو گیت‌هاب → bot_flow.py → Edit → همه‌اش رو پاک کن → دقیقاً اینو بچسبون:


---

bot_flow.py (نسخه جدید با اصلاح گل حفاری و متراژ)

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

# ================================
#  داده‌ها و مرحله‌ها
# ================================

user_states = {}
user_data = {}

# مراحل هدر
STEP_REGION = "region"
STEP_BOREHOLE = "borehole"
STEP_RIG = "rig"
STEP_ANGLE = "angle"
STEP_DATE_YEAR = "date_year"
STEP_DATE_MONTH = "date_month"
STEP_DATE_DAY = "date_day"

# مراحل شیفت‌ها
STEP_CHOOSE_SHIFT = "choose_shift"
STEP_START_DEPTH = "start_depth"
STEP_END_DEPTH = "end_depth"
STEP_SIZE = "size"
STEP_MUD = "mud"
STEP_WATER = "water"
STEP_DIESEL = "diesel"
STEP_ASK_NEXT_SHIFT = "ask_next_shift"

# وقتی شیفت‌ها کامل شدند
STEP_SHIFTS_DONE = "shifts_done"


# ================================
#   شروع فلو
# ================================

async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_states[user_id] = STEP_REGION
    user_data[user_id] = {
        "region": None,
        "borehole": None,
        "rig": None,
        "angle_deg": None,
        "date": None,

        "shifts": {
            "day": {},
            "night": {},
        },
        "current_shift": None
    }

    await update.message.reply_text("🔸 لطفاً *منطقه* را وارد کنید:",
                                    parse_mode="Markdown")


# ================================
#   مدیریت پیام‌های متنی
# ================================

async def flow_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id not in user_states:
        await update.message.reply_text("برای شروع /start را بزنید.")
        return

    step = user_states[user_id]

    # ----------------------------------
    #   مراحل هدر
    # ----------------------------------

    if step == STEP_REGION:
        user_data[user_id]["region"] = text
        user_states[user_id] = STEP_BOREHOLE
        await update.message.reply_text("🔸 *شماره گمانه* را وارد کنید:",
                                        parse_mode="Markdown")
        return

    if step == STEP_BOREHOLE:
        user_data[user_id]["borehole"] = text
        user_states[user_id] = STEP_RIG

        buttons = [
            [InlineKeyboardButton("DB 1200", callback_data="rig_DB1200")],
            [InlineKeyboardButton("DBC-S15-A", callback_data="rig_DBC")],
        ]
        markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text("🔸 *نوع دستگاه حفاری* را انتخاب کنید:",
                                        reply_markup=markup,
                                        parse_mode="Markdown")
        return

    if step == STEP_ANGLE:
        try:
            angle_val = float(text.replace(",", "."))
        except ValueError:
            await update.message.reply_text("⛔ لطفاً زاویه را فقط عدد وارد کنید.")
            return

        user_data[user_id]["angle_deg"] = angle_val
        user_states[user_id] = STEP_DATE_YEAR

        await update.message.reply_text("🔸 سال گزارش را وارد کنید:")
        return

    if step == STEP_DATE_YEAR:
        if not text.isdigit():
            await update.message.reply_text("⛔ سال باید عدد باشد.")
            return

        year = int(text)
        if year < 1300 or year > 1500:
            await update.message.reply_text("⛔ سال نامعتبر.")
            return

        user_data[user_id]["date_year"] = year
        user_states[user_id] = STEP_DATE_MONTH
        await update.message.reply_text("🔸 ماه را وارد کنید (۱ تا ۱۲):")
        return

    if step == STEP_DATE_MONTH:
        if not text.isdigit():
            await update.message.reply_text("⛔ ماه باید عدد باشد.")
            return

        month = int(text)
        if not 1 <= month <= 12:
            await update.message.reply_text("⛔ ماه باید بین ۱ تا ۱۲ باشد.")
            return

        user_data[user_id]["date_month"] = month
        user_states[user_id] = STEP_DATE_DAY
        await update.message.reply_text("🔸 روز را وارد کنید (۱ تا ۳۱):")
        return

    if step == STEP_DATE_DAY:
        if not text.isdigit():
            await update.message.reply_text("⛔ روز باید عدد باشد.")
            return

        day = int(text)
        if not 1 <= day <= 31:
            await update.message.reply_text("⛔ روز باید بین ۱ تا ۳۱ باشد.")
            return

        year = user_data[user_id]["date_year"]
        month = user_data[user_id]["date_month"]

        date_str = f"{day:02d}/{month:02d}/{year}"
        user_data[user_id]["date"] = date_str

        del user_data[user_id]["date_year"]
        del user_data[user_id]["date_month"]

        # بعد از هدر → شیفت‌ها
        await show_header_summary(update, user_id)
        await ask_shift_choice(update, user_id)
        return

    # ----------------------------------
    #   مراحل شیفت‌ها
    # ----------------------------------

    if step == STEP_START_DEPTH:
        return await handle_start_depth(update, user_id, text)

    if step == STEP_END_DEPTH:
        return await handle_end_depth(update, user_id, text)

    if step == STEP_WATER:
        return await handle_water(update, user_id, text)

    if step == STEP_DIESEL:
        return await handle_diesel(update, user_id, text)

    # اگر هیچ‌کدام نبود
    await update.message.reply_text("⛔ دستور نامعتبر است.")


# ================================
#   دکمه‌های شیشه‌ای (Callback)
# ================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if user_id not in user_states:
        await query.edit_message_text("جلسه منقضی شده → /start")
        return

    # انتخاب دستگاه حفاری
    if data.startswith("rig_"):
        rig_label = "DB 1200" if data == "rig_DB1200" else "DBC-S15-A"
        user_data[user_id]["rig"] = rig_label
        user_states[user_id] = STEP_ANGLE

        await query.edit_message_text("🔸 زاویه حفاری را وارد کنید:")
        return

    # انتخاب شیفت
    if data in ("shift_day", "shift_night"):
        shift_key = "day" if data == "shift_day" else "night"
        user_data[user_id]["current_shift"] = shift_key
        return await ask_start_depth(query, user_id)

    # سایز حفاری
    if data.startswith("size_"):
        size = data.replace("size_", "")
        return await set_size(query, user_id, size)

    # گل حفاری
    if data.startswith("mud_"):
        return await toggle_mud(query, user_id, data.replace("mud_", ""))

    # تایید اتمام انتخاب گل حفاری
    if data == "mud_done":
        return await ask_water(query, user_id)

    # آیا شیفت دوم هم بگیرد؟
    if data == "need_night":
        return await ask_shift_choice(query, user_id, only_night=True)

    if data == "no_more_shift":
        return await finish_shifts(query, user_id)


# ============================================================
#       نمایش خلاصه هدر
# ============================================================

async def show_header_summary(update_or_query, user_id):
    d = user_data[user_id]
    msg = (
        "✅ هدر گزارش ثبت شد:\n"
        f"• منطقه: {d['region']}\n"
        f"• شماره گمانه: {d['borehole']}\n"
        f"• دستگاه حفاری: {d['rig']}\n"
        f"• زاویه: {d['angle_deg']} درجه\n"
        f"• تاریخ: {d['date']}\n\n"
        "حالا وارد بخش شیفت‌ها می‌شویم."
    )

    try:
        await update_or_query.message.reply_text(msg)
    except:
        await update_or_query.edit_message_text(msg)


# ============================================================
#       انتخاب شیفت
# ============================================================

async def ask_shift_choice(update_or_query, user_id, only_night=False):
    user_states[user_id] = STEP_CHOOSE_SHIFT

    if only_night:
        buttons = [
            [InlineKeyboardButton("شیفت شب", callback_data="shift_night")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("شیفت روز", callback_data="shift_day")],
            [InlineKeyboardButton("شیفت شب", callback_data="shift_night")],
        ]
    markup = InlineKeyboardMarkup(buttons)

    txt = "🔸 لطفاً *شیفت* را انتخاب کنید:"
    await send_msg(update_or_query, txt, markup)


# ============================================================
#       متراژ شروع
# ============================================================

async def ask_start_depth(update_or_query, user_id):
    user_states[user_id] = STEP_START_DEPTH
    shift = user_data[user_id]["current_shift"]
    await send_msg(
        update_or_query,
        f"🔹 *متراژ شروع* شیفت {fa_shift(shift)} را وارد کنید:",
        None
    )


async def handle_start_depth(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except:
        await update.message.reply_text("⛔ مقدار نامعتبر. دوباره وارد کنید.")
        return

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["start"] = val

    user_states[user_id] = STEP_END_DEPTH
    await update.message.reply_text(
        f"🔹 *متراژ پایان* شیفت {fa_shift(shift)} را وارد کنید:",
        parse_mode="Markdown"
    )


# ============================================================
#       متراژ پایان + رفتن به انتخاب سایز با دکمه
# ============================================================

async def handle_end_depth(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except:
        await update.message.reply_text("⛔ مقدار نامعتبر.")
        return

    shift = user_data[user_id]["current_shift"]
    start_val = user_data[user_id]["shifts"][shift].get("start", 0)
    user_data[user_id]["shifts"][shift]["end"] = val

    length = val - start_val
    user_data[user_id]["shifts"][shift]["length"] = length

    user_states[user_id] = STEP_SIZE

    # دکمه‌های سایز حفاری
    buttons = [
        [InlineKeyboardButton("BQ", callback_data="size_BQ")],
        [InlineKeyboardButton("NQ", callback_data="size_NQ")],
        [InlineKeyboardButton("HQ", callback_data="size_HQ")],
        [InlineKeyboardButton("PQ", callback_data="size_PQ")],
    ]
    markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"🔹 متراژ این شیفت = {length:.2f} متر\n\n"
        "لطفاً *سایز حفاری* را انتخاب کنید:",
        reply_markup=markup,
        parse_mode="Markdown"
    )


# ============================================================
#       سایز حفاری
# ============================================================

async def set_size(query, user_id, size):
    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["size"] = size

    # گل حفاری
    user_states[user_id] = STEP_MUD

    mud_buttons = [
        [InlineKeyboardButton("سوپرمیکس", callback_data="mud_super")],
        [InlineKeyboardButton("CMC", callback_data="mud_cmc")],
        [InlineKeyboardButton("خاک اره", callback_data="mud_sawdust")],
        [InlineKeyboardButton("گازوئیل", callback_data="mud_diesel")],
        [InlineKeyboardButton("✅ اتمام انتخاب", callback_data="mud_done")],
    ]
    markup = InlineKeyboardMarkup(mud_buttons)

    await query.edit_message_text(
        "🔹 نوع گل حفاری را انتخاب کنید (می‌توانید چند مورد را انتخاب کنید).\n"
        "برای *حذف* یک مورد، دوباره روی همان دکمه بزنید.\n"
        "در پایان، دکمه «✅ اتمام انتخاب» را بزنید.",
        reply_markup=markup,
        parse_mode="Markdown"
    )


async def toggle_mud(query, user_id, mud_key):
    shift = user_data[user_id]["current_shift"]
    mud_list = user_data[user_id]["shifts"][shift].setdefault("mud", [])

    translate = {
        "super": "سوپرمیکس",
        "cmc": "CMC",
        "sawdust": "خاک اره",
        "diesel": "گازوئیل",
    }

    mud_name = translate[mud_key]

    if mud_name in mud_list:
        mud_list.remove(mud_name)
    else:
        mud_list.append(mud_name)

    await query.edit_message_text(
        f"🔹 انتخاب فعلی: { ' + '.join(mud_list) if mud_list else 'هیچ'}\n"
        "برای حذف یک مورد، دوباره روی همان دکمه بزن.\n"
        "در پایان، دکمه «✅ اتمام انتخاب» را بزن.",
        reply_markup=query.message.reply_markup,
        parse_mode="Markdown"
    )


# ============================================================
#       آب مصرفی
# ============================================================

async def ask_water(query, user_id):
    user_states[user_id] = STEP_WATER
    shift = user_data[user_id]["current_shift"]

    await query.edit_message_text(
        f"🔹 *مقدار آب مصرفی* شیفت {fa_shift(shift)} را وارد کنید (لیتر):",
        parse_mode="Markdown"
    )


async def handle_water(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except:
        await update.message.reply_text("⛔ مقدار آب نامعتبر.")
        return

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["water"] = val

    user_states[user_id] = STEP_DIESEL
    await update.message.reply_text(
        f"🔹 *مقدار گازوئیل* شیفت {fa_shift(shift)} را وارد کنید (لیتر):",
        parse_mode="Markdown"
    )


# ============================================================
#       گازوئیل
# ============================================================

async def handle_diesel(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except:
        await update.message.reply_text("⛔ مقدار گازوئیل نامعتبر.")
        return

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["diesel"] = val

    # بعد از پایان شیفت → پرسیدن درباره شیفت دوم
    user_states[user_id] = STEP_ASK_NEXT_SHIFT

    buttons = [
        [InlineKeyboardButton("شیفت بعدی (شب)", callback_data="need_night")],
        [InlineKeyboardButton("خیر، ادامه بده", callback_data="no_more_shift")],
    ]
    markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "🔸 آیا شیفت دیگری هم باید ثبت شود؟",
        reply_markup=markup
    )


# ============================================================
#   اتمام شیفت‌ها
# ============================================================

async def finish_shifts(query, user_id):
    user_states[user_id] = STEP_SHIFTS_DONE

    d = user_data[user_id]["shifts"]

    total_len = (d["day"].get("length", 0) or 0) + (d["night"].get("length", 0) or 0)
    total_water = (d["day"].get("water", 0) or 0) + (d["night"].get("water", 0) or 0)
    total_diesel = (d["day"].get("diesel", 0) or 0) + (d["night"].get("diesel", 0) or 0)

    msg = (
        "🔰 **جمع‌بندی شیفت‌ها:**\n"
        f"• مجموع متراژ: {total_len:.2f} متر\n"
        f"• مجموع آب مصرفی: {total_water:.2f} لیتر\n"
        f"• مجموع گازوئیل: {total_diesel:.2f} لیتر\n\n"
        "🔜 مرحلهٔ بعد: مسئول شیفت و پرسنل کمکی + توضیحات + PDF"
    )

    await query.edit_message_text(msg, parse_mode="Markdown")


# ============================================================
#   توابع کمکی
# ============================================================

def fa_shift(key):
    return "روز" if key == "day" else "شب"


async def send_msg(update_or_query, text, markup=None):
    try:
        await update_or_query.message.reply_text(text, reply_markup=markup)
    except:
        await update_or_query.edit_message_text(text, reply_markup=markup)


---

الان بعد از Commit:

Railway اگر خودش redeploy نکرد، یه Restart بزن

تو تلگرام، دوباره /start رو بزن و این مسیر رو تست کن:

تا انتخاب شیفت

متراژ شروع و پایان

دیدن متراژ محاسبه‌شده + دکمه‌های سایز

انتخاب سایز

انتخاب و ویرایش گل حفاری (اضافه/حذف با کلیک دوباره)

زدن «✅ اتمام انتخاب» → رفتن به آب

بعد گازوئیل

بعد سؤال شیفت دوم



این‌طوری هم باگ قبلی پوشش داده می‌شه، هم UX می‌شینه سر جاش.

وقتی این نسخه رو تست کردی، بریم سراغ بخش بعدی:
مسئول شیفت، پرسنل کمکی، محاسبه کاراکترهای مجاز توضیحات، و بعدش حمله به PDF نهایی.

