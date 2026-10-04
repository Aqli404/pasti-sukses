"""Telegram bot: Pasti Sukses - job alert with per-user preferences."""
import logging

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import db
from classifier import classify

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

FIELD_LABELS = {
    "any": "🌐 Semua Bidang",
    "it": "💻 IT / Teknologi",
    "design": "🎨 Desain",
    "marketing": "📢 Marketing / Sales",
    "finance": "💰 Finance / Akuntansi",
    "other": "📦 Lainnya",
}
LOC_LABELS = {
    "any": "🌐 Semua Lokasi",
    "remote": "🏠 Remote",
    "jakarta": "🏙 Jakarta",
    "bandung": "🏔 Bandung",
    "surabaya": "🌉 Surabaya",
    "yogyakarta": "culture Yogyakarta",
    "semarang": "🌇 Semarang",
    "medan": "🌴 Medan",
    "makassar": "⛵ Makassar",
    "other": "📍 Kota lain",
}

WELCOME = (
    "🌟 *Selamat datang di Pasti Sukses!*\n\n"
    "Saya kirimkan lowongan kerja terbaru yang *sesuai profilmu* — otomatis, gratis.\n\n"
    "Pilih preferensimu sekarang 👇"
)

# In-memory onboarding state (per user, short-lived)
_onboarding: dict[int, dict] = {}


def field_kb(inline: bool = False) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(FIELD_LABELS[f], callback_data=f"field:{f}")] for f in FIELD_LABELS]
    return InlineKeyboardMarkup(rows)


def loc_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(LOC_LABELS["remote"], callback_data="loc:remote"),
         InlineKeyboardButton(LOC_LABELS["any"], callback_data="loc:any")],
        [InlineKeyboardButton("🏙 Jakarta", callback_data="loc:jakarta"),
         InlineKeyboardButton("🏔 Bandung", callback_data="loc:bandung")],
        [InlineKeyboardButton("🌉 Surabaya", callback_data="loc:surabaya"),
         InlineKeyboardButton("Yogyakarta", callback_data="loc:yogyakarta")],
        [InlineKeyboardButton("🌇 Semarang", callback_data="loc:semarang"),
         InlineKeyboardButton("🌴 Medan", callback_data="loc:medan")],
        [InlineKeyboardButton(LOC_LABELS["makassar"], callback_data="loc:makassar"),
         InlineKeyboardButton(LOC_LABELS["other"], callback_data="loc:other")],
    ]
    return InlineKeyboardMarkup(rows)


def remote_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏠 Hanya remote", callback_data="remote:1"),
             InlineKeyboardButton("🏢 Semua tipe", callback_data="remote:0")],
        ]
    )


def done_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⚙️ Ubah Preferensi", callback_data="menu:edit"),
          InlineKeyboardButton("🆕 Lowongan Terbaru", callback_data="menu:latest")]]
    )


def job_text(job: dict) -> str:
    icon = "🏠" if job["is_remote"] else "🏢"
    return (
        f"{icon} *{job['title']}*\n"
        f"👔 {job['company'] or '-'}\n"
        f"📍 {job['location'] or '-'}\n"
        f"🏷 {FIELD_LABELS.get(job['category'], '📦 Lainnya')} | sumber: {job['source']}\n"
        f"🔗 {job['url']}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.username)
    _onboarding[user.id] = {}
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=field_kb())


async def preferences_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = db.get_preferences(update.effective_user.id)
    if not prefs:
        await start(update, context)
        return
    mode = "🏠 Remote saja" if prefs["is_remote"] else "🏢 Semua tipe kerja"
    await update.message.reply_text(
        "⚙️ *Preferensimu saat ini:*\n"
        f"• Bidang: {FIELD_LABELS.get(prefs['field'], prefs['field'])}\n"
        f"• Lokasi: {LOC_LABELS.get(prefs['location'], prefs['location'])}\n"
        f"• Tipe: {mode}\n\nTekan tombol untuk mengubah 👇",
        parse_mode="Markdown",
        reply_markup=field_kb(),
    )


