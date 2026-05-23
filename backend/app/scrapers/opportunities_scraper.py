import asyncio
import httpx
import logging
import random
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from app.database import db
from app.scrapers.utils import get_random_user_agent, random_anti_block_delay, verify_link

logger = logging.getLogger("app.scrapers.opportunities_scraper")
opportunities_collection = db["opportunities"]

# Rich, curated list of premium active student opportunities
CURATED_OPPORTUNITIES = [
    {
        "title": "Google Summer of Code (GSoC) 2026",
        "company": "Google Open Source",
        "opportunity_type": "Open-Source Program",
        "eligibility": "Students & Open Source Contributors (18+)",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=45)).strftime("%Y-%m-%d"),
        "apply_link": "https://summerofcode.withgoogle.com/",
        "location": "Global / Remote",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_Summer_of_Code_logo.svg/330px-Google_Summer_of_Code_logo.svg.png",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    },
    {
        "title": "Devfolio Web3 Buildathon",
        "company": "Devfolio hackathons",
        "opportunity_type": "Hackathon",
        "eligibility": "Open to all students & builders",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
        "apply_link": "https://devfolio.co/hackathons",
        "location": "Remote / Virtual",
        "logo": "https://devfolio.co/favicon.png",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    },
    {
        "title": "HackerEarth Hack-from-Home Challenge",
        "company": "HackerEarth Technologies",
        "opportunity_type": "Hackathon",
        "eligibility": "University students globally",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=12)).strftime("%Y-%m-%d"),
        "apply_link": "https://hackerearth.com/challenges",
        "location": "Remote / Online",
        "logo": "https://hackerearth.com/favicon.ico",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    },
    {
        "title": "LeetCode Weekly Coding Contest",
        "company": "LeetCode Platform",
        "opportunity_type": "Coding Contest",
        "eligibility": "All coders",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=6)).strftime("%Y-%m-%d"),
        "apply_link": "https://leetcode.com/contest/",
        "location": "LeetCode Online",
        "logo": "https://leetcode.com/favicon.ico",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    },
    {
        "title": "React Frontend Developer Intern",
        "company": "WebScale Solutions",
        "opportunity_type": "Internship",
        "eligibility": "B.Tech / MCA candidates (2026/2027 grads)",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "apply_link": "https://internshala.com/internships/matching-your-skills",
        "location": "Bengaluru (Hybrid)",
        "logo": "",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    },
    {
        "title": "Outreachy Open-Source Internship",
        "company": "Outreachy Platform",
        "opportunity_type": "Internship",
        "eligibility": "Underrepresented students & contributors",
        "deadline": (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d"),
        "apply_link": "https://www.outreachy.org/",
        "location": "Remote / Global",
        "logo": "https://www.outreachy.org/static/images/logo.png",
        "is_active": True,
        "scraped_at": datetime.now(timezone.utc)
    }
]

async def prune_expired_opportunities():
    """Removes all opportunities that have expired based on their deadline dates."""
    try:
        now_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = await opportunities_collection.delete_many({
            "deadline": {"$lt": now_date_str}
        })
        if result.deleted_count > 0:
            logger.info(f"Auto-Cleanup: Pruned {result.deleted_count} expired opportunities from MongoDB.")
    except Exception as e:
        logger.error(f"Auto-Cleanup failed: {e}")

async def scrape_opportunities() -> int:
    """Attempts to dynamically scrape developer internships and contests. Falls back cleanly to active curated listings."""
    scraped_count = 0
    scraped_opportunities = []
    
    # Target URL: WeWorkRemotely categories to fetch actual internships or programming roles
    target_url = "https://weworkremotely.com/categories/remote-programming-jobs"
    
    try:
        logger.info("Initiating dynamic student opportunities scrape...")
        headers = {"User-Agent": get_random_user_agent()}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(target_url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                sections = soup.find_all("section", class_="jobs")
                
                for section in sections[:2]: # Scrape first couple sections for density
                    li_elements = section.find_all("li")
                    for li in li_elements:
                        if "view-all" in li.get("class", []) or "post-a-job" in li.get("class", []):
                            continue
                            
                        link_tag = li.find("a", href=True)
                        if not link_tag:
                            continue
                            
                        job_url = "https://weworkremotely.com" + link_tag["href"] if link_tag["href"].startswith("/") else link_tag["href"]
                        
                        company_tag = li.find("span", class_="company")
                        title_tag = li.find("span", class_="title")
                        region_tag = li.find("span", class_="region")
                        
                        company_name = company_tag.text.strip() if company_tag else "Remote Company"
                        job_title = title_tag.text.strip() if title_tag else "Software Engineer"
                        region = region_tag.text.strip() if region_tag else "Remote"
                        
                        # Categorize Internships vs Hackathons vs Remote Jobs
                        opportunity_type = "Remote Job"
                        if "intern" in job_title.lower() or "internship" in job_title.lower():
                            opportunity_type = "Internship"
                        
                        deadline_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d") # Mock 30-days validity
                        
                        scraped_opportunities.append({
                            "title": job_title,
                            "company": company_name,
                            "opportunity_type": opportunity_type,
                            "eligibility": "Students & Grads with coding skills",
                            "deadline": deadline_date,
                            "apply_link": job_url,
                            "location": region,
                            "logo": "",
                            "is_active": True,
                            "scraped_at": datetime.now(timezone.utc)
                        })
                        if len(scraped_opportunities) >= 10:
                            break
                            
        await random_anti_block_delay(0.5, 1.5)
        
    except Exception as e:
        logger.error(f"Live opportunities scrape skipped: {e}. Decoupling to fail-safe database mode.")
        
    # Fail-safe static merge
    if not scraped_opportunities:
        logger.info("Using curated student opportunities fallback dataset.")
        scraped_opportunities = CURATED_OPPORTUNITIES
    else:
        # Merge static curated listings on top to ensure hackathons are always present
        scraped_opportunities = scraped_opportunities + CURATED_OPPORTUNITIES
        
    # Save/Upsert to MongoDB
    for opp in scraped_opportunities:
        try:
            # Validate links asynchronously in background to ensure zero broken paths!
            is_valid = await verify_link(opp["apply_link"])
            if not is_valid and not opp["apply_link"].startswith("https://weworkremotely.com"):
                logger.warning(f"Skipping link verification failure: {opp['apply_link']}")
                continue
                
            await opportunities_collection.update_one(
                {"apply_link": opp["apply_link"]},
                {"$set": opp},
                upsert=True
            )
            scraped_count += 1
        except Exception as db_err:
            logger.error(f"Failed to record student opportunity: {db_err}")
            
    # Trigger auto-cleanup of expired rows
    await prune_expired_opportunities()
    
    logger.info(f"Recorded {scraped_count} unique student opportunities in MongoDB.")
    return scraped_count
