import json
import datetime
import re
import html
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
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
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

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
    if any(kw in combined for kw in ["intern", "internship", "graduate", "trainee", "attachment", "learnership", "student", "apprentice", "bursary"]):
        return "Internship"
    if any(kw in combined for kw in ["general worker", "general assistant", "driver", "cleaner", "assistant", "clerk", "security", "cashier", "packer", "handyman", "housekeeping", "operator", "teller", "chef", "waiter"]):
        return "General"
    return "Full-time"

def fetch_telegram_namibia_jobs():
    """Scrapes 60-100+ live Namibian vacancies, internships & general jobs from t.me/s/NamibianJobOpportunities."""
    results = []
    base_url = "https://t.me/s/NamibianJobOpportunities"
    next_url = base_url

    # Fetch 4 pages (~80+ recent posts)
    for _ in range(4):
        try:
            res = requests.get(next_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                print(f"Telegram status: {res.status_code}")
                break

            page_html = res.text

            # Split into individual message widgets
            messages = re.findall(r'<div class="tgme_widget_message_wrap[^"]*">(.*?)</div>\s*</div>\s*</div>', page_html, re.DOTALL)
            if not messages:
                messages = page_html.split('class="tgme_widget_message_wrap')[1:]

            for msg in messages:
                # Extract post permalink
                link_match = re.search(r'href="(https://t\.me/NamibianJobOpportunities/\d+)"', msg)
                post_url = link_match.group(1) if link_match else base_url

                # Extract exact release date from <time datetime="2026-11-18T...">
                time_match = re.search(r'<time[^>]+datetime="([^"]+)"', msg)
                posted_date = time_match.group(1).split("T")[0] if time_match else str(datetime.date.today())

                # Extract message text
                text_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', msg, re.DOTALL)
                if not text_match:
                    continue

                raw_body = clean_text(text_match.group(1))
                lines = [ln.strip() for ln in raw_body.split("\n") if len(ln.strip()) > 3]
                if not lines:
                    continue

                # Skip pure promo/spam lines and pick the actual job headline
                headline = ""
                for ln in lines:
                    low = ln.lower()
                    if any(skip in low for skip in ["join our", "share this", "welcome to jobportunities", "follow us", "telegram.me"]):
                        continue
                    headline = ln
                    break

                if not headline or len(headline) < 5:
                    continue

                # Check if post includes a direct external application URL (e.g., jobportunities.net, company career page)
                ext_links = re.findall(r'href="(https?://[^"]+)"', text_match.group(1))
                apply_url = post_url
                for ext in ext_links:
                    if "t.me/" not in ext and "telegram.org" not in ext:
                        apply_url = ext
                        break

                title = headline[:95] + ("..." if len(headline) > 95 else "")
                desc = " ".join(lines)[:230]
                if len(" ".join(lines)) > 230:
                    desc += "..."

                location = detect_location(raw_body)
                job_type = detect_job_type(title, desc)

                results.append({
                    "title": title,
                    "company": "Namibia Job Opportunities",
                    "location": location,
                    "type": job_type,
                    "postedDate": posted_date,
                    "desc": desc,
                    "contact": apply_url
                })

            # Find pagination link for older posts (?before=XXXXX)
            before_match = re.search(r'href="(/s/NamibianJobOpportunities\?before=\d+)"', page_html)
            if before_match:
                next_url = "https://t.me" + before_match.group(1)
            else:
                break

        except Exception as e:
            print(f"Telegram fetch error: {e}")
            break

    return results

def fetch_wordpress_namibia_feeds():
    """Fetches Namibian vacancy posts from open WordPress RSS feeds."""
    results = []
    feeds = [
        ("https://www.newsfocusnamibia.com/vacancies/feed/", "News Focus Namibia"),
        ("https://hireresolve.co.za/job-region/namibia-2/feed/", "Hire Resolve Namibia")
    ]
    for feed_url, source_name in feeds:
        try:
            res = requests.get(feed_url, headers=HEADERS, timeout=12)
            if res.status_code == 200 and "<item>" in res.text:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item")[:25]:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    pub_date = (item.findtext("pubDate") or "").strip()
                    desc_raw = clean_text(item.findtext("description") or "")

                    if not title or not link:
                        continue

                    try:
                        posted_date = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d")
                    except Exception:
                        posted_date = str(datetime.date.today())

                    location = detect_location(f"{title} {desc_raw}")
                    results.append({
                        "title": title,
                        "company": source_name,
                        "location": location,
                        "type": detect_job_type(title, desc_raw),
                        "postedDate": posted_date,
                        "desc": (desc_raw[:210] + "...") if len(desc_raw) > 210 else desc_raw,
                        "contact": link
                    })
        except Exception as e:
            print(f"Feed skipped ({feed_url}): {e}")
    return results

def fetch_global_remote_jobs():
    """Fetches remote jobs strictly marked Worldwide/Anywhere so Namibians can apply."""
    results = []
    try:
        res = requests.get("https://remotive.com/api/remote-jobs?limit=25", headers=HEADERS, timeout=15)
        if res.status_code == 200:
            for item in res.json().get("jobs", []):
                region = (item.get("candidate_required_location") or "").lower()
                if not any(ok in region for ok in ["worldwide", "anywhere", "global", "africa"]):
                    continue

                title = clean_text(item.get("title", ""))
                company = clean_text(item.get("company_name", "Global Remote Employer"))
                job_url = item.get("url", "").strip()
                pub = item.get("publication_date", "")
                posted_date = pub.split("T")[0] if "T" in pub else str(datetime.date.today())

                if not title or not job_url:
                    continue

                results.append({
                    "title": f"{title} (Remote - Namibia Eligible)",
                    "company": company,
                    "location": "Remote / Windhoek",
                    "type": detect_job_type(title),
                    "postedDate": posted_date,
                    "desc": f"Work from anywhere in Namibia. Category: {item.get('category', 'Remote')}. Tap 'Apply Here' to apply.",
                    "contact": job_url
                })
    except Exception as e:
        print(f"Remotive fetch error: {e}")
    return results

def get_verified_namibian_portals():
    """Core Namibian portals for students, graduates & non-degree job seekers."""
    today = str(datetime.date.today())
    return [
        {
            "title": "NIEIS National Job & Internship Portal (All 14 Regions)",
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
        }
    ]

def scrape_jobs():
    raw_jobs = []
    raw_jobs.extend(fetch_telegram_namibia_jobs())
    raw_jobs.extend(fetch_wordpress_namibia_feeds())
    raw_jobs.extend(fetch_global_remote_jobs())
    raw_jobs.extend(get_verified_namibian_portals())

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

    # Sort newest posted dates first
    unique_jobs.sort(key=lambda x: x.get("postedDate", ""), reverse=True)

    for idx, job in enumerate(unique_jobs, 1):
        job["id"] = f"job-{idx}"

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(unique_jobs)} unique Namibian jobs to jobs.json!")

if __name__ == "__main__":
    scrape_jobs()
