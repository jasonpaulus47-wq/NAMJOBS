import json
import datetime
import requests
from bs4 import BeautifulSoup

def scrape_jobs():
    jobs = []
    
    # 1. Fallback / Starter Jobs to keep feed populated
    starter_jobs = [
        {
            "id": "1",
            "title": "Engineering Technician (Transmission)",
            "company": "NamPower (Pty) Ltd",
            "location": "Windhoek",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Responsible for installation and maintenance of PLC systems and HF/VHF radio equipment.",
            "contact": "https://www.nampower.com.na/Careers.aspx"
        },
        {
            "id": "2",
            "title": "Store Cashier & Customer Assistant",
            "company": "BUCO Building Supplies",
            "location": "Windhoek",
            "type": "Full-time",
            "postedDate": str(datetime.date.today()),
            "desc": "Handling POS systems, payment processing, customer inquiries, and stock reconciliation.",
            "contact": "https://www.buco.co.za/"
        }
    ]
    
    jobs.extend(starter_jobs)
    
    # 2. Scrape Live Web Data
    try:
        url = "https://www.namijob.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for job article cards
            articles = soup.find_all('article')
            
            for index, article in enumerate(articles[:10]):
                title_elem = article.find(['h2', 'h3', 'a'])
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    link = title_elem.get('href') if title_elem.name == 'a' else article.find('a', href=True)
                    link_url = link['href'] if link and 'href' in link.attrs else "https://www.namijob.com/"
                    
                    jobs.append({
                        "id": f"scraped-{index+1}",
                        "title": title_text,
                        "company": "Verified Employer",
                        "location": "Namibia",
                        "type": "Full-time",
                        "postedDate": str(datetime.date.today()),
                        "desc": "Click apply to view full requirements and submission details for this vacancy.",
                        "contact": link_url
                    })
    except Exception as e:
        print(f"Scraper notice: {e}")
        
    # Write updated listings directly to jobs.json
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2)

if __name__ == "__main__":
    scrape_jobs()
