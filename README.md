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
