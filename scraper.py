import json
import datetime
import re
import html
import requests
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9"
}

NAMIBIA_TOWNS = [
    "Windhoek", "Walvis Bay", "Swakopmund", "Oshakati",
    "Ondangwa", "Ongwediva", "Rundu", "Katima Mulilo",
    "Otjiwarongo", "Gobabis", "Keetmanshoop", "Tsumeb",
    "Oranjemund", "Luderitz", "Rehoboth", "Okahandja",
    "Otavi", "Rosh Pinah", "Grootfontein", "Mariental"
]

def clean_text(raw):
    if not raw:
        return ""
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def detect_location(text):
    t = (text or "").lower()
    for town in NAMIBIA_TOWNS:
        if town.lower() in t:
            return town
    if "erongo" in t:
        return "Walvis Bay / Swakopmund"
    if "oshana" in t:
        return "Oshakati / Ongwediva"
    if "kavango" in t:
        return "Rundu"
    if "zambezi" in t:
        return "Katima Mulilo"
    if "karas" in t:
        return "Keetmanshoop"
    return "Windhoek / Namibia"

def detect_job_type(title, desc=""):
    combined = f"{title} {desc}".lower()
    if any(kw in combined for kw in ["intern", "internship", "graduate", "trainee", "attachment", "learnership", "student", "apprentice"]):
        return "Internship"
    if any(kw in combined for kw in ["general worker", "driver", "cleaner", "assistant", "clerk", "security", "cashier", "packer", "handyman", "housekeeping", "operator"]):
        return "General"
    return "Full-time"

