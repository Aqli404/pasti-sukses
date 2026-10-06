"""Generate marketing/tiktok/tt_0*.svg — 4-slide TikTok carousel (1080x1920).

Branding: @rosif.ai — "build with AI".
CTA: GitHub repository + follow (no bot link, per brief).

Safe zone (TikTok overlays UI on top of photo posts):
  x 70..880  (right rail: like/share/comment ~900..1080)
  y 230..1560 (top bar <200, caption/music >1600)
marketing/check_layout.py enforces these bounds for tt_*.svg.
"""
import base64
import io
import os

import qrcode

REPO = "https://github.com/Aqli404/pasti-sukses"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFS = """
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0A1930"/>
      <stop offset="0.55" stop-color="#0D2A52"/>
      <stop offset="1" stop-color="#123C6E"/>
    </linearGradient>
    <linearGradient id="cta" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#38BDF8"/>
    </linearGradient>
    <radialGradient id="glow1" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#38BDF8" stop-opacity="0.32"/>
      <stop offset="1" stop-color="#38BDF8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#2563EB" stop-opacity="0.30"/>
      <stop offset="1" stop-color="#2563EB" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="72" height="72" patternUnits="userSpaceOnUse">
      <path d="M 72 0 L 0 0 0 72" fill="none" stroke="#38BDF8" stroke-opacity="0.07" stroke-width="1.5"/>
    </pattern>
"""


def qr_data_uri() -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2
    )
    qr.add_data(REPO)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="#0A1930", back_color="white").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def shell(body: str, glow1: tuple, glow2: tuple) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1920" viewBox="0 0 1080 1920">
  <defs>{DEFS}</defs>
  <rect width="1080" height="1920" fill="url(#bg)"/>
  <rect width="1080" height="1920" fill="url(#grid)"/>
  <circle cx="{glow1[0]}" cy="{glow1[1]}" r="430" fill="url(#glow1)"/>
  <circle cx="{glow2[0]}" cy="{glow2[1]}" r="470" fill="url(#glow2)"/>
  <g stroke="#38BDF8" stroke-opacity="0.20" stroke-width="2" fill="none">
    <path d="M -40 170 L 150 110 L 360 175"/>
  </g>
  <g fill="#38BDF8">
    <circle cx="150" cy="110" r="6" fill-opacity="0.7"/>
  </g>
  <g font-family="Segoe UI, Arial, sans-serif" text-anchor="middle">
{body}
  </g>
