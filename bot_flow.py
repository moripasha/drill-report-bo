from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ==========================
# ساختار داده و مراحل
# ==========================

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

# مراحل اطلاعات مسئول/پرسنل برای هر شیفت
STEP_SHIFT_SUPERVISORS = "shift_supervisors"
STEP_SHIFT_HELPERS = "shift_helpers"
STEP_SHIFT_WORKSHOP = "shift_workshop"

# مراحل شیفت‌ها
STEP_CHOOSE_SHIFT = "choose_shift"
STEP_START_DEPTH = "start_depth"
STEP_END_DEPTH = "end_depth"
STEP_SIZE = "size"
STEP_MUD = "mud"
STEP_WATER = "water"
STEP_DIESEL = "diesel"
STEP_SHIFT_REVIEW = "shift_review"
STEP_EDIT_FIELD = "edit_field"

# مرحله توضیحات
STEP_NOTES = "notes"

# مرحله پرسش برای شیفت بعدی
STEP_ASK_NEXT_SHIFT = "ask_next_shift"

# مرحله پایان
STEP_DONE = "done"


# ==========================
# شروع فلو
# ==========================

async def start_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_data[user_id] = {
        "region": None,
        "borehole": None,
        "rig": None,
        "angle_deg": None,
        "date": None,

        "shifts": {
            "day": {
                "supervisors": [],
                "helpers": [],
                "workshop_bosses": [],
                "start": None,
                "end": None,
                "length": None,
                "size": None,
                "mud": [],
                "water": None,
                "diesel": None,
                "notes": "",
            },
            "night": {
                "supervisors": [],
                "helpers": [],
                "workshop_bosses": [],
                "start": None,
                "end": None,
                "length": None,
                "size": None,
                "mud": [],
                "water": None,
                "diesel": None,
                "notes": "",
            },
        },
        "current_shift": None,
        "edit_field": None,  # برای ویرایش متراژ/آب/گازوئیل
    }

    user_states[user_id] = STEP_REGION
    await update.message.reply_text("🔸 لطفاً *منطقه* را وارد کنید:", parse_mode="Markdown")


# ==========================
# مدیریت پیام‌های متنی
# ==========================

