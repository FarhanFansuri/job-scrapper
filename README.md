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