</svg>
"""


def indicator(n: int) -> str:
    return (
        f'<text x="830" y="242" font-size="26" font-weight="600" '
        f'fill="#7DD3FC" fill-opacity="0.9">{n}/4</text>'
    )


def swipe(y: int = 1500) -> str:
    return (
        f'<text x="540" y="{y}" font-size="38" font-weight="700" '
        f'fill="#7DD3FC">Swipe →</text>'
    )


def slide1() -> str:
    return shell(
        f"""
    {indicator(1)}
    <rect x="280" y="262" width="520" height="66" rx="33" fill="#38BDF8" fill-opacity="0.14" stroke="#38BDF8" stroke-opacity="0.55" stroke-width="2"/>
    <text x="540" y="306" font-size="30" font-weight="600" fill="#7DD3FC" letter-spacing="1">BUILD WITH AI · @rosif.ai</text>

    <text x="540" y="530" font-size="70" font-weight="800" fill="#FFFFFF">PROJECT PERTAMA</text>
    <text x="540" y="630" font-size="70" font-weight="800" fill="#FFFFFF">GUE DI GITHUB 🚀</text>
    <rect x="440" y="678" width="200" height="8" rx="4" fill="#38BDF8"/>

    <text x="540" y="800" font-size="46" font-weight="600" fill="#BAE6FD">dibangun 100% bareng AI</text>
    <text x="540" y="870" font-size="36" fill="#93C5FD">open source di GitHub 🐙</text>

    <rect x="195" y="970" width="690" height="430" rx="36" fill="#0F2B52" fill-opacity="0.9" stroke="#38BDF8" stroke-opacity="0.35" stroke-width="2"/>
    <text x="260" y="1065" font-size="40" font-weight="700" fill="#FFFFFF" text-anchor="start">Isi carousel ini 👇</text>
    <text x="260" y="1155" font-size="36" fill="#BAE6FD" text-anchor="start">1. Kenapa gue bikin bot kerja</text>
    <text x="260" y="1235" font-size="36" fill="#BAE6FD" text-anchor="start">2. Gimana AI bantu codingnya</text>
    <text x="260" y="1315" font-size="36" fill="#BAE6FD" text-anchor="start">3. Kode lengkap — gratis, buka</text>

    {swipe()}""",
        (120, 300),
        (960, 1700),
    )


def slide2() -> str:
    return shell(
        f"""
    {indicator(2)}
    <text x="540" y="440" font-size="80" font-weight="800" fill="#FFFFFF">CAPEK SCROLL</text>
    <text x="540" y="545" font-size="80" font-weight="800" fill="#FFFFFF">CARI KERJA?</text>
    <rect x="440" y="592" width="200" height="8" rx="4" fill="#38BDF8"/>
    <text x="540" y="700" font-size="48" font-weight="600" fill="#BAE6FD">biarin bot yang nyariin 🤖</text>

    <rect x="150" y="790" width="730" height="400" rx="36" fill="#0F2B52" fill-opacity="0.9" stroke="#38BDF8" stroke-opacity="0.35" stroke-width="2"/>
    <text x="210" y="895" font-size="42" text-anchor="start" fill="#FFFFFF">✅  Lowongan baru <tspan font-weight="700" fill="#7DD3FC">tiap jam</tspan></text>
    <text x="210" y="995" font-size="42" text-anchor="start" fill="#FFFFFF">✅  Sesuai <tspan font-weight="700" fill="#7DD3FC">bidang &amp; lokasimu</tspan></text>
    <text x="210" y="1095" font-size="42" text-anchor="start" fill="#FFFFFF">✅  Langsung ke <tspan font-weight="700" fill="#7DD3FC">Telegram</tspan></text>
    <text x="210" y="1170" font-size="30" text-anchor="start" fill="#93C5FD">gratis · tanpa daftar ribet</text>

    <text x="540" y="1340" font-size="33" font-weight="600" fill="#7DD3FC">6 sumber lowongan: global + Indonesia 🌏</text>

    {swipe()}""",
        (940, 320),
        (140, 1680),
    )


def slide3() -> str:
    chips1 = [
        (200, "Python 3.11"),
        (435, "Telegram Bot"),
        (670, "SQLite"),
    ]
    chips2 = [(317, "6 Scrapers"), (552, "Scheduler")]
    chip_svg = ""
    for x, label in chips1:
        chip_svg += (
            f'\n    <rect x="{x}" y="700" width="210" height="80" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>'
            f'\n    <text x="{x + 105}" y="752" font-size="26" font-weight="600" fill="#BAE6FD">{label}</text>'
        )
    for x, label in chips2:
        chip_svg += (
            f'\n    <rect x="{x}" y="810" width="210" height="80" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>'
            f'\n    <text x="{x + 105}" y="862" font-size="26" font-weight="600" fill="#BAE6FD">{label}</text>'
        )
    return shell(
        f"""
    {indicator(3)}
    <text x="540" y="440" font-size="70" font-weight="800" fill="#FFFFFF">PAIRING SAMA AI</text>
    <rect x="440" y="488" width="200" height="8" rx="4" fill="#38BDF8"/>
    <text x="540" y="590" font-size="36" fill="#93C5FD">ide, arsitektur &amp; debug — bareng AI</text>
{chip_svg}

    <rect x="200" y="960" width="680" height="180" rx="28" fill="#0F2B52" fill-opacity="0.9" stroke="#38BDF8" stroke-opacity="0.35" stroke-width="2"/>
    <text x="310" y="1050" font-size="56" font-weight="800" fill="#7DD3FC">183</text>
    <text x="310" y="1100" font-size="26" fill="#CBD5E1">lowongan</text>
    <text x="540" y="1050" font-size="56" font-weight="800" fill="#7DD3FC">8</text>
    <text x="540" y="1100" font-size="26" fill="#CBD5E1">kategori</text>
    <text x="770" y="1050" font-size="56" font-weight="800" fill="#7DD3FC">24/7</text>
    <text x="770" y="1100" font-size="26" fill="#CBD5E1">jalan terus</text>

    <text x="540" y="1300" font-size="36" font-weight="600" fill="#BAE6FD">scheduler scrape &amp; kirim tiap jam ⏰</text>
    <text x="540" y="1370" font-size="34" fill="#93C5FD">VPS murah + systemd — auto-restart</text>

    {swipe(1500)}""",
        (950, 280),
        (130, 1720),
    )


def slide4() -> str:
    return shell(
        f"""
    {indicator(4)}
    <text x="540" y="430" font-size="80" font-weight="800" fill="#FFFFFF">OPEN SOURCE</text>
    <rect x="440" y="478" width="200" height="8" rx="4" fill="#38BDF8"/>
    <text x="540" y="575" font-size="42" font-weight="600" fill="#BAE6FD">baca, fork, pelajari — bebas</text>

    <rect x="340" y="640" width="400" height="430" rx="32" fill="#FFFFFF"/>
    <image x="375" y="680" width="330" height="330" xlink:href="{qr_data_uri()}"/>
    <text x="540" y="1050" font-size="26" font-weight="600" fill="#0C2344">Scan → buka repository</text>

    <text x="540" y="1145" font-size="34" font-weight="700" fill="#E0F2FE">github.com/Aqli404/pasti-sukses</text>

    <rect x="195" y="1215" width="690" height="100" rx="50" fill="url(#cta)"/>
    <text x="540" y="1279" font-size="40" font-weight="800" fill="#FFFFFF">⭐ Star &amp; fork kalau bermanfaat</text>

    <rect x="195" y="1360" width="690" height="100" rx="50" fill="#38BDF8" fill-opacity="0.14" stroke="#38BDF8" stroke-opacity="0.55" stroke-width="2"/>
    <text x="540" y="1424" font-size="40" font-weight="800" fill="#7DD3FC">FOLLOW @rosif.ai ✨</text>

    <text x="540" y="1545" font-size="30" fill="#93C5FD">project AI berikutnya menyusul</text>""",
        (930, 300),
        (150, 1650),
    )


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, fn in enumerate([slide1, slide2, slide3, slide4], start=1):
        path = os.path.join(OUT_DIR, f"tt_{i:02d}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", os.path.basename(path))


if __name__ == "__main__":
    main()
