# 🌟 Pasti Sukses — Bot Telegram Lowongan Kerja

Bot Telegram yang mengirim lowongan kerja terbaru **sesuai preferensi tiap user** — otomatis, gratis.

## Sumber Lowongan (5 sumber, 2 regional)

| Sumber | Region | Metode |
|---|---|---|
| RemoteOK | Global remote | API resmi |
| Remotive | Global remote | API resmi |
| We Work Remotely | Global remote | RSS resmi |
| Kalibrr | 🇮🇩 Indonesia | Scraping HTML |
| Glints | 🇮🇩 Indonesia | API (fallback HTML) |

## Fitur

- `/start` — wizard preferensi (bidang → lokasi → remote/tidak) via tombol
- `/preferences` — lihat & ubah preferensi
- `/latest` — 10 lowongan terbaru sesuai bidang
- Otomatis: scheduler scrape tiap jam → kirim lowongan baru yang cocok ke tiap user (dedup per user)

## Setup Lokal (Windows)

```powershell
cd pasti-sukses
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 1. Bikin bot via @BotFather di Telegram → /newbot → salin token
# 2. Set token & jalankan bot (untuk onboarding user):
$env:BOT_TOKEN = "123456:ABC-DEF..." 
.\.venv\Scripts\python.exe bot.py

# 3. Di terminal lain, jalankan scheduler (scrape + kirim):
$env:BOT_TOKEN = "123456:ABC-DEF..."
.\.venv\Scripts\python.exe scheduler.py
```

## Deploy Gratis (GitHub Actions, Rp0)

1. Push repo ini ke GitHub (private recommended)
2. Di repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `BOT_TOKEN`, Value: token dari @BotFather
3. Workflow `.github/workflows/scheduler.yml` otomatis jalan tiap jam
4. Untuk bot polling 24/7: jalankan `bot.py` di PC/Raspberry Pi, atau deploy ke Railway/Render free tier

> Catatan: GitHub Actions cron biasanya telat 3–10 menit — tidak masalah untuk job alert.

## Struktur

```
pasti-sukses/
├── bot.py          # Telegram bot (onboarding, preferensi, kirim job)
├── scheduler.py    # loop scrape → classify → dedup → dispatch
├── db.py           # SQLite (users, preferences, jobs, deliveries)
├── classifier.py   # kategori bidang via keyword (tanpa API eksternal)
├── scraper/
│   ├── base.py     # HTTP helper + polite delay
│   ├── remoteok.py # API
│   ├── remotive.py # API
│   ├── wwr.py      # RSS
│   ├── kalibrr.py  # HTML
│   └── glints.py   # GraphQL → HTML fallback
└── .github/workflows/scheduler.yml  # cron tiap jam
```

## Etika & Legal

- Hanya sumber dengan API/RSS resmi atau halaman publik tanpa login
- Setiap lowongan selalu sertakan link ke sumber asli
- Hormati server: delay antar-request, request terbatas
