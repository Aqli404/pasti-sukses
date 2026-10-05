"""Telegram bot: Pasti Sukses - job alert with per-user preferences."""
import html
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
    "agro": "🌱 Pertanian & Pangan",
    "operations": "📦 Operasional & Logistik",
    "other": "🧩 Lainnya",
}
LOC_LABELS = {
    "any": "🌐 Semua Lokasi",
    "remote": "🏠 Remote",
    "jakarta": "🏙 Jakarta",
    "bandung": "🏔 Bandung",
    "surabaya": "🌉 Surabaya",
    "yogyakarta": "🏛 Yogyakarta",
    "semarang": "🌇 Semarang",
    "medan": "🌴 Medan",
    "makassar": "⛵ Makassar",
    "other": "📍 Kota lain",
}

# Plain-text labels (used raw in inline keyboards); always html.escape() them inside message bodies.
FIELD_LABELS_PLAIN = FIELD_LABELS

WELCOME = (
    "🌟 <b>Selamat datang di Pasti Sukses!</b>\n\n"
    "Saya kirimkan lowongan kerja terbaru yang <b>sesuai profilmu</b> — otomatis, gratis.\n\n"
    "Pilih preferensimu sekarang 👇"
)

# In-memory onboarding state (per user, short-lived)
_onboarding: dict[int, dict] = {}


def field_kb() -> InlineKeyboardMarkup:
    # Two buttons per row for a tidy layout with the new categories
    keys = list(FIELD_LABELS.keys())
    rows = []
    for i in range(0, len(keys), 2):
        pair = keys[i:i + 2]
        rows.append([InlineKeyboardButton(FIELD_LABELS[k], callback_data=f"field:{k}") for k in pair])
    return InlineKeyboardMarkup(rows)


def loc_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(LOC_LABELS["remote"], callback_data="loc:remote"),
         InlineKeyboardButton(LOC_LABELS["any"], callback_data="loc:any")],
        [InlineKeyboardButton("🏙 Jakarta", callback_data="loc:jakarta"),
         InlineKeyboardButton("🏔 Bandung", callback_data="loc:bandung")],
        [InlineKeyboardButton("🌉 Surabaya", callback_data="loc:surabaya"),
         InlineKeyboardButton("🏛 Yogyakarta", callback_data="loc:yogyakarta")],
        [InlineKeyboardButton("🌇 Semarang", callback_data="loc:semarang"),
         InlineKeyboardButton("🌴 Medan", callback_data="loc:medan")],
        [InlineKeyboardButton("⛵ Makassar", callback_data="loc:makassar"),
         InlineKeyboardButton("📍 Kota lain", callback_data="loc:other")],
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
          InlineKeyboardButton("🆕 Lowongan Terbaru", callback_data="menu:latest")],
         [InlineKeyboardButton("⭐️ Lowongan Disimpan", callback_data="menu:saved")]]
    )


def job_text(job: dict) -> str:
    """HTML-formatted job card. All dynamic data is escaped."""
    esc = html.escape
    icon = "🏠" if job["is_remote"] else "🏢"
    title = esc(str(job.get("title", "-")))
    company = esc(str(job.get("company") or "-"))
    location = esc(str(job.get("location") or "-"))
    cat = FIELD_LABELS.get(job.get("category", "other"), "🧩 Lainnya")
    source = esc(str(job.get("source", "-")))
    url = esc(str(job.get("url", "")), quote=True)
    return (
        f"{icon} <b>{title}</b>\n"
        f"👔 {company}\n"
        f"📍 {location}\n"
        f"🏷 {cat} | sumber: {source}\n"
        f"🔗 <a href=\"{url}\">Buka lowongan</a>"
    )


