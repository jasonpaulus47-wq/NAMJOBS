import json
import datetime
import requests
import xml.etree.ElementTree as ET

def scrape_namibian_jobs():
    jobs = []
    today = datetime.date.today().strftime("%Y-%m-%d")

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }

    # 1. Pull real Namibian listings via local RSS / job feeds
    rss_sources = [
        {
            "url": "https://www.jobportunities.net/rss.xml",
            "default_company": "Namibian Employer"
        },
        {
            "url": "https://namibia.jobs/feed/",
            "default_company": "Namibia Jobs Portal"
        }
    ]

    for source in rss_sources:
        try:
            resp = requests.get(source["url"], headers=headers, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item")[:25]:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    desc_raw = (item.findtext("description") or "").strip()

                    if not title or not link:
                        continue

                    # Clean HTML tags from description if present
                    clean_desc = desc_raw.split("<")[0].strip()
                    if not clean_desc:
                        clean_desc = "Verified Namibian vacancy. Tap 'Apply Here' to view full requirements and submit your CV."

                    # Detect Namibian town from title or description
                    location = detect_namibia_town(f"{title} {clean_desc}")
                    job_type = detect_job_type(title)

                    jobs.append({
                        "title": title,
                        "company": source["default_company"],
                        "location": location,
                        "type": job_type,
                        "postedDate": today,
                        "desc": clean_desc[:220] + ("..." if len(clean_desc) > 220 else ""),
                        "contact": link
                    })
        except Exception as e:
            print(f"Skipping feed {source['url']}: {e}")

    # 2. Fallback / Local Verified Portals if RSS feeds return empty
    if not jobs:
        jobs = [
            {
                "title": "General Workers, Drivers & Clerks (Ongoing Intake)",
                "company": "NIEIS - Ministry of Labour Namibia",
                "location": "Windhoek / Nationwide",
                "type": "General",
                "postedDate": today,
                "desc": "Register your profile and apply directly for verified government and private sector vacancies across all 14 regions of Namibia.",
                "contact": "https://nieis.namibiaatwork.gov.na/"
            },
            {
                "title": "Graduate Internships & Trainee Programs",
                "company": "Namibia Job Opportunities Portal",
                "location": "Windhoek",
                "type": "Internship",
                "postedDate": today,
                "desc": "Browse the latest internships, vocational attachments, and entry-level roles for Namibian students and graduates.",
                "contact": "https://www.jobportunities.net/"
            },
            {
                "title": "Retail, Logistics & Mining Vacancies",
                "company": "Careers in Namibia",
                "location": "Walvis Bay / Swakopmund / Windhoek",
                "type": "Full-time",
                "postedDate": today,
                "desc": "Direct applications for Erongo and Khomas region employers. Tap 'Apply Here' to go straight to the local listing.",
                "contact": "https://www.careers.com.na/"
            }
        ]

    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(jobs)} verified Namibian jobs to jobs.json")


def detect_namibia_town(text):
    t = text.lower()
    towns = [
        "Windhoek", "Walvis Bay", "Swakopmund", "Oshakati",
        "Ondangwa", "Ongwediva", "Rundu", "Katima Mulilo",
        "Otjiwarongo", "Gobabis", "Keetmanshoop", "Tsumeb",
        "Oranjemund", "Luderitz", "Rehoboth", "Okahandja"
    ]
    for town in towns:
        if town.lower() in t:
            return town
    return "Windhoek / Namibia"


def detect_job_type(title):
    t = title.lower()
    if any(k in t for k in ["intern", "trainee", "graduate", "attachment"]):
        return "Internship"
    if any(k in t for k in ["driver", "cleaner", "assistant", "clerk", "general", "security", "cashier"]):
        return "General"
    return "Full-time"


if __name__ == "__main__":
    scrape_namibian_jobs()
