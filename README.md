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

## Deploy ke VPS (panduan agen server) — Ubuntu/Debian

Semua perintah dijalankan sebagai root (atau pakai `sudo`). Bot akan jalan 24/7 via systemd dengan auto-restart.

### 1. Clone & setup environment

```bash
cd /opt
git clone git@github.com:Aqli404/pasti-sukses.git
cd pasti-sukses
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> Jika clone via SSH: generate deploy key dulu (`ssh-keygen -t ed25519 -N "" -f ~/.ssh/github_deploy`) lalu daftarkan `~/.ssh/github_deploy.pub` ke repo → Settings → Deploy keys (read-only cukup). Alternatif: clone via HTTPS + token.

### 2. Simpan token bot

Buat file env (ganti dengan token dari @BotFather):

```bash
cat > /etc/pasti-sukses.env << 'EOF'
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
EOF
chmod 600 /etc/pasti-sukses.env
```

### 3. Buat 2 systemd service

```bash
cat > /etc/systemd/system/pasti-sukses-bot.service << 'EOF'
[Unit]
Description=Pasti Sukses Telegram Bot (polling)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/pasti-sukses.env
WorkingDirectory=/opt/pasti-sukses
ExecStart=/opt/pasti-sukses/.venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/pasti-sukses-scheduler.service << 'EOF'
[Unit]
Description=Pasti Sukses Job Scheduler (scrape + dispatch per jam)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/pasti-sukses.env
WorkingDirectory=/opt/pasti-sukses
ExecStart=/opt/pasti-sukses/.venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Aktifkan & jalankan

```bash
systemctl daemon-reload
systemctl enable --now pasti-sukses-bot pasti-sukses-scheduler
systemctl status pasti-sukses-bot pasti-sukses-scheduler --no-pager
```

### 5. Pantau log

```bash
journalctl -u pasti-sukses-bot -f        # log bot
journalctl -u pasti-sukses-scheduler -f  # log scraper
```

### 6. Update kode di kemudian hari

```bash
cd /opt/pasti-sukses && git pull
systemctl restart pasti-sukses-bot pasti-sukses-scheduler
```

> Database SQLite tersimpan di `/opt/pasti-sukses/pasti_sukses.db`. Backup rutin: `cp pasti_sukses.db /root/backup/$(date +%F).db`

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
└── requirements.txt
```

## Etika & Legal

- Hanya sumber dengan API/RSS resmi atau halaman publik tanpa login
- Setiap lowongan selalu sertakan link ke sumber asli
- Hormati server: delay antar-request, request terbatas
