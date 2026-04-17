from __future__ import annotations

from dataclasses import asdict
from typing import Any

from flask import Flask, jsonify, render_template, request
from flasgger import Swagger

from linkedin_jobs_scraper import save_to_csv, scrape_linkedin_jobs

app = Flask(__name__)
app.config["SWAGGER"] = {
    "title": "LinkedIn Job Scraper API",
    "uiversion": 3,
}
swagger = Swagger(app)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@app.get("/")
def home() -> Any:
    return render_template("index.html")


@app.get("/api-info")
def api_info() -> Any:
    return jsonify(
        {
            "message": "LinkedIn Job Scraper API aktif.",
            "docs": "/apidocs/",
            "frontend": "/",
            "endpoints": {
                "health": "/health",
                "scrape_jobs": "/api/scrape-jobs?keywords=Data+Analyst&location=Indonesia&pages=1",
            },
        }
    )


@app.get("/health")
def health() -> Any:
    """Health check endpoint.
    ---
    tags:
      - Health
    responses:
      200:
        description: API berjalan normal
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
    """
    return jsonify({"status": "ok"})


@app.get("/api/scrape-jobs")
def scrape_jobs() -> Any:
    """Scrape job publik dari LinkedIn.
    ---
    tags:
      - Jobs
    parameters:
      - name: keywords
        in: query
        type: string
        required: true
        description: Kata kunci pencarian pekerjaan
        example: Data Analyst
      - name: location
        in: query
        type: string
        required: false
        default: Indonesia
        description: Lokasi pencarian
      - name: pages
        in: query
        type: integer
        required: false
        default: 1
        description: Jumlah halaman hasil pencarian
      - name: delay
        in: query
        type: number
        required: false
        default: 1.0
        description: Jeda antar request dalam detik
      - name: include_description
        in: query
        type: boolean
        required: false
        default: false
        description: Ikut mengambil deskripsi lowongan
      - name: output
        in: query
        type: string
        required: false
        description: Nama file CSV output jika ingin disimpan
    responses:
      200:
        description: Berhasil mengambil data lowongan
      400:
        description: Parameter request tidak valid
      500:
        description: Terjadi error saat scraping
    """
    keywords = (request.args.get("keywords") or "").strip()
    location = (request.args.get("location") or "Indonesia").strip()
    output = (request.args.get("output") or "").strip()

    if not keywords:
        return jsonify({"error": "Parameter 'keywords' wajib diisi."}), 400

    try:
        pages = max(1, int(request.args.get("pages", 1)))
        delay = max(0.0, float(request.args.get("delay", 1.0)))
    except ValueError:
        return jsonify({"error": "Parameter 'pages' atau 'delay' tidak valid."}), 400

    include_description = parse_bool(request.args.get("include_description"), default=False)

    try:
        jobs = scrape_linkedin_jobs(
            keywords=keywords,
            location=location,
            pages=pages,
            delay=delay,
            include_description=include_description,
        )

        if output:
            save_to_csv(jobs, output)

        return jsonify(
            {
                "success": True,
                "keywords": keywords,
                "location": location,
                "pages": pages,
                "total": len(jobs),
                "saved_to": output or None,
                "jobs": [asdict(job) for job in jobs],
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