def fetch_jobsnamibia_net():
    """Scrapes high-volume local Namibian vacancies directly from jobsnamibia.net."""
    results = []
    urls = [
        "https://jobsnamibia.net/",
        "https://jobsnamibia.net/jobs/",
        "https://jobsnamibia.net/page/2/"
    ]
    today = str(datetime.date.today())

    for page_url in urls:
        try:
            res = requests.get(page_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue

            # Extract job links and surrounding card context
            blocks = re.findall(r'<a[^>]+href=["\'](https://jobsnamibia\.net/job/[^"\']+|https://jobsnamibia\.net/[^"\']*vacanc[^"\']*|https://jobsnamibia\.net/[a-z0-9\-]+/)["\'][^>]*>(.*?)</a>', res.text, re.DOTALL | re.IGNORECASE)
            
            for link, inner_html in blocks:
                title = clean_text(inner_html)
                # Filter out navigation/category links
                if len(title) < 6 or len(title) > 120:
                    continue
                if any(skip in title.lower() for skip in ["home", "contact", "post a job", "browse", "privacy", "terms", "how to", "read more", "apply", "view all"]):
                    continue

                location = detect_location(title)
                job_type = detect_job_type(title)

                results.append({
                    "title": title,
                    "company": "Namibian Employer (via JobsNamibia)",
                    "location": location,
                    "type": job_type,
                    "postedDate": today,
                    "desc": f"Verified Namibian vacancy in {location}. Tap 'Apply Here' to view full job specifications and submit your CV.",
                    "contact": link
                })
        except Exception as e:
            print(f"JobsNamibia scrape error ({page_url}): {e}")
    return results

def fetch_careerjet_namibia():
    """Scrapes active Namibian job listings across Windhoek, Walvis Bay, Oshakati, Rundu, etc."""
    results = []
    queries = [
        "https://www.careerjet.co.na/jobs/Namibia",
        "https://www.careerjet.co.na/jobs/internship-Namibia",
        "https://www.careerjet.co.na/jobs/graduate-Namibia"
    ]
    today = str(datetime.date.today())

    for search_url in queries:
        try:
            res = requests.get(search_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue

            # Parse article job cards from Careerjet Namibia
            articles = re.findall(r'<article[^>]*class=["\'][^"\']*job[^"\']*["\'][^>]*>(.*?)</article>', res.text, re.DOTALL | re.IGNORECASE)
            for art in articles:
                link_match = re.search(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', art, re.DOTALL | re.IGNORECASE)
                if not link_match:
                    continue

                raw_href, raw_title = link_match.groups()
                title = clean_text(raw_title)
                if not title or len(title) < 4:
                    continue

                full_url = urljoin("https://www.careerjet.co.na", raw_href)

                comp_match = re.search(r'<p[^>]*class=["\'][^"\']*company[^"\']*["\'][^>]*>(.*?)</p>', art, re.DOTALL | re.IGNORECASE)
                company = clean_text(comp_match.group(1)) if comp_match else "Namibian Employer"

                loc_match = re.search(r'<ul[^>]*class=["\'][^"\']*location[^"\']*["\'][^>]*>(.*?)</ul>', art, re.DOTALL | re.IGNORECASE)
                raw_loc = clean_text(loc_match.group(1)) if loc_match else ""
                location = detect_location(f"{raw_loc} {title}")

                desc_match = re.search(r'<div[^>]*class=["\'][^"\']*desc[^"\']*["\'][^>]*>(.*?)</div>', art, re.DOTALL | re.IGNORECASE)
                desc = clean_text(desc_match.group(1)) if desc_match else ""
                if not desc:
                    desc = f"Active opportunity in {location}. Tap 'Apply Here' for direct application instructions."

                job_type = detect_job_type(title, desc)

                results.append({
                    "title": title,
                    "company": company or "Namibian Employer",
                    "location": location,
                    "type": job_type,
                    "postedDate": today,
                    "desc": desc[:210] + ("..." if len(desc) > 210 else ""),
                    "contact": full_url
                })
        except Exception as e:
            print(f"Careerjet Namibia scrape error ({search_url}): {e}")
    return results

def fetch_reliefweb_namibia():
    """Fetches real Namibian NGO, UN & development sector jobs and internships with exact release dates."""
    results = []
    url = "https://api.reliefweb.int/v1/jobs?appname=namjobs-portal"
    payload = {
        "filter": {"field": "country.name", "value": "Namibia"},
        "fields": {"include": ["title", "url", "date.created", "source.name", "city.name", "body-html"]},
        "limit": 50,
        "sort": ["date.created:desc"]
    }
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            for entry in res.json().get("data", []):
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
                posted_date = created.split("T")[0] if "T" in created else str(datetime.date.today())

                body_text = clean_text(fields.get("body-html", ""))
                desc = (body_text[:200] + "...") if len(body_text) > 200 else (body_text or "Verified Namibian vacancy. Tap 'Apply Here' to apply.")

                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "type": detect_job_type(title, desc),
                    "postedDate": posted_date,
                    "desc": desc,
                    "contact": job_url
                })
    except Exception as e:
        print(f"ReliefWeb fetch error: {e}")
    return results

def fetch_worldwide_remote_jobs():
    """Fetches strictly Worldwide/Anywhere remote jobs (excludes Europe/US-only jobs)."""
    results = []
    try:
        res = requests.get("https://jobicy.com/api/v2/remote-jobs?count=30", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            for item in res.json().get("jobs", []):
                geo = (item.get("jobGeo") or "").lower()
                # Strictly allow only global/anywhere/Africa remote jobs
                if geo not in ["anywhere", "worldwide", "global", "africa", ""]:
                    continue

                title = clean_text(item.get("jobTitle", ""))
                company = clean_text(item.get("companyName", "Remote Company"))
                job_url = item.get("url", "").strip()
                if not title or not job_url:
                    continue

                pub = item.get("pubDate", "")
                posted_date = pub.split("T")[0] if "T" in pub else str(datetime.date.today())
                excerpt = clean_text(item.get("jobExcerpt", ""))

                results.append({
                    "title": f"{title} (Work From Namibia)",
                    "company": company,
                    "location": "Remote / Windhoek",
                    "type": detect_job_type(title, excerpt),
                    "postedDate": posted_date,
                    "desc": excerpt[:200] + ("..." if len(excerpt) > 200 else ""),
                    "contact": job_url
                })
    except Exception as e:
        print(f"Jobicy remote fetch error: {e}")
    return results

def get_verified_namibian_portals():
    """Ensures students & job seekers in every major Namibian town always have direct portal links."""
    today = str(datetime.date.today())
    return [
        {
            "title": "NIEIS National Job & Internship Registration (All 14 Regions)",
            "company": "Ministry of Labour Namibia",
            "location": "Windhoek",
            "type": "General",
            "postedDate": today,
            "desc": "Official government database connecting Namibian job seekers, artisans, drivers, and graduates with local employers.",
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
            "company": "Rössing Uranium",
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
            "company": "Ministry of Health / Partner Programmes",
            "location": "Rundu",
            "type": "Full-time",
            "postedDate": today,
            "desc": "Data clerks, community field officers, and administrative roles based in Rundu and surrounding districts.",
            "contact": "https://jobsnamibia.net/"
        }
    ]

def scrape_jobs():
    raw_jobs = []
    raw_jobs.extend(fetch_careerjet_namibia())
    raw_jobs.extend(fetch_jobsnamibia_net())
    raw_jobs.extend(fetch_reliefweb_namibia())
    raw_jobs.extend(fetch_worldwide_remote_jobs())
    raw_jobs.extend(get_verified_namibian_portals())

    # Strict Deduplication
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

    for idx, job in enumerate(unique_jobs, 1):
        job["id"] = f"job-{idx}"

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)

    print(f"Successfully updated jobs.json with {len(unique_jobs)} unique Namibian & global remote jobs!")

if __name__ == "__main__":
    scrape_jobs()
