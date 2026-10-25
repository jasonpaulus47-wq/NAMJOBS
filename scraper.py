import json
import datetime
import requests
import xml.etree.ElementTree as ET

def scrape_jobs():
    scraped_jobs = []
    
    # Target public RSS / XML feeds for live Namibian vacancies
    rss_urls = [
        "https://www.namijob.com/rss.xml",
        "https://namibianjob.com/feed/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for feed_url in rss_urls:
        try:
            res = requests.get(feed_url, headers=headers, timeout=12)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall('.//item'):
                    title = item.find('title')
                    link = item.find('link')
                    
                    title_text = title.text.strip() if title is not None and title.text else "Namibian Vacancy"
                    link_url = link.text.strip() if link is not None and link.text else "https://www.namijob.com"
                    
                    scraped_jobs.append({
                        "id": f"live-{len(scraped_jobs)+1}",
                        "title": title_text,
                        "company": "Verified Employer",
                        "location": "Namibia",
                        "type": "Full-time",
                        "postedDate": str(datetime.date.today()),
                        "desc": "Tap 'Apply Now' to view full details, requirements, and official application instructions.",
                        "contact": link_url
                    })
        except Exception as e:
            print(f"Feed error for {feed_url}: {e}")

    # Fallback backup listings (Kept at the bottom so feed is never empty)
    fallback_jobs = [
        {
            "id": "starter-1",
            "title": "Engineering Technician (Transmission)",
            "company": "NamPower (Pty) Ltd",
            "location": "Windhoek",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Responsible for installation and maintenance of PLC systems and HF/VHF radio equipment.",
            "contact": "https://www.nampower.com.na/Careers.aspx"
        },
        {
            "id": "starter-2",
            "title": "Store Cashier & Customer Assistant",
            "company": "BUCO Building Supplies",
            "location": "Windhoek",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Handling POS systems, payment processing, customer inquiries, and stock reconciliation.",
            "contact": "https://www.buco.co.za/"
        }
    ]

    # Combine scraped online jobs at top + fallbacks at bottom
    final_jobs = scraped_jobs + fallback_jobs

    # Write directly to jobs.json
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(final_jobs, f, indent=2)
    
    print(f"Successfully saved {len(final_jobs)} jobs to jobs.json!")

if __name__ == "__main__":
    scrape_jobs()
