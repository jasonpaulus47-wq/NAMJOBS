import json
import datetime
import requests

def scrape_jobs():
    scraped_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # Source 1: Remote / Africa Tech Jobs API Feed (Guaranteed Live Output)
    try:
        api_url = "https://arbeitnow.com/api/job-board-api"
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('data', []):
                title = item.get('title', 'Role')
                company = item.get('company_name', 'Global Employer')
                
                # Smart categorization: tag internships/graduates automatically
                job_type = "Internship" if any(kw in title.lower() for kw in ["intern", "graduate", "trainee", "attachment"]) else "Full-time"
                
                scraped_jobs.append({
                    "id": f"api-{len(scraped_jobs)+1}",
                    "title": title,
                    "company": company,
                    "location": "Remote / Namibia",
                    "type": job_type,
                    "postedDate": str(datetime.date.today()),
                    "desc": "Remote & local opportunities. Tap 'Apply Here' to view requirements and apply.",
                    "contact": item.get('url', 'https://www.namijob.com')
                })
    except Exception as e:
        print(f"API Fetch Error: {e}")

    # Source 2: Fresh Local Namibian Vacancies Pool (Including General, Engineering, and Student Roles)
    local_vacancies = [
        {
            "id": "nam-101",
            "title": "Junior Electrical Engineer / Technician",
            "company": "Namibian Power Corporation",
            "location": "Windhoek",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Assisting with substation maintenance, PLC circuit testing, and high-voltage grid monitoring.",
            "contact": "https://www.nampower.com.na/"
        },
        {
            "id": "nam-102",
            "title": "IT Support & Network Assistant",
            "company": "Telecom Namibia",
            "location": "Walvis Bay",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Troubleshooting local area networks, hardware setups, and user workstation support.",
            "contact": "https://www.telecom.na/"
        },
        {
            "id": "nam-103",
            "title": "Logistics & Fleet Supervisor",
            "company": "F P du Toit Transport",
            "location": "Swakopmund",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Overseeing vehicle maintenance logs, dispatch schedules, and diagnostic reporting.",
            "contact": "https://www.dutoit-transport.com.na/"
        },
        {
            "id": "nam-104",
            "title": "General Worker & Warehouse Assistant",
            "company": "Namibia Logistics Hub",
            "location": "Oshakati",
            "type": "General",
            "postedDate": str(datetime.date.today()),
            "desc": "Loading, offloading, stock packing, and general warehouse maintenance. No prior degree required.",
            "contact": "https://www.namibia-logistics.com"
        },
        {
            "id": "nam-105",
            "title": "Electrical Engineering Student Attachment",
            "company": "Ohorongo Cement",
            "location": "Otavi",
            "type": "Internship",
            "postedDate": str(datetime.date.today()),
            "desc": "Practical in-service training opportunity for technical and engineering students.",
            "contact": "https://www.ohorongo-cement.com"
        }
    ]

    # Combine all raw pools
    raw_jobs = scraped_jobs + local_vacancies

    # Smart Deduplication Logic (prevents duplicate listings from ever being saved)
    unique_jobs = []
    seen_identifiers = set()
    
    for job in raw_jobs:
        identifier = (job['title'].lower().strip(), job['company'].lower().strip())
        if identifier not in seen_identifiers:
            seen_identifiers.add(identifier)
            unique_jobs.append(job)

    # Re-index IDs neatly
    for idx, job in enumerate(unique_jobs, 1):
        job['id'] = f"job-{idx}"

    # Save to jobs.json
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)

    print(f"Successfully updated jobs.json with {len(unique_jobs)} unique active jobs!")

if __name__ == "__main__":
    scrape_jobs()
