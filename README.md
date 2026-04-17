# LinkedIn Job Scraper + Flask API

Project ini mengambil data lowongan **publik** dari hasil pencarian LinkedIn dan bisa dipakai dalam tiga mode:

1. **CLI / script biasa** → simpan ke file CSV
2. **API Flask** → ambil data job dalam format JSON
3. **Frontend web** → form pencarian dan tampilan hasil langsung di browser

## File
- `linkedin_jobs_scraper.py` — scraper utama
- `app.py` — API Flask
- `requirements.txt` — dependency proyek

## Instalasi
```bash
pip install -r requirements.txt
```

---

## Menjalankan scraper biasa (CLI)

### Contoh ambil lowongan ke CSV
```bash
python linkedin_jobs_scraper.py --keywords "Data Analyst" --location "Indonesia" --pages 3 --output hasil_linkedin.csv
```

### Jika ingin ikut ambil deskripsi job
```bash
python linkedin_jobs_scraper.py --keywords "Software Engineer" --location "Jakarta" --pages 2 --include-description
```

---

## Menjalankan API Flask

Jalankan server:

```bash
python app.py
```

Server akan aktif di:

```text
http://127.0.0.1:5000
```

Frontend web tersedia di root URL berikut:

```text
http://127.0.0.1:5000/
```

Dokumentasi Swagger UI tersedia di:

```text
http://127.0.0.1:5000/apidocs/
```

### Fitur frontend
- Form input `keywords`, `location`, `pages`, `delay`
- Opsi simpan hasil ke CSV
- Tombol ambil data langsung dari API
- Hasil lowongan ditampilkan dalam tabel di browser

### Endpoint yang tersedia

#### 1. Cek health
```http
GET /health
```

Contoh:
```bash
curl http://127.0.0.1:5000/health
```

#### 2. Scrape job LinkedIn
```http
GET /api/scrape-jobs
```

### Query parameter

| Parameter | Wajib | Default | Keterangan |
|---|---:|---|---|
| `keywords` | Ya | - | Kata kunci pencarian job |
| `location` | Tidak | `Indonesia` | Lokasi job |
| `pages` | Tidak | `1` | Jumlah halaman hasil pencarian |
| `delay` | Tidak | `1.0` | Jeda antar request |
| `include_description` | Tidak | `false` | Ambil deskripsi job |
| `output` | Tidak | - | Jika diisi, hasil juga disimpan ke CSV |

### Contoh request API

```bash
curl "http://127.0.0.1:5000/api/scrape-jobs?keywords=Data%20Analyst&location=Indonesia&pages=1"
```

### Contoh request API + simpan ke CSV

```bash
curl "http://127.0.0.1:5000/api/scrape-jobs?keywords=Backend%20Developer&location=Jakarta&pages=2&output=backend_jobs.csv"
```

### Contoh response JSON

```json
{
  "success": true,
  "keywords": "Data Analyst",
  "location": "Indonesia",
  "pages": 1,
  "total": 10,
  "saved_to": null,
  "jobs": [
    {
      "title": "Data Analyst",
      "company": "Contoh Company",
      "location": "Indonesia",
      "posted_time": "1 day ago",
      "job_link": "https://www.linkedin.com/jobs/view/...",
      "description": "..."
    }
  ]
}
```

## Kolom data
- `title`
- `company`
- `location`
- `posted_time`
- `job_link`
- `description`

## Catatan penting
- Gunakan hanya untuk data yang memang **publik** dan pastikan sesuai kebijakan platform.
- Hindari request terlalu cepat; gunakan `delay` agar lebih aman.
- Struktur HTML LinkedIn bisa berubah sewaktu-waktu, jadi selector scraper mungkin perlu disesuaikan lagi nanti.

## 🚀 Deployment ke VPS (Production Setup)

Berikut adalah panduan menjalankan aplikasi ini di server VPS menggunakan **Gunicorn + Nginx + Systemd + CI/CD GitHub Actions**.

---

### 1. Setup awal di VPS (sekali saja)

Masuk ke VPS:

```bash
ssh user@your-vps
```

Install dependency sistem:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
```

---

### 2. Clone repository

```bash
git clone https://github.com/username/repo.git
cd repo
```

---

### 3. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

---

### 4. Test Gunicorn

```bash
gunicorn app:app -b 127.0.0.1:5000
```

Jika berhasil, berarti Flask siap dijalankan di production server.

---

### 5. Setup Systemd Service

Buat file:

```bash
sudo nano /etc/systemd/system/flask-linkedin.service
```

Isi:

```ini
[Unit]
Description=Flask LinkedIn Job Scraper
After=network.target

[Service]
User=your-user
WorkingDirectory=/home/your-user/repo
ExecStart=/home/your-user/repo/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

Restart=always

[Install]
WantedBy=multi-user.target
```

Aktifkan service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-linkedin
sudo systemctl start flask-linkedin
```

Cek status:

```bash
sudo systemctl status flask-linkedin
```

---

### 6. Setup Nginx (Reverse Proxy)

Buat config:

```bash
sudo nano /etc/nginx/sites-available/flask-linkedin
```

Isi:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/flask-linkedin /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

---

### 7. (Opsional) Setup HTTPS

Gunakan Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 🔄 CI/CD Auto Deploy (GitHub Actions)

Tambahkan file:

```
.github/workflows/deploy.yml
```

Isi:

```yaml
name: Deploy Flask to VPS

on:
  push:
    branches:
      - development

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.VPS_KEY }}

      - name: Deploy to VPS
        run: |
          ssh -o StrictHostKeyChecking=no ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} << 'EOF'
            set -e

            cd /home/your-user/repo

            echo "➡️ Pull latest code..."
            git fetch origin
            git reset --hard origin/development

            echo "➡️ Activate virtualenv..."
            source venv/bin/activate

            echo "➡️ Install dependencies..."
            pip install -r requirements.txt

            echo "➡️ Restart service..."
            sudo systemctl restart flask-linkedin

            echo "✅ Deploy selesai!"
          EOF
```

---

## ⚠️ Catatan Deployment

* Gunakan **Gunicorn**, bukan `flask run`
* Jangan stop database/service lain saat deploy (tidak diperlukan)
* Gunakan `git reset --hard` dengan hati-hati (akan overwrite perubahan lokal)
* Gunakan delay pada scraper agar tidak kena rate limit

---

## 🧠 Arsitektur Production

```
User → Nginx → Gunicorn → Flask App → Scraper
```

---

## 🔥 Rekomendasi Upgrade (Next Level)

* Gunakan **Docker** untuk environment yang lebih konsisten
* Tambahkan **logging & monitoring**
* Gunakan **Redis + queue** jika scraping berat
* Implementasi **rate limiting** pada API

---

