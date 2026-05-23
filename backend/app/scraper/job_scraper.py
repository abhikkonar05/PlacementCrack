import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import logging
from typing import List, Dict, Any
import time
import warnings

logger = logging.getLogger("app.scraper.job_scraper")
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Global job cache to prevent heavy rate limits
_JOB_CACHE = {
    "data": [],
    "last_fetched": 0
}

# 10 minutes cache duration
CACHE_EXPIRY_SECONDS = 600

FALLBACK_JOBS = [
    {
        "title": "Software Engineer Intern - Full Stack",
        "company": "PlacementCrack Labs",
        "url": "https://weworkremotely.com/remote-jobs/search?term=software+engineer+intern",
        "location": "Remote",
        "logo": "",
        "date": "Curated",
        "type": "Internship"
    },
    {
        "title": "Junior Backend Developer",
        "company": "RemoteFirst Careers",
        "url": "https://weworkremotely.com/remote-jobs/search?term=backend+developer",
        "location": "Remote",
        "logo": "",
        "date": "Curated",
        "type": "Full-Time"
    },
    {
        "title": "Data Science Intern",
        "company": "Analytics Launchpad",
        "url": "https://weworkremotely.com/remote-jobs/search?term=data+science+intern",
        "location": "Remote",
        "logo": "",
        "date": "Curated",
        "type": "Internship"
    },
    {
        "title": "Machine Learning Engineer Intern",
        "company": "ModelOps Academy",
        "url": "https://weworkremotely.com/remote-jobs/search?term=machine+learning+intern",
        "location": "Remote",
        "logo": "",
        "date": "Curated",
        "type": "Internship"
    },
    {
        "title": "AI Application Developer",
        "company": "Applied AI Studio",
        "url": "https://weworkremotely.com/remote-jobs/search?term=ai+developer",
        "location": "Remote",
        "logo": "",
        "date": "Curated",
        "type": "Full-Time"
    }
]

def fetch_wewokremotely_jobs() -> List[Dict[str, Any]]:
    """Scrapes remote job listings from WeWorkRemotely."""
    global _JOB_CACHE
    now = time.time()
    
    # Return cache if valid
    if _JOB_CACHE["data"] and (now - _JOB_CACHE["last_fetched"]) < CACHE_EXPIRY_SECONDS:
        logger.info("Returning cached job listings.")
        return _JOB_CACHE["data"]
        
    url = "https://weworkremotely.com/categories/remote-programming-jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        logger.info(f"Scraping jobs from: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to fetch page. Status: {response.status_code}")
            return _JOB_CACHE["data"] # Return stale cache on error
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_listings = []
        
        # WeWorkRemotely lists jobs inside <section class="jobs"> under <ul> list elements
        sections = soup.find_all('section', class_='jobs')
        
        for section in sections:
            li_elements = section.find_all('li')
            for li in li_elements:
                # Skip pagination and headers
                if 'view-all' in li.get('class', []) or 'post-a-job' in li.get('class', []):
                    continue
                    
                # Extract details
                link_tag = li.find('a', href=True)
                if not link_tag:
                    continue
                    
                # WeWorkRemotely relative link structure
                job_url = "https://weworkremotely.com" + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href']
                
                company_tag = li.find('span', class_='company')
                title_tag = li.find('span', class_='title')
                type_tag = li.find('span', class_='company') # Sometimes lists full-time / part-time
                region_tag = li.find('span', class_='region')
                
                # Some lists have date/region details structured inside another list
                date_tag = li.find('time')
                date_str = date_tag.text.strip() if date_tag else "Recently"
                
                company_name = company_tag.text.strip() if company_tag else "Remote Company"
                job_title = title_tag.text.strip() if title_tag else "Software Engineer"
                region = region_tag.text.strip() if region_tag else "Anywhere (Remote)"
                
                # Check for logo image
                logo_div = li.find('div', class_='flag-logo')
                logo_style = logo_div.get('style', '') if logo_div else ''
                logo_url = ""
                if logo_style and 'url(' in logo_style:
                    start = logo_style.find('url(') + 4
                    end = logo_style.find(')', start)
                    logo_url = logo_style[start:end].replace('"', '').replace("'", "")
                
                job_listings.append({
                    "title": job_title,
                    "company": company_name,
                    "url": job_url,
                    "location": region,
                    "logo": logo_url,
                    "date": date_str,
                    "type": "Full-Time" # Default fallback
                })
                
        if job_listings:
            _JOB_CACHE["data"] = job_listings
            _JOB_CACHE["last_fetched"] = now
            logger.info(f"Successfully scraped {len(job_listings)} jobs.")
            return job_listings
            
    except Exception as e:
        logger.error(f"Error occurred during web scraping: {e}")
        
    return _JOB_CACHE["data"] or FALLBACK_JOBS

def get_jobs_by_role(role: str) -> List[Dict[str, Any]]:
    """Scrapes weworkremotely and filters by candidate job role classification."""
    all_jobs = fetch_wewokremotely_jobs()
    role_key = role.lower().strip()
    
    # Fallback to general list if empty
    if not all_jobs:
        return []
        
    filtered = []
    
    for job in all_jobs:
        title = job["title"].lower()
        
        if role_key == "data science":
            # Match data analysis, statistics, data scientist, data engineering
            if any(term in title for term in ["data", "analyst", "science", "scientist", "analytics", "statistics"]):
                filtered.append(job)
        elif role_key == "ai/ml":
            # Match artificial intelligence, machine learning, vision, deep learning, nlp, neural
            if any(term in title for term in ["ai", "ml", "machine learning", "deep learning", "nlp", "computer vision", "intelligence", "neural", "llm"]):
                filtered.append(job)
        elif role_key == "software development":
            # Exclude specific data/ml roles unless it's general engineering
            if not any(term in title for term in ["data scientist", "deep learning", "machine learning"]):
                filtered.append(job)
        else:
            filtered.append(job)
            
    # If filtered results are too small, append general software development jobs
    if len(filtered) < 3 and role_key in ["data science", "ai/ml"]:
        # Fallback to show related backend or general dev jobs so list isn't empty
        for job in all_jobs:
            title = job["title"].lower()
            if any(term in title for term in ["python", "backend", "go ", "rust", "developer", "engineer"]):
                if job not in filtered:
                    filtered.append(job)
                    
    return filtered
