from __future__ import annotations

import argparse
import csv
import re
import time
from dataclasses import asdict, dataclass
from html import unescape
from typing import Any, List
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    BeautifulSoup = None
    Tag = Any

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
}


@dataclass
class JobItem:
    title: str
    company: str
    location: str
    posted_time: str
    job_link: str
    description: str = ""


def clean_text(tag: Any) -> str:
    if not tag:
        return ""
    if hasattr(tag, "get_text"):
        return " ".join(tag.get_text(" ", strip=True).split())
    return strip_tags(str(tag))


def strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return " ".join(unescape(text).split())


# LinkedIn geoId mapping for better location filtering
# LinkedIn needs geoId parameter for accurate geographic filtering
LOCATION_GEO_IDS: dict[str, str] = {
    "indonesia": "102478259",
    "malaysia": "106808692",
    "singapore": "102454443",
    "india": "102713980",
    "united states": "103644278",
    "australia": "101452733",
    "japan": "101355337",
    "germany": "101282230",
    "united kingdom": "101165590",
    "thailand": "105146118",
    "philippines": "103121230",
    "vietnam": "104195383",
}


def get_geo_id(location: str) -> str | None:
    """Return LinkedIn geoId for common location names."""
    loc = location.strip().lower()
    for key, geo_id in LOCATION_GEO_IDS.items():
        if key in loc or loc in key:
            return geo_id
    return None


def build_search_url(keywords: str, location: str, start: int) -> str:
    geo_id = get_geo_id(location)
    base = (
        "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search/"
        f"?keywords={quote_plus(keywords)}&location={quote_plus(location)}&start={start}"
    )
    if geo_id:
        base += f"&geoId={geo_id}"
    return base


def download_html(url: str) -> str:
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_job_description(url: str) -> str:
    try:
        html = download_html(url)
    except Exception:
        return ""

    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        description_tag = (
            soup.select_one("div.show-more-less-html__markup")
            or soup.select_one("div.description__text")
            or soup.select_one("section.show-more-less-html")
        )
        return clean_text(description_tag)

    match = re.search(
        r'<div[^>]*class="[^"]*(show-more-less-html__markup|description__text)[^"]*"[^>]*>(.*?)</div>',
        html,
        flags=re.S | re.I,
    )
    return strip_tags(match.group(2)) if match else ""


def parse_job_cards_with_bs4(html: str, include_description: bool, delay: float) -> List[JobItem]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[JobItem] = []

    for card in soup.select("li"):
        title_tag = card.select_one("h3.base-search-card__title") or card.select_one("h3")
        company_tag = card.select_one("h4.base-search-card__subtitle") or card.select_one("h4")
        location_tag = card.select_one("span.job-search-card__location") or card.select_one(
            ".job-search-card__location"
        )
        time_tag = card.select_one("time")
        link_tag = card.select_one("a.base-card__full-link, a.base-search-card__full-link, a")

        title = clean_text(title_tag)
        company = clean_text(company_tag)
        location = clean_text(location_tag)
        posted_time = clean_text(time_tag)
        job_link = link_tag.get("href", "").split("?")[0].strip() if link_tag else ""

        if not title or not job_link:
            continue

        description = ""
        if include_description:
            description = fetch_job_description(job_link)
            time.sleep(delay)

        jobs.append(
            JobItem(
                title=title,
                company=company,
                location=location,
                posted_time=posted_time,
                job_link=job_link,
                description=description,
            )
        )

    return jobs


def extract_first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.S | re.I)
        if match:
            return strip_tags(match.group(1))
    return ""


def parse_job_cards_with_regex(html: str, include_description: bool, delay: float) -> List[JobItem]:
    jobs: List[JobItem] = []
    cards = re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S | re.I)

    for card in cards:
        title = extract_first(
            [
                r'<h3[^>]*class="[^"]*base-search-card__title[^"]*"[^>]*>(.*?)</h3>',
                r"<h3[^>]*>(.*?)</h3>",
            ],
            card,
        )
        company = extract_first(
            [
                r'<h4[^>]*class="[^"]*base-search-card__subtitle[^"]*"[^>]*>(.*?)</h4>',
                r"<h4[^>]*>(.*?)</h4>",
            ],
            card,
        )
        location = extract_first(
            [r'<span[^>]*class="[^"]*job-search-card__location[^"]*"[^>]*>(.*?)</span>'],
            card,
        )
        posted_time = extract_first([r"<time[^>]*>(.*?)</time>"], card)

        link_match = re.search(r'href="([^"]+)"', card, flags=re.I)
        job_link = unescape(link_match.group(1)).split("?")[0].strip() if link_match else ""

        if not title or not job_link:
            continue

        description = ""
        if include_description:
            description = fetch_job_description(job_link)
            time.sleep(delay)

        jobs.append(
            JobItem(
                title=title,
                company=company,
                location=location,
                posted_time=posted_time,
                job_link=job_link,
                description=description,
            )
        )

    return jobs