async def flow_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if user_id not in user_states:
        await update.message.reply_text("برای شروع /start را بزن.")
        return

    step = user_states[user_id]

    # --- منطقه ---
    if step == STEP_REGION:
        user_data[user_id]["region"] = text
        user_states[user_id] = STEP_BOREHOLE
        return await update.message.reply_text(
            "🔸 شماره گمانه را وارد کنید (ترجیحاً با اعداد انگلیسی):"
        )

    # --- شماره گمانه ---
    if step == STEP_BOREHOLE:
        user_data[user_id]["borehole"] = text
        user_states[user_id] = STEP_RIG

        buttons = [
            [InlineKeyboardButton("DB 1200", callback_data="rig_DB1200")],
            [InlineKeyboardButton("DBC-S15-A", callback_data="rig_DBC")],
        ]
        return await update.message.reply_text(
            "🔸 دستگاه حفاری را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    # --- زاویه ---
    if step == STEP_ANGLE:
        try:
            ang = float(text.replace(",", "."))
        except ValueError:
            return await update.message.reply_text("⛔ زاویه باید عدد باشد.")

        user_data[user_id]["angle_deg"] = ang
        user_states[user_id] = STEP_DATE_YEAR
        return await update.message.reply_text("🔸 سال گزارش:")

    # --- سال ---
    if step == STEP_DATE_YEAR:
        if not text.isdigit():
            return await update.message.reply_text("⛔ سال باید عدد باشد.")
        user_data[user_id]["date_year"] = int(text)
        user_states[user_id] = STEP_DATE_MONTH
        return await update.message.reply_text("🔸 ماه:")

    # --- ماه ---
    if step == STEP_DATE_MONTH:
        if not text.isdigit():
            return await update.message.reply_text("⛔ ماه باید عدد باشد.")
        user_data[user_id]["date_month"] = int(text)
        user_states[user_id] = STEP_DATE_DAY
        return await update.message.reply_text("🔸 روز:")

    # --- روز ---
    if step == STEP_DATE_DAY:
        if not text.isdigit():
            return await update.message.reply_text("⛔ روز باید عدد باشد.")
        day = int(text)
        y = user_data[user_id]["date_year"]
        m = user_data[user_id]["date_month"]

        user_data[user_id]["date"] = f"{day:02d}/{m:02d}/{y}"
        del user_data[user_id]["date_year"]
        del user_data[user_id]["date_month"]

        d = user_data[user_id]
        summary = (
            "✅ هدر ثبت شد:\n"
            f"• منطقه: {d['region']}\n"
            f"• گمانه: {d['borehole']}\n"
            f"• دستگاه: {d['rig']}\n"
            f"• زاویه: {d['angle_deg']} درجه\n"
            f"• تاریخ: {d['date']}\n\n"
            "حالا شیفت را انتخاب کن."
        )
        await update.message.reply_text(summary)
        return await ask_shift_choice(update, user_id)

    # --- مسئول/مسئولین شیفت ---
    if step == STEP_SHIFT_SUPERVISORS:
        shift = user_data[user_id]["current_shift"]
        user_data[user_id]["shifts"][shift]["supervisors"] = split_names(text)
        user_states[user_id] = STEP_SHIFT_HELPERS
        return await update.message.reply_text(
            f"🔹 نام پرسنل کمکی شیفت {fa_shift(shift)} را وارد کن "
            "(اگر چند نفر است، با «،» یا ',' جدا کن):"
        )

    # --- پرسنل کمکی ---
    if step == STEP_SHIFT_HELPERS:
        shift = user_data[user_id]["current_shift"]
        user_data[user_id]["shifts"][shift]["helpers"] = split_names(text)
        user_states[user_id] = STEP_SHIFT_WORKSHOP
        return await update.message.reply_text(
            f"🔹 نام سرپرست کارگاه برای شیفت {fa_shift(shift)} (اگر دو نفرند، با «،» جدا کن):"
        )

    # --- سرپرست کارگاه ---
    if step == STEP_SHIFT_WORKSHOP:
        shift = user_data[user_id]["current_shift"]
        user_data[user_id]["shifts"][shift]["workshop_bosses"] = split_names(text)
        return await ask_start_depth(update, user_id)

    # --- متراژ شروع ---
    if step == STEP_START_DEPTH:
        return await handle_start_depth(update, user_id, text)

    # --- متراژ پایان ---
    if step == STEP_END_DEPTH:
        return await handle_end_depth(update, user_id, text)

    # --- آب ---
    if step == STEP_WATER:
        return await handle_water(update, user_id, text)

    # --- گازوئیل ---
    if step == STEP_DIESEL:
        return await handle_diesel(update, user_id, text)

    # --- ویرایش یک فیلد از شیفت ---
    if step == STEP_EDIT_FIELD:
        return await handle_edit_field(update, user_id, text)

    # --- توضیحات (برای شیفت روز یا شب) ---
    if step == STEP_NOTES:
        return await handle_notes(update, user_id, text)

    if step == STEP_DONE:
        return await update.message.reply_text("گزارش ثبت شده است. برای گزارش جدید /start را بزن.")

    return await update.message.reply_text("⛔ ورودی نامعتبر.")


# ==========================
# Callback ها
# ==========================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_states:
        return await query.edit_message_text("جلسه منقضی شده → /start")

    # --- دستگاه ---
    if data.startswith("rig_"):
        user_data[user_id]["rig"] = "DB 1200" if data == "rig_DB1200" else "DBC-S15-A"
        user_states[user_id] = STEP_ANGLE
        return await query.edit_message_text("🔸 زاویه حفاری:")

    # --- انتخاب شیفت ---
    if data in ("shift_day", "shift_night"):
        shift = "day" if data == "shift_day" else "night"
        user_data[user_id]["current_shift"] = shift
        user_states[user_id] = STEP_SHIFT_SUPERVISORS
        return await query.edit_message_text(
            f"🔹 نام مسئول یا مسئولین شیفت {fa_shift(shift)} را وارد کن "
            "(اگر چند نفرند، با «،» جدا کن):"
        )

    # --- سایز حفاری ---
    if data.startswith("size_"):
        size = data.replace("size_", "")
        return await set_size(query, user_id, size)

    # --- پایان انتخاب گل حفاری ---
    if data == "mud_done":
        return await ask_water(query, user_id)

    # --- انتخاب/حذف گل حفاری ---
    if data.startswith("mud_"):
        return await toggle_mud(query, user_id, data.replace("mud_", ""))

    # --- تأیید شیفت (روز یا شب) ---
    if data in ("shift_ok_day", "shift_ok_night"):
        shift = "day" if data == "shift_ok_day" else "night"
        user_data[user_id]["current_shift"] = shift
        user_states[user_id] = STEP_NOTES
        return await query.edit_message_text(
            f"📝 توضیحات شیفت {fa_shift(shift)} را بنویس."
        )

    # --- ویرایش فیلدهای شیفت ---
    if data in ("edit_start", "edit_end", "edit_water", "edit_diesel"):
        field = data.replace("edit_", "")
        user_data[user_id]["edit_field"] = field
        user_states[user_id] = STEP_EDIT_FIELD

        names = {
            "start": "متراژ شروع",
            "end": "متراژ پایان",
            "water": "مقدار آب مصرفی (لیتر)",
            "diesel": "مقدار گازوئیل (لیتر)",
        }
        shift = user_data[user_id]["current_shift"]
        return await query.edit_message_text(
            f"✏️ مقدار جدید {names[field]} برای شیفت {fa_shift(shift)} را وارد کن:"
        )

    # --- بعد از توضیحات: آیا شیفت شب هم هست؟ ---
    if data == "need_night":
        return await ask_shift_choice(query, user_id, only_night=True)

    if data == "no_more_shift":
        return await finish_shifts_callback(query, user_id)


# ==========================
# انتخاب شیفت
# ==========================

async def ask_shift_choice(update_or_query, user_id, only_night: bool = False):
    user_states[user_id] = STEP_CHOOSE_SHIFT

    if only_night:
        buttons = [[InlineKeyboardButton("شیفت شب", callback_data="shift_night")]]
    else:
        buttons = [
            [InlineKeyboardButton("شیفت روز", callback_data="shift_day")],
            [InlineKeyboardButton("شیفت شب", callback_data="shift_night")],
        ]

    markup = InlineKeyboardMarkup(buttons)
    return await send_msg(update_or_query, "🔸 شیفت را انتخاب کنید:", markup)


# ==========================
# متراژ شروع
# ==========================

async def ask_start_depth(update_or_query, user_id):
    user_states[user_id] = STEP_START_DEPTH
    shift = user_data[user_id]["current_shift"]
    return await send_msg(
        update_or_query,
        f"🔹 متراژ شروع شیفت {fa_shift(shift)}:",
        None,
    )


async def handle_start_depth(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("⛔ مقدار نامعتبر.")

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["start"] = val

    user_states[user_id] = STEP_END_DEPTH
    return await update.message.reply_text(
        f"🔹 متراژ پایان شیفت {fa_shift(shift)}:"
    )


# ==========================
# متراژ پایان + رفتن به سایز
# ==========================

async def handle_end_depth(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("⛔ مقدار نامعتبر.")

    shift = user_data[user_id]["current_shift"]
    start = user_data[user_id]["shifts"][shift]["start"]
    length = val - start

    user_data[user_id]["shifts"][shift]["end"] = val
    user_data[user_id]["shifts"][shift]["length"] = length

    user_states[user_id] = STEP_SIZE

    buttons = [
        [InlineKeyboardButton("BQ", callback_data="size_BQ")],
        [InlineKeyboardButton("NQ", callback_data="size_NQ")],
        [InlineKeyboardButton("HQ", callback_data="size_HQ")],
        [InlineKeyboardButton("PQ", callback_data="size_PQ")],
    ]

    return await update.message.reply_text(
        f"🔹 متراژ این شیفت: {length:.2f} متر\n"
        "سایز حفاری را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ==========================
# انتخاب سایز → گل حفاری
# ==========================

async def set_size(query, user_id, size):
    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["size"] = size

    user_states[user_id] = STEP_MUD

    mud_btns = [
        [InlineKeyboardButton("سوپرمیکس", callback_data="mud_super")],
        [InlineKeyboardButton("CMC", callback_data="mud_cmc")],
        [InlineKeyboardButton("خاک اره", callback_data="mud_sawdust")],
        [InlineKeyboardButton("گازوئیل", callback_data="mud_diesel")],
        [InlineKeyboardButton("✅ اتمام انتخاب", callback_data="mud_done")],
    ]

    return await query.message.reply_text(
        "🔹 گل حفاری را انتخاب کنید (چندتایی).\n"
        "برای حذف، دوباره همان گزینه را بزنید.\n"
        "در پایان، «اتمام انتخاب» را بزنید.",
        reply_markup=InlineKeyboardMarkup(mud_btns),
    )


# ==========================
# انتخاب / حذف گل حفاری
# ==========================

async def toggle_mud(query, user_id, key):
    shift = user_data[user_id]["current_shift"]
    lst = user_data[user_id]["shifts"][shift].setdefault("mud", [])

    translate = {
        "super": "سوپرمیکس",
        "cmc": "CMC",
        "sawdust": "خاک اره",
        "diesel": "گازوئیل",
    }

    val = translate[key]

    if val in lst:
        lst.remove(val)
    else:
        lst.append(val)

    mud_btns = [
        [InlineKeyboardButton("سوپرمیکس", callback_data="mud_super")],
        [InlineKeyboardButton("CMC", callback_data="mud_cmc")],
        [InlineKeyboardButton("خاک اره", callback_data="mud_sawdust")],
        [InlineKeyboardButton("گازوئیل", callback_data="mud_diesel")],
        [InlineKeyboardButton("✅ اتمام انتخاب", callback_data="mud_done")],
    ]

    return await query.edit_message_text(
        f"🔹 انتخاب فعلی: { ' + '.join(lst) if lst else 'هیچ'}\n"
        "برای حذف، دوباره روی همان گزینه بزن.\n"
        "در پایان، «اتمام انتخاب» را بزن.",
        reply_markup=InlineKeyboardMarkup(mud_btns),
    )


# ==========================
# آب مصرفی
# ==========================

async def ask_water(query, user_id):
    user_states[user_id] = STEP_WATER
    shift = user_data[user_id]["current_shift"]

    return await query.edit_message_text(
        f"🔹 مقدار آب مصرفی شیفت {fa_shift(shift)} (لیتر):"
    )


async def handle_water(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("⛔ مقدار آب نامعتبر.")

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["water"] = val

    user_states[user_id] = STEP_DIESEL
    return await update.message.reply_text(
        f"🔹 مقدار گازوئیل شیفت {fa_shift(shift)} (لیتر):"
    )


# ==========================
# گازوئیل → خلاصه و امکان ویرایش
# ==========================

async def handle_diesel(update, user_id, text):
    try:
        val = float(text.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("⛔ مقدار گازوئیل نامعتبر.")

    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["diesel"] = val

    # بعد از کامل شدن داده‌ها، خلاصه شیفت و دکمه‌های ویرایش
    return await ask_shift_review(update, user_id)


async def ask_shift_review(update_or_query, user_id):
    shift = user_data[user_id]["current_shift"]
    sh = user_data[user_id]["shifts"][shift]
    user_states[user_id] = STEP_SHIFT_REVIEW

    sup = "، ".join(sh["supervisors"]) if sh["supervisors"] else "-"
    helpers = "، ".join(sh["helpers"]) if sh["helpers"] else "-"
    bosses = "، ".join(sh["workshop_bosses"]) if sh["workshop_bosses"] else "-"
    mud = " + ".join(sh["mud"]) if sh["mud"] else "-"

    msg = (
        f"🔍 خلاصه شیفت {fa_shift(shift)}:\n"
        f"• مسئول(ین) شیفت: {sup}\n"
        f"• پرسنل کمکی: {helpers}\n"
        f"• سرپرست کارگاه: {bosses}\n"
        f"• متراژ شروع: {sh['start']} متر\n"
        f"• متراژ پایان: {sh['end']} متر\n"
        f"• متراژ شیفت: {sh['length']:.2f} متر\n"
        f"• سایز حفاری: {sh['size']}\n"
        f"• گل حفاری: {mud}\n"
        f"• آب مصرفی: {sh['water']} لیتر\n"
        f"• گازوئیل: {sh['diesel']} لیتر\n\n"
        "اگر موردی اشتباه است، گزینه ویرایش را بزن."
    )

    buttons = [
        [
            InlineKeyboardButton(
                f"✅ تأیید شیفت {fa_shift(shift)}",
                callback_data=f"shift_ok_{shift}",
            )
        ],
        [
            InlineKeyboardButton("✏️ ویرایش متراژ شروع", callback_data="edit_start"),
            InlineKeyboardButton("✏️ ویرایش متراژ پایان", callback_data="edit_end"),
        ],
        [
            InlineKeyboardButton("✏️ ویرایش آب", callback_data="edit_water"),
            InlineKeyboardButton("✏️ ویرایش گازوئیل", callback_data="edit_diesel"),
        ],
    ]

    markup = InlineKeyboardMarkup(buttons)
    return await send_msg(update_or_query, msg, markup)


# ==========================
# ویرایش فیلدهای شیفت
# ==========================

async def handle_edit_field(update: Update, user_id: int, text: str):
    field = user_data[user_id].get("edit_field")
    shift = user_data[user_id]["current_shift"]
    sh = user_data[user_id]["shifts"][shift]

    try:
        val = float(text.replace(",", "."))
    except ValueError:
        return await update.message.reply_text("⛔ مقدار عددی نامعتبر است. دوباره وارد کن.")

    if field == "start":
        sh["start"] = val
        if sh["end"] is not None:
            sh["length"] = sh["end"] - sh["start"]
    elif field == "end":
        sh["end"] = val
        if sh["start"] is not None:
            sh["length"] = sh["end"] - sh["start"]
    elif field == "water":
        sh["water"] = val
    elif field == "diesel":
        sh["diesel"] = val

    user_states[user_id] = STEP_SHIFT_REVIEW
    return await ask_shift_review(update, user_id)


# ==========================
# توضیحات هر شیفت
# ==========================

async def handle_notes(update: Update, user_id: int, text: str):
    shift = user_data[user_id]["current_shift"]
    user_data[user_id]["shifts"][shift]["notes"] = text

    # اگر شیفت روز است → بپرس آیا شیفت شب هم هست؟
    if shift == "day":
        user_states[user_id] = STEP_ASK_NEXT_SHIFT
        buttons = [
            [InlineKeyboardButton("بله، شیفت شب داریم", callback_data="need_night")],
            [InlineKeyboardButton("خیر، فقط همین شیفت", callback_data="no_more_shift")],
        ]
        markup = InlineKeyboardMarkup(buttons)
        return await update.message.reply_text(
            "آیا شیفت شب هم باید ثبت شود؟",
            reply_markup=markup,
        )

    # اگر شیفت شب است → مستقیم جمع‌بندی نهایی
    if shift == "night":
        return await finish_shifts_text(update, user_id)


# ==========================
# پایان شیفت‌ها + پیش‌نمایش
# ==========================

def build_shifts_summary(user_id: int) -> str:
    d = user_data[user_id]["shifts"]

    total_len = (d["day"]["length"] or 0) + (d["night"]["length"] or 0)
    total_water = (d["day"]["water"] or 0) + (d["night"]["water"] or 0)
    total_diesel = (d["day"]["diesel"] or 0) + (d["night"]["diesel"] or 0)

    msg = (
        "🔰 **جمع‌بندی شیفت‌ها:**\n"
        f"• مجموع متراژ = {total_len:.2f} متر\n"
        f"• مجموع آب = {total_water:.2f} لیتر\n"
        f"• مجموع گازوئیل = {total_diesel:.2f} لیتر"
    )
    return msg


def build_full_preview(user_id: int) -> str:
    d = user_data[user_id]
    s = d["shifts"]

    lines = []
    lines.append("🧾 پیش‌نمایش گزارش روزانه")
    lines.append("────────────────────")
    lines.append(f"منطقه: {d['region']}")
    lines.append(f"شماره گمانه: {d['borehole']}")
    lines.append(f"دستگاه حفاری: {d['rig']}")
    lines.append(f"زاویه: {d['angle_deg']} درجه")
    lines.append(f"تاریخ: {d['date']}")
    lines.append("")

    for key in ("day", "night"):
        sh = s[key]
        if sh["start"] is None:
            continue

        lines.append(f"─── شیفت {fa_shift(key)} ───")
        sup = "، ".join(sh["supervisors"]) if sh["supervisors"] else "-"
        helpers = "، ".join(sh["helpers"]) if sh["helpers"] else "-"
        bosses = "، ".join(sh["workshop_bosses"]) if sh["workshop_bosses"] else "-"
        mud = " + ".join(sh["mud"]) if sh["mud"] else "-"

        lines.append(f"مسئول(ین) شیفت: {sup}")
        lines.append(f"پرسنل کمکی: {helpers}")
        lines.append(f"سرپرست کارگاه: {bosses}")
        lines.append(f"متراژ شروع: {sh['start']} متر")
        lines.append(f"متراژ پایان: {sh['end']} متر")
        lines.append(f"متراژ شیفت: {sh['length']:.2f} متر")
        lines.append(f"سایز حفاری: {sh['size']}")
        lines.append(f"گل حفاری: {mud}")
        lines.append(f"آب مصرفی: {sh['water']} لیتر")
        lines.append(f"گازوئیل: {sh['diesel']} لیتر")
        lines.append(f"توضیحات شیفت {fa_shift(key)}:")
        lines.append(sh["notes"] or "-")
        lines.append("")

    return "\n".join(lines)


async def finish_shifts_callback(query, user_id):
    user_states[user_id] = STEP_DONE
    summary = build_shifts_summary(user_id)
    preview = build_full_preview(user_id)

    await query.edit_message_text(summary, parse_mode="Markdown")
    await query.message.reply_text(preview)
    await query.message.reply_text(
        "✅ گزارش ثبت شد.\n"
        "در نسخهٔ بعدی، تولید و ارسال PDF روی قالب فرم هم اضافه می‌شود."
    )


async def finish_shifts_text(update, user_id):
    user_states[user_id] = STEP_DONE
    summary = build_shifts_summary(user_id)
    preview = build_full_preview(user_id)

    await update.message.reply_text(summary, parse_mode="Markdown")
    await update.message.reply_text(preview)
    await update.message.reply_text(
        "✅ گزارش ثبت شد.\n"
        "در نسخهٔ بعدی، تولید و ارسال PDF روی قالب فرم هم اضافه می‌شود."
    )


# ==========================
# ابزارها
# ==========================

def fa_shift(key: str) -> str:
    return "روز" if key == "day" else "شب"


def split_names(raw: str):
    parts = [p.strip() for p in raw.replace("،", ",").split(",")]
    return [p for p in parts if p]


async def send_msg(update_or_query, text: str, markup=None):
    try:
        return await update_or_query.message.reply_text(text, reply_markup=markup)
    except AttributeError:
        return await update_or_query.edit_message_text(text, reply_markup=markup)