async def latest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = db.get_preferences(update.effective_user.id)
    category = prefs["field"] if prefs else "any"
    jobs = db.latest_jobs(10, category if category != "other" else "other")
    if not jobs:
        await update.message.reply_text("Belum ada lowongan tersimpan. Coba lagi nanti ya 🙏")
        return
    for j in jobs[:10]:
        await update.message.reply_text(job_text(j), parse_mode="Markdown", disable_web_page_preview=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Pasti Sukses*\n"
        "/start - pilih preferensi\n"
        "/preferences - lihat & ubah preferensi\n"
        "/latest - 10 lowongan terbaru sesuai bidangmu",
        parse_mode="Markdown",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    db.upsert_user(user_id, q.from_user.username)
    data = q.data or ""

    if data.startswith("field:"):
        _onboarding.setdefault(user_id, {})["field"] = data.split(":", 1)[1]
        await q.edit_message_text("Bagus! Sekarang pilih lokasi yang kamu mau 👇", reply_markup=loc_kb())
    elif data.startswith("loc:"):
        loc = data.split(":", 1)[1]
        state = _onboarding.setdefault(user_id, {})
        state["location"] = loc
        if loc == "remote":
            state["is_remote"] = True
            await _finish_onboarding(q, user_id)
        else:
            await q.edit_message_text("Terakhir: kamu cari kerja remote saja atau semua tipe? 👇", reply_markup=remote_kb())
    elif data.startswith("remote:"):
        state = _onboarding.setdefault(user_id, {})
        state["is_remote"] = data.split(":", 1)[1] == "1"
        await _finish_onboarding(q, user_id)
    elif data == "menu:edit":
        await q.edit_message_text("Pilih bidang baru 👇", reply_markup=field_kb())
    elif data == "menu:latest":
        prefs = db.get_preferences(user_id)
        jobs = db.latest_jobs(10, prefs["field"] if prefs else "any")
        if not jobs:
            await q.edit_message_text("Belum ada lowongan tersimpan. Coba lagi nanti ya 🙏")
            return
        await q.edit_message_text(f"🆕 *{len(jobs[:10])} lowongan terbaru untukmu:*", parse_mode="Markdown")
        for j in jobs[:10]:
            await context.bot.send_message(user_id, job_text(j), parse_mode="Markdown", disable_web_page_preview=True)


async def _finish_onboarding(q, user_id: int) -> None:
    state = _onboarding.get(user_id, {})
    field = state.get("field", "any")
    location = state.get("location", "any")
    is_remote = state.get("is_remote", False)
    if location == "remote":
        is_remote = True
    db.set_preferences(user_id, field, location, is_remote)
    _onboarding.pop(user_id, None)
    mode = "🏠 Remote saja" if is_remote else "🏢 Semua tipe kerja"
    await q.edit_message_text(
        "✅ *Preferensi tersimpan!*\n"
        f"• Bidang: {FIELD_LABELS.get(field, field)}\n"
        f"• Lokasi: {LOC_LABELS.get(location, location)}\n"
        f"• Tipe: {mode}\n\n"
        "Lowongan baru yang cocok akan saya kirim otomatis ke sini 🚀\n"
        "Ketik /latest untuk lihat yang sudah tersedia.",
        parse_mode="Markdown",
        reply_markup=done_kb(),
    )


def send_job_message(token: str, chat_id: int, job: dict) -> bool:
    """Blocking dispatch used by scheduler (outside asyncio)."""
    text = job_text(job)
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True},
        timeout=15,
    )
    return resp.ok


def main() -> None:
    import os

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("Set BOT_TOKEN env var dulu. Contoh: set BOT_TOKEN=123:abc")
    db.init_db()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("preferences", preferences_cmd))
    app.add_handler(CommandHandler("latest", latest_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    print("🤖 Pasti Sukses bot jalan... tekan Ctrl+C untuk stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