def parse_job_cards(html: str, include_description: bool, delay: float) -> List[JobItem]:
    if BeautifulSoup is not None:
        return parse_job_cards_with_bs4(html, include_description, delay)
    return parse_job_cards_with_regex(html, include_description, delay)


# Countries that need city-based searching because LinkedIn guest API
# does not filter well with just the country name.
COUNTRY_CITY_FALLBACKS: dict[str, list[str]] = {
    "indonesia": ["Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Medan", "Semarang"],
}


def scrape_linkedin_jobs(
    keywords: str,
    location: str,
    pages: int,
    delay: float,
    include_description: bool,
) -> List[JobItem]:
    # If location is a country that needs city-based searching, fan out
    loc_lower = location.strip().lower()
    if loc_lower in COUNTRY_CITY_FALLBACKS:
        cities = COUNTRY_CITY_FALLBACKS[loc_lower]
        all_jobs: List[JobItem] = []
        seen_links: set[str] = set()
        per_city_pages = max(1, pages)

        for city in cities:
            city_jobs = _scrape_single_location(
                keywords, city, per_city_pages, delay, include_description
            )
            for job in city_jobs:
                if job.job_link not in seen_links:
                    seen_links.add(job.job_link)
                    all_jobs.append(job)

        print(f"Total dari {len(cities)} kota: {len(all_jobs)} job unik")
        return all_jobs

    return _scrape_single_location(keywords, location, pages, delay, include_description)


def _scrape_single_location(
    keywords: str,
    location: str,
    pages: int,
    delay: float,
    include_description: bool,
) -> List[JobItem]:
    all_jobs: List[JobItem] = []
    seen_links: set[str] = set()

    for page in range(pages):
        start = page * 25
        url = build_search_url(keywords, location, start)
        print(f"Mengambil data halaman {page + 1}: {url}")

        try:
            html = download_html(url)
        except Exception as exc:
            print(f"Gagal mengambil data pada halaman {page + 1}: {exc}")
            break

        page_jobs = parse_job_cards(html, include_description, delay)
        if not page_jobs:
            print("Tidak ada job yang ditemukan lagi. Proses dihentikan.")
            break

        for job in page_jobs:
            if job.job_link in seen_links:
                continue
            seen_links.add(job.job_link)
            all_jobs.append(job)

        print(f"- Ditemukan {len(page_jobs)} job pada halaman {page + 1}")
        time.sleep(delay)

    return all_jobs


def save_to_csv(jobs: List[JobItem], output_file: str) -> None:
    with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["title", "company", "location", "posted_time", "job_link", "description"],
        )
        writer.writeheader()
        for job in jobs:
            writer.writerow(asdict(job))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scraper lowongan kerja publik LinkedIn ke file CSV."
    )
    parser.add_argument("--keywords", required=True, help="Kata kunci pencarian. Contoh: Data Analyst")
    parser.add_argument("--location", default="Indonesia", help="Lokasi pencarian. Default: Indonesia")
    parser.add_argument("--pages", type=int, default=2, help="Jumlah halaman yang diambil. Default: 2")
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Jeda antar request dalam detik. Default: 2.0",
    )
    parser.add_argument(
        "--output",
        default="linkedin_jobs.csv",
        help="Nama file output CSV. Default: linkedin_jobs.csv",
    )
    parser.add_argument(
        "--include-description",
        action="store_true",
        help="Ikut ambil deskripsi singkat dari tiap lowongan (lebih lambat).",
    )
    args = parser.parse_args()

    jobs = scrape_linkedin_jobs(
        keywords=args.keywords,
        location=args.location,
        pages=args.pages,
        delay=args.delay,
        include_description=args.include_description,
    )

    if not jobs:
        print("Tidak ada data job yang berhasil diambil.")
        return

    save_to_csv(jobs, args.output)
    print(f"Selesai. Total {len(jobs)} job disimpan ke: {args.output}")


if __name__ == "__main__":
    main()
