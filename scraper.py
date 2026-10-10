import json
import datetime
import requests
from bs4 import BeautifulSoup

def fetch_scraped_jobs():
    scraped_jobs = []
    today_str = datetime.date.today().isoformat()
    
    url = "https://jobsnamibia.net/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('h2', limit=10)
            
            job_id = int(datetime.datetime.now().timestamp())
            for idx, article in enumerate(articles):
                a_tag = article.find('a')
                if a_tag and a_tag.text:
                    title = a_tag.text.strip()
                    link = a_tag.get('href', url)
                    
                    scraped_jobs.append({
                        "id": job_id + idx,
                        "title": title,
                        "company": "JobsNamibia Portal",
                        "location": "Windhoek / Various",
                        "type": "Full-time",
                        "postedDate": today_str,
                        "desc": f"New vacancy: {title}. Click below to apply on official portal.",
                        "contact": link
                    })
    except Exception as e:
        print(f"Scraping error: {e}")
        
    return scraped_jobs

def update_jobs_file():
    new_jobs = fetch_scraped_jobs()
    if not new_jobs:
        print("No new jobs found or request failed.")
        return

    try:
        with open('jobs.json', 'r') as f:
            existing_jobs = json.load(f)
    except Exception:
        existing_jobs = []

    existing_titles = {j['title'].lower() for j in existing_jobs}
    added_count = 0
    
    for job in new_jobs:
        if job['title'].lower() not in existing_titles:
            existing_jobs.insert(0, job)
            added_count += 1

    existing_jobs = existing_jobs[:50]

    with open('jobs.json', 'w') as f:
        json.dump(existing_jobs, f, indent=2)

    print(f"Successfully added {added_count} new job(s)!")

if __name__ == '__main__':
    update_jobs_file()
