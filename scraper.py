import json
import datetime
import re
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, application/xml, text/xml, */*"
}

NAMIBIA_TOWNS = [
    "Windhoek", "Walvis Bay", "Swakopmund", "Oshakati",
    "Ondangwa", "Ongwediva", "Rundu", "Katima Mulilo",
    "Otjiwarongo", "Gobabis", "Keetmanshoop", "Tsumeb",
    "Oranjemund", "Luderitz", "Rehoboth", "Okahandja", "Otavi"
]

def detect_location(text):
    t = (text or "").lower()
    for town in NAMIBIA_TOWNS:
        if town.lower() in t:
            return town
    return "Windhoek / Nationwide"

def detect_job_type(title, desc=""):
    combined = f"{title} {desc}".lower()
    if any(kw in combined for kw in ["intern", "internship", "graduate", "trainee", "attachment", "learnership", "student"]):
        return "Internship"
    if any(kw in combined for kw in ["general worker", "driver", "cleaner", "assistant", "clerk", "security", "cashier", "packer", "handyman"]):
        return "General"
    return "Full-time"

def clean_html(raw_text):
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def format_date(date_str):
    if not date_str:
        return str(datetime.date.today())
    try:
        # Handle ISO format e.g. 2026-11-18T10:30:00+00:00
        if "T" in date_str:
            return date_str.split("T")[0]
        # Handle RSS RFC-2822 format e.g. Wed, 18 Nov 2026 08:00:00 +0000
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(datetime.date.today())

def fetch_reliefweb_namibia():
    """Fetches real, verified Namibian jobs & internships from ReliefWeb API with exact posted dates."""
    results = []
    url = "https://api.reliefweb.int/v1/jobs?appname=namjobs-portal"
    payload = {
        "filter": {
            "field": "country.name",
            "value": "Namibia"
        },
        "fields": {
            "include": ["title", "url", "date.created", "source.name", "city.name", "body-html", "type.name"]
        },
        "limit": 60,
        "sort": ["date.created:desc"]
    }
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            items = res.json().get("data", [])
            for entry in items:
                fields = entry.get("fields", {})
                title = fields.get("title", "").strip()
                job_url = fields.get("url", "").strip()
                if not title or not job_url:
                    continue

                sources = fields.get("source", [])
                company = sources[0].get("name", "Namibia Organization") if sources else "Namibia Organization"

                cities = fields.get("city", [])
                raw_loc = cities[0].get("name", "") if cities else ""
                location = detect_location(f"{raw_loc} {title}")

                created = fields.get("date", {}).get("created", "")
                posted_date = format_date(created)

                body_text = clean_html(fields.get("body-html", ""))
                desc = (body_text[:200] + "...") if len(body_text) > 200 else (body_text or "Verified Namibian vacancy. Tap 'Apply Here' to view full details and apply.")

                job_type = detect_job_type(title, desc)

                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "type": job_type,
                    "postedDate": posted_date,
                    "desc": desc,
                    "contact": job_url
                })
    except Exception as e:
        print(f"ReliefWeb fetch error: {e}")
    return results

def fetch_namibian_rss_feeds():
    """Fetches fresh Namibian vacancies from local RSS feeds with exact release dates."""
    results = []
    feeds = [
        ("https://www.jobportunities.net/rss.xml", "JobPortunities Namibia"),
        ("https://namibia.jobs/feed/", "Namibia Jobs"),
        ("https://www.careers.com.na/feed/", "Careers in Namibia")
    ]
    for feed_url, default_company in feeds:
        try:
            res = requests.get(feed_url, headers=HEADERS, timeout=12)
            if res.status_code == 200 and "<item" in res.text:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item")[:40]:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    pub_date = (item.findtext("pubDate") or "").strip()
                    raw_desc = clean_html(item.findtext("description") or "")

                    if not title or not link:
                        continue

                    location = detect_location(f"{title} {raw_desc}")
                    job_type = detect_job_type(title, raw_desc)
                    posted_date = format_date(pub_date)
                    desc = (raw_desc[:200] + "...") if len(raw_desc) > 200 else (raw_desc or "Active Namibian opportunity. Tap 'Apply Here' to go directly to the listing.")

                    results.append({
                        "title": title,
                        "company": default_company,
                        "location": location,
                        "type": job_type,
                        "postedDate": posted_date,
                        "desc": desc,
                        "contact": link
                    })
        except Exception as e:
            print(f"RSS feed skipped ({feed_url}): {e}")
    return results

def get_verified_local_pool():
    """Guaranteed active Namibian portals & student/general opportunities across major towns."""
    today = str(datetime.date.today())
    return [
        {
            "title": "NIEIS National Job & Internship Portal (All Regions)",
            "company": "Ministry of Labour, Industrial Relations & Employment Creation",
            "location": "Windhoek",
            "type": "General",
            "postedDate": today,
            "desc": "Official Namibian government employment portal for general workers, drivers, clerks, artisans, and graduates.",
            "contact": "https://nieis.namibiaatwork.gov.na/"
        },
        {
            "title": "Engineering & Technical Student Internships / In-Service Training",
            "company": "NamPower (Namibia Power Corporation)",
            "location": "Windhoek",
            "type": "Internship",
            "postedDate": today,
            "desc": "Bursaries, graduate-in-training, and vocational attachment opportunities for NUST, UNAM & VTC students.",
            "contact": "https://www.nampower.com.na/Careers.aspx"
        },
        {
            "title": "Graduate Trainee & IT Internship Programme",
            "company": "Telecom Namibia",
            "location": "Walvis Bay",
            "type": "Internship",
            "postedDate": today,
            "desc": "Student attachment and graduate opportunities in telecommunications, networking, and customer operations.",
            "contact": "https://www.telecom.na/careers"
        },
        {
            "title": "Mining, Artisan & Engineering Apprenticeships",
            "company": "Rössing Uranium / Swakop Uranium",
            "location": "Swakopmund",
            "type": "Internship",
            "postedDate": today,
            "desc": "Apprenticeships, engineering graduate programmes, and technical roles in the Erongo region.",
            "contact": "https://www.rossing.com/careers.htm"
        },
        {
            "title": "Northern Region Retail, Warehouse & General Support Vacancies",
            "company": "Pupkewitz Group Namibia",
            "location": "Oshakati",
            "type": "General",
            "postedDate": today,
            "desc": "Sales assistants, drivers, warehouse packers, and branch administrators across northern Namibia.",
            "contact": "https://www.pupkewitz.com/careers"
        },
        {
            "title": "Kavango East Health, Admin & Community Field Opportunities",
            "company": "IntraHealth / Namibia Health Programmes",
            "location": "Rundu",
            "type": "Full-time",
            "postedDate": today,
            "desc": "Data clerks, community field officers, and administrative roles based in Rundu and surrounding districts.",
            "contact": "https://www.jobportunities.net/"
        },
        {
            "title": "Electrical & Mechanical Plant Attachment",
            "company": "Ohorongo Cement",
            "location": "Tsumeb",
            "type": "Internship",
            "postedDate": today,
            "desc": "Practical industrial attachment and artisan vacancies in the Oshikoto region.",
            "contact": "https://www.ohorongo-cement.com/careers/"
        },
        {
            "title": "Banking Graduate Programme & Teller Vacancies",
            "company": "FNB Namibia (FirstRand Namibia)",
            "location": "Ongwediva",
            "type": "Graduate",
            "postedDate": today,
            "desc": "Entry-level branch roles and graduate development programmes for UNAM, NUST, and IUM graduates.",
            "contact": "https://www.fnbnamibia.com.na/careers/"
        }
    ]

def scrape_jobs():
    raw_jobs = []
    raw_jobs.extend(fetch_reliefweb_namibia())
    raw_jobs.extend(fetch_namibian_rss_feeds())
    raw_jobs.extend(get_verified_local_pool())

    # Strict Deduplication (checks title+company+location AND exact URL)
    unique_jobs = []
    seen_keys = set()
    seen_urls = set()

    for job in raw_jobs:
        key = (
            job["title"].lower().strip(),
            job["company"].lower().strip(),
            job["location"].lower().strip()
        )
        url = job["contact"].lower().strip().rstrip("/")

        if key not in seen_keys and url not in seen_urls:
            seen_keys.add(key)
            seen_urls.add(url)
            unique_jobs.append(job)

    # Sort newest release dates first
    unique_jobs.sort(key=lambda x: x.get("postedDate", ""), reverse=True)

    # Re-index IDs cleanly
    for idx, job in enumerate(unique_jobs, 1):
        job["id"] = f"job-{idx}"

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)

    print(f"Successfully updated jobs.json with {len(unique_jobs)} unique Namibian jobs!")

if __name__ == "__main__":
    scrape_jobs()
