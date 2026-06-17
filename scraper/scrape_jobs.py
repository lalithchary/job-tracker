"""Job scraper for PPC, Manufacturing, Material Planning roles in India."""
import json, os, time, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SEARCH_QUERIES = [
    "Production Planning Control PPC",
    "Material Planning Engineer",
    "Manufacturing Engineer",
    "PPC Engineer manufacturing",
    "Material Planning Manager",
    "Manufacturing Business Process",
    "Lean Manufacturing Engineer",
    "Supply Chain Planning Manufacturing",
    "Inventory Planning Manufacturing",
]

# Only Hyderabad, Remote, WFH, Contract jobs
ALLOWED_LOCATIONS = ["hyderabad", "remote", "work from home", "wfh", "india", "telangana", "anywhere", "contract"]

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"


def job_id(title, company, location):
    raw = f"{title}{company}{location}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def scrape_remotive():
    """Scrape from Remotive (free API)."""
    jobs = []
    try:
        for q in ["manufacturing", "planning", "production"]:
            r = requests.get(f"https://remotive.com/api/remote-jobs?search={q}&limit=20", headers=HEADERS, timeout=15)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    jobs.append({
                        "id": job_id(j["title"], j["company_name"], j.get("candidate_required_location", "")),
                        "title": j["title"],
                        "company": j["company_name"],
                        "location": j.get("candidate_required_location", "Remote"),
                        "url": j["url"],
                        "source": "Remotive",
                        "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "salary": j.get("salary", ""),
                    })
            time.sleep(1)
    except Exception as e:
        print(f"Remotive error: {e}")
    return jobs


def scrape_adzuna():
    """Scrape from Adzuna (free tier via web scraping)."""
    jobs = []
    queries = ["production+planning", "material+planning", "ppc+engineer", "manufacturing+engineer", "lean+manufacturing"]
    try:
        for q in queries:
            url = f"https://www.adzuna.co.in/search?q={q}&loc=Hyderabad"
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for listing in soup.select("div[data-aid]")[:10]:
                title_el = listing.select_one("a[data-aid='jobTitle']") or listing.select_one("h2 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if not link.startswith("http"):
                    link = "https://www.adzuna.co.in" + link
                company_el = listing.select_one("span[data-aid='companyName']") or listing.select_one(".ui-company")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_el = listing.select_one("span[data-aid='location']") or listing.select_one(".ui-location")
                location = loc_el.get_text(strip=True) if loc_el else "India"
                jobs.append({
                    "id": job_id(title, company, location),
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": link,
                    "source": "Adzuna",
                    "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "salary": "",
                })
            time.sleep(2)
    except Exception as e:
        print(f"Adzuna error: {e}")
    return jobs


def scrape_linkedin_public():
    """Scrape LinkedIn public job search (no auth needed)."""
    jobs = []
    queries = [
        "production planning control hyderabad",
        "material planning engineer hyderabad",
        "manufacturing engineer hyderabad",
        "PPC engineer hyderabad",
        "lean manufacturing engineer hyderabad",
        "production planning remote india",
        "material planning remote india",
    ]
    try:
        for q in queries:
            url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(q)}&location=Hyderabad&f_TPR=r604800"
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("div.base-card")[:10]:
                title_el = card.select_one("h3.base-search-card__title")
                link_el = card.select_one("a.base-card__full-link")
                company_el = card.select_one("h4.base-search-card__subtitle")
                loc_el = card.select_one("span.job-search-card__location")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = link_el["href"] if link_el else ""
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = loc_el.get_text(strip=True) if loc_el else "India"
                jobs.append({
                    "id": job_id(title, company, location),
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": link,
                    "source": "LinkedIn",
                    "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "salary": "",
                })
            time.sleep(2)
    except Exception as e:
        print(f"LinkedIn error: {e}")
    return jobs