def job_kb(job: dict) -> InlineKeyboardMarkup:
    """Inline keyboard for a job card: bookmark button."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⭐️ Simpan Lowongan", callback_data=f"save:{job['id']}")]]
    )


def send_job_message(token: str, chat_id: int, job: dict) -> bool:
    """Blocking dispatch used by scheduler (outside asyncio)."""
    text = job_text(job)
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": {
                "inline_keyboard": [[{
                    "text": "⭐️ Simpan Lowongan",
                    "callback_data": f"save:{job['id']}",
                }]]
            },
        },
        timeout=15,
    )
    return resp.ok


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.username)
    _onboarding[user.id] = {}
    await update.message.reply_text(WELCOME, parse_mode="HTML", reply_markup=field_kb())


async def preferences_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = db.get_preferences(update.effective_user.id)
    if not prefs:
        await start(update, context)
        return
    mode = "🏠 Remote saja" if prefs["is_remote"] else "🏢 Semua tipe kerja"
    esc = html.escape
    await update.message.reply_text(
        "⚙️ <b>Preferensimu saat ini:</b>\n"
        f"• Bidang: {esc(FIELD_LABELS_PLAIN.get(prefs['field'], prefs['field']))}\n"
        f"• Lokasi: {esc(LOC_LABELS.get(prefs['location'], prefs['location']))}\n"
        f"• Tipe: {esc(mode)}\n\nTekan tombol untuk mengubah 👇",
        parse_mode="HTML",
        reply_markup=field_kb(),
    )


async def _send_latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prefs = db.get_preferences(update.effective_user.id)
    category = prefs["field"] if prefs else "any"
    jobs = db.latest_jobs(10, category)
    if not jobs:
        await update.message.reply_text("Belum ada lowongan tersimpan. Coba lagi nanti ya 🙏")
        return
    for j in jobs[:10]:
        await update.message.reply_text(
            job_text(j),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=job_kb(j),
        )


async def latest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_latest(update, context)


async def saved_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    saved = db.get_saved_jobs(user_id)
    if not saved:
        await update.message.reply_text(
            "⭐️ Belum ada lowongan tersimpan.\n"
            "Tekan tombol <b>⭐️ Simpan Lowongan</b> di kartu lowongan untuk menyimpannya di sini.",
            parse_mode="HTML",
        )
        return
    await update.message.reply_text(
        f"⭐️ <b>{len(saved)} lowongan tersimpan:</b>\n(batasi 30 terakhir)",
        parse_mode="HTML",
    )
    for j in saved:
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🗑 Hapus Simpanan", callback_data=f"unsave:{j['id']}")]]
        )
        await update.message.reply_text(
            job_text(j),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=kb,
        )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 <b>Pasti Sukses</b>\n"
        "/start - pilih preferensi\n"
        "/preferences - lihat &amp; ubah preferensi\n"
        "/latest - 10 lowongan terbaru sesuai bidangmu\n"
        "/saved - lihat lowongan yang kamu simpan ⭐️",
        parse_mode="HTML",
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
        await q.edit_message_text(f"🆕 <b>{html.escape(str(len(jobs[:10])))} lowongan terbaru untukmu:</b>", parse_mode="HTML")
        for j in jobs[:10]:
            await context.bot.send_message(
                user_id, job_text(j), parse_mode="HTML",
                disable_web_page_preview=True, reply_markup=job_kb(j),
            )
    elif data == "menu:saved":
        saved = db.get_saved_jobs(user_id)
        if not saved:
            await q.edit_message_text(
                "⭐️ Belum ada lowongan tersimpan.\nTekan tombol <b>⭐️ Simpan Lowongan</b> di kartu lowongan.",
                parse_mode="HTML",
            )
            return
        await q.edit_message_text(f"⭐️ <b>{len(saved)} lowongan tersimpan:</b>", parse_mode="HTML")
        for j in saved:
            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🗑 Hapus Simpanan", callback_data=f"unsave:{j['id']}")]]
            )
            await context.bot.send_message(
                user_id, job_text(j), parse_mode="HTML",
                disable_web_page_preview=True, reply_markup=kb,
            )
    elif data.startswith("save:"):
        try:
            job_id = int(data.split(":", 1)[1])
        except ValueError:
            return
        db.save_job(user_id, job_id)
        try:
            await q.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("✅ Tersimpan — buka /saved", callback_data="noop")]
                     ]
                )
            )
        except Exception:
            pass
    elif data.startswith("unsave:"):
        try:
            job_id = int(data.split(":", 1)[1])
        except ValueError:
            return
        db.unsave_job(user_id, job_id)
        try:
            await q.edit_message_text("🗑 Simpanan dihapus. Ketik /saved untuk lihat daftar terkini.")
        except Exception:
            pass
    elif data == "noop":
        return


async def _finish_onboarding(q, user_id: int) -> None:
    state = _onboarding.get(user_id, {})
    field = state.get("field", "any")
    location = state.get("location", "any")
    is_remote = state.get("is_remote", False)
    if location == "remote":
        is_remote = True
    db.set_preferences(user_id, field, location, is_remote)
    _onboarding.pop(user_id, None)
    esc = html.escape
    mode = "🏠 Remote saja" if is_remote else "🏢 Semua tipe kerja"
    await q.edit_message_text(
        "✅ <b>Preferensi tersimpan!</b>\n"
        f"• Bidang: {esc(FIELD_LABELS_PLAIN.get(field, field))}\n"
        f"• Lokasi: {esc(LOC_LABELS.get(location, location))}\n"
        f"• Tipe: {esc(mode)}\n\n"
        "Lowongan baru yang cocok akan saya kirim otomatis ke sini 🚀\n"
        "Ketik /latest untuk lihat yang tersedia, /saved untuk simpananmu ⭐️",
        parse_mode="HTML",
        reply_markup=done_kb(),
    )


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
    app.add_handler(CommandHandler("saved", saved_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(on_button))
    print("🤖 Pasti Sukses bot jalan... tekan Ctrl+C untuk stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
