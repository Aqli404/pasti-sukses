"""Generate marketing/poster_c.svg (GitHub branding story poster) with an embedded QR."""
import base64
import io

import qrcode

REPO = "https://github.com/Aqli404/pasti-sukses"

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
qr.add_data(REPO)
qr.make(fit=True)
buf = io.BytesIO()
qr.make_image(fill_color="#0A1930", back_color="white").save(buf, format="PNG")
qr_b64 = base64.b64encode(buf.getvalue()).decode()

SVG = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="1920" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#050D1A"/>
      <stop offset="0.5" stop-color="#0C2344"/>
      <stop offset="1" stop-color="#10315E"/>
    </linearGradient>
    <linearGradient id="cta" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="1" stop-color="#38BDF8"/>
    </linearGradient>
    <radialGradient id="glowTop" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#38BDF8" stop-opacity="0.32"/>
      <stop offset="1" stop-color="#38BDF8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowBot" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#2563EB" stop-opacity="0.30"/>
      <stop offset="1" stop-color="#2563EB" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="54" height="54" patternUnits="userSpaceOnUse">
      <path d="M 54 0 L 0 0 0 54" fill="none" stroke="#38BDF8" stroke-opacity="0.06" stroke-width="1.5"/>
    </pattern>
  </defs>

  <rect width="1080" height="1920" fill="url(#bg)"/>
  <rect width="1080" height="1920" fill="url(#grid)"/>
  <circle cx="900" cy="260" r="430" fill="url(#glowTop)"/>
  <circle cx="180" cy="1720" r="470" fill="url(#glowBot)"/>

  <!-- GitHub-style branch decoration, safely away from text -->
  <g stroke="#38BDF8" stroke-opacity="0.20" stroke-width="2" fill="none">
    <path d="M -40 210 L 140 140 L 340 205"/>
    <path d="M 1020 1500 L 1075 1450 L 1140 1500"/>
  </g>
  <g fill="#38BDF8">
    <circle cx="140" cy="140" r="6" fill-opacity="0.7"/>
    <circle cx="1075" cy="1450" r="5" fill-opacity="0.55"/>
  </g>

  <g font-family="Segoe UI, Arial, sans-serif" text-anchor="middle">
    <!-- top badge -->
    <rect x="290" y="150" width="500" height="66" rx="33" fill="#38BDF8" fill-opacity="0.14" stroke="#38BDF8" stroke-opacity="0.55" stroke-width="2"/>
    <text x="540" y="194" font-size="30" font-weight="600" fill="#7DD3FC" letter-spacing="1">PROJECT PERTAMA DI GITHUB 🚀</text>

    <!-- headline -->
    <text x="540" y="400" font-size="84" font-weight="800" fill="#FFFFFF">PASTI SUKSES</text>
    <text x="540" y="500" font-size="84" font-weight="800" fill="#7DD3FC">OPEN SOURCE</text>
    <rect x="440" y="545" width="200" height="8" rx="4" fill="#38BDF8"/>

    <!-- sub -->
    <text x="540" y="640" font-size="46" font-weight="600" fill="#BAE6FD">Bot Telegram lowongan kerja 🤖</text>
    <text x="540" y="700" font-size="34" fill="#93C5FD">Python · dibangun dari nol, jalan 24/7</text>

    <!-- tech stack chips -->
    <g font-size="30" font-weight="600">
      <rect x="150" y="770" width="230" height="76" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>
      <text x="265" y="820" fill="#BAE6FD">Python 3.11</text>
      <rect x="425" y="770" width="230" height="76" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>
      <text x="540" y="820" fill="#BAE6FD">Telegram Bot</text>
      <rect x="700" y="770" width="230" height="76" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>
      <text x="815" y="820" fill="#BAE6FD">SQLite</text>
      <rect x="285" y="880" width="230" height="76" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>
      <text x="400" y="930" fill="#BAE6FD">6 Scrapers</text>
      <rect x="565" y="880" width="230" height="76" rx="20" fill="#12325C" stroke="#38BDF8" stroke-opacity="0.30" stroke-width="1.5"/>
      <text x="680" y="930" fill="#BAE6FD">Scheduler</text>
    </g>

    <!-- stat strip -->
    <rect x="150" y="1010" width="780" height="150" rx="28" fill="#0F2B52" fill-opacity="0.9" stroke="#38BDF8" stroke-opacity="0.35" stroke-width="2"/>
    <text x="320" y="1085" font-size="58" font-weight="800" fill="#7DD3FC">183</text>
    <text x="320" y="1130" font-size="26" fill="#CBD5E1">lowongan terindeks</text>
    <text x="760" y="1085" font-size="58" font-weight="800" fill="#7DD3FC">8</text>
    <text x="760" y="1130" font-size="26" fill="#CBD5E1">kategori bidang</text>

    <!-- QR card -->
    <rect x="340" y="1200" width="400" height="440" rx="32" fill="#FFFFFF"/>
    <image x="375" y="1235" width="330" height="330" xlink:href="data:image/png;base64,{qr_b64}"/>
    <text x="540" y="1610" font-size="26" font-weight="600" fill="#0C2344">Scan → buka repository</text>

    <!-- CTA text -->
    <text x="540" y="1770" font-size="38" font-weight="800" fill="#FFFFFF">github.com/Aqli404/pasti-sukses</text>
    <text x="540" y="1830" font-size="28" fill="#7DD3FC" fill-opacity="0.85">⭐ Star kalau bermanfaat · fork &amp; kontribusi terbuka</text>
  </g>
</svg>
'''

with open("marketing/poster_c.svg", "w", encoding="utf-8") as f:
    f.write(SVG)
print("poster_c.svg written,", len(SVG), "bytes")