def scrape_jooble():
    """Scrape Jooble India."""
    jobs = []
    queries = ["production+planning", "material+planning", "PPC+engineer", "manufacturing+engineer"]
    try:
        for q in queries:
            url = f"https://in.jooble.org/SearchResult?ukw={q}&rgns=Hyderabad"
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("article")[:10]:
                title_el = card.select_one("h2 a") or card.select_one("[data-test-name='titleLink']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = "https://in.jooble.org" + link
                company_el = card.select_one("[data-test-name='company']") or card.select_one(".company-name")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_el = card.select_one("[data-test-name='location']") or card.select_one(".caption")
                location = loc_el.get_text(strip=True) if loc_el else "India"
                jobs.append({
                    "id": job_id(title, company, location),
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": link,
                    "source": "Jooble",
                    "date_found": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "salary": "",
                })
            time.sleep(2)
    except Exception as e:
        print(f"Jooble error: {e}")
    return jobs


def filter_relevant(jobs):
    """Filter jobs relevant to PPC/Manufacturing/Material Planning in Hyderabad/Remote."""
    keywords = [
        "production planning", "ppc", "material planning", "manufacturing",
        "lean", "kaizen", "inventory", "supply chain", "procurement",
        "shop floor", "plant", "operations", "industrial", "process engineer",
        "six sigma", "erp", "mrp", "scheduling", "warehouse",
    ]
    filtered = []
    seen_ids = set()
    for j in jobs:
        if j["id"] in seen_ids:
            continue
        text = (j["title"] + " " + j.get("company", "")).lower()
        loc = j.get("location", "").lower()
        # Must match role keywords
        if not any(k in text for k in keywords):
            continue
        # Must be Hyderabad, Remote, or broad India (not other specific cities)
        is_allowed_location = any(al in loc for al in ALLOWED_LOCATIONS)
        is_other_city = any(c in loc for c in [
            "bangalore", "bengaluru", "chennai", "mumbai", "pune", "delhi",
            "gurgaon", "noida", "kolkata", "ahmedabad", "jaipur", "kochi",
            "coimbatore", "silvassa", "kanchipuram", "vadodara", "surat",
        ])
        if not is_allowed_location and is_other_city:
            continue
        seen_ids.add(j["id"])
        filtered.append(j)
    return filtered


def load_existing():
    """Load existing jobs data."""
    filepath = DATA_DIR / "jobs.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def merge_jobs(existing, new_jobs):
    """Merge new jobs with existing, preserving status fields."""
    existing_map = {j["id"]: j for j in existing}
    for j in new_jobs:
        if j["id"] not in existing_map:
            j["status"] = "new"
            j["notes"] = ""
            existing_map[j["id"]] = j
    # Keep max 500 jobs (GitHub Pages file size consideration), remove oldest first
    all_jobs = list(existing_map.values())
    all_jobs.sort(key=lambda x: x.get("date_found", ""), reverse=True)
    return all_jobs[:500]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Starting job scrape...")
    
    all_new = []
    
    print("Scraping LinkedIn...")
    all_new.extend(scrape_linkedin_public())
    print(f"  Found {len(all_new)} jobs so far")
    
    print("Scraping Adzuna...")
    all_new.extend(scrape_adzuna())
    print(f"  Found {len(all_new)} jobs so far")
    
    print("Scraping Jooble...")
    all_new.extend(scrape_jooble())
    print(f"  Found {len(all_new)} jobs so far")
    
    print("Scraping Remotive...")
    all_new.extend(scrape_remotive())
    print(f"  Total scraped: {len(all_new)}")
    
    relevant = filter_relevant(all_new)
    print(f"  Relevant after filtering: {len(relevant)}")
    
    existing = load_existing()
    merged = merge_jobs(existing, relevant)
    
    with open(DATA_DIR / "jobs.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    # Write last update timestamp
    with open(DATA_DIR / "last_updated.json", "w", encoding="utf-8") as f:
        json.dump({"last_updated": datetime.now(timezone.utc).isoformat()}, f)
    
    print(f"Done! Total jobs in database: {len(merged)}")


if __name__ == "__main__":
    main()
