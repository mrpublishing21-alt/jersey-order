#!/usr/bin/env python3
"""Scrape Bundesliga 26-27 short sleeve fan/player/adult suit jerseys from jeogk9.com."""

import requests
from bs4 import BeautifulSoup
import json
import re
import time

BASE_URL = "https://www.jeogk9.com"

# Teams with dedicated pages (from main Bundesliga category)
DEDICATED_TEAMS = {
    "Bayern": {"url": "/Bayern-c69196.html", "name": "FC Bayern Munich"},
    "Dortmund": {"url": "/Dortmund-c69195.html", "name": "Borussia Dortmund"},
    "Frankfurt": {"url": "/Eintracht-Frankfurt-c69447.html", "name": "Eintracht Frankfurt"},
    "Union-Berlin": {"url": "/FC-Union-Berlin-c69846.html", "name": "1. FC Union Berlin"},
    "Leipzig": {"url": "/RB-Leipzig-c69635.html", "name": "RB Leipzig"},
    "Bremen": {"url": "/Werder-Bremen-c69550.html", "name": "SV Werder Bremen"},
    "Stuttgart": {"url": "/VfB-Stuttgart-c69589.html", "name": "VfB Stuttgart"},
}

# 2026/27 Bundesliga clubs that appear in the shared category (no dedicated pages)
SHARED_CATEGORY_CLUBS = {
    "Mainz": {"display_name": "1. FSV Mainz 05"},
    "Leverkusen": {"display_name": "Bayer 04 Leverkusen"},
    "Gladbach": {"display_name": "Borussia Mönchengladbach"},
    "Augsburg": {"display_name": "FC Augsburg"},
    "Schalke": {"display_name": "FC Schalke 04"},
    "Freiburg": {"display_name": "SC Freiburg"},
    "Paderborn": {"display_name": "SC Paderborn 07"},
    "Elversberg": {"display_name": "SV Elversberg"},
    "Hoffenheim": {"display_name": "TSG 1899 Hoffenheim"},
    "Köln": {"display_name": "1. FC Köln"},
}

def scrape_page(url):
    """Scrape products from a single page."""
    full_url = BASE_URL + url if url.startswith('/') else url
    r = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    soup = BeautifulSoup(r.text, 'html.parser')
    
    items = []
    ul = soup.find('ul', class_='common_pro_list1')
    if not ul:
        return items
    
    for li in ul.find_all('li'):
        img_tag = li.find('img')
        alt_text = img_tag.get('alt', '') if img_tag else ''
        
        price_tag = li.find(class_=lambda c: c and 'price' in str(c).lower())
        price_raw = price_tag.get_text(strip=True) if price_tag else ''
        
        name = alt_text.strip() if alt_text else ''
        if not name:
            a_tag = li.find('a')
            name = a_tag.get_text(strip=True) if a_tag else ''
        
        img_url = img_tag.get('src', '') if img_tag else ''
        
        price_match = re.search(r'\$([\d.]+)', price_raw)
        price = f"${price_match.group(1)}" if price_match else ""
        
        if name and img_url:
            items.append({
                "name": name,
                "image": img_url,
                "price": price
            })
    
    return items

def is_relevant(name):
    """Filter for short sleeve fan/player/adult suit only."""
    n = name.lower()
    
    # Exclude long sleeve
    if 'long sleeve' in n or '长袖' in n:
        return False
    
    # Exclude kids
    if 'kids' in n:
        return False
    
    # Exclude women
    if 'women' in n or 'woman' in n:
        return False
    
    # Exclude shorts/socks/pants
    if any(kw in n for kw in ['shorts', 'socks', 'pants']):
        return False
    
    # Exclude pet
    if 'pet' in n:
        return False
    
    # Must be a jersey or suit (adult)
    is_jersey = 'jersey' in n or 'soccer jersey' in n
    is_suit = any(kw in n for kw in ['suit', 'high quality'])
    
    if not (is_jersey or is_suit):
        return False
    
    return True

def extract_team_from_name(name, known_teams=None):
    """Extract team name from jersey product name."""
    # Pattern: "26-27 TEAMNAME Home/Away/Third Fans Soccer Jersey"
    match = re.search(r'\d{2}-\d{2}\s+(.+?)\s+(?:Home|Away|Third|Fourth)', name)
    if match:
        return match.group(1).strip()
    
    # Pattern for adult suits: "26-27 TEAMNAME Home Adult Suit"
    match = re.search(r'\d{2}-\d{2}\s+(.+?)\s+Adult\s+Suit', name)
    if match:
        return match.group(1).strip()
    
    # Pattern for leaked edition: "26-27 TEAMNAME Home Leaked Edition Player Version"
    match = re.search(r'\d{2}-\d{2}\s+(.+?)\s+Leaked', name)
    if match:
        return match.group(1).strip()
    
    # Pattern for special edition: "26-27 TEAMNAME Home Special Edition Fans"
    match = re.search(r'\d{2}-\d{2}\s+(.+?)\s+Special', name)
    if match:
        return match.group(1).strip()
    
    # Try to match against known team names
    if known_teams:
        for team in known_teams:
            if team.lower() in name.lower():
                return team
    
    return "Unknown"

def scrape_all():
    """Scrape all pages of Bundesliga."""
    all_jerseys = []
    
    # Known team names for matching on shared category
    KNOWN_TEAMS = list(SHARED_CATEGORY_CLUBS.keys())
    
    # Scrape dedicated team pages first
    for team_key, team_info in DEDICATED_TEAMS.items():
        url = team_info["url"]
        display_name = team_info["name"]
        
        print(f"Scraping {display_name}...")
        items = scrape_page(url)
        relevant_count = 0
        
        for item in items:
            if is_relevant(item["name"]):
                relevant_count += 1
                all_jerseys.append({
                    "team": display_name,
                    **item
                })
        
        print(f"  {len(items)} total -> {relevant_count} relevant")
        time.sleep(0.5)
    
    # Scrape shared category for other teams (only 2026/27 Bundesliga clubs)
    print(f"\nScraping shared Bundesliga Other category...")
    items = scrape_page("/Bundesliga-Other-c69455.html")
    print(f"  {len(items)} products on shared page")
    
    for item in items:
        if not is_relevant(item["name"]):
            continue
        
        # Try to identify which team this belongs to
        extracted_team = extract_team_from_name(item['name'], KNOWN_TEAMS)
        
        # Only include if it's one of our target 2026/27 Bundesliga clubs
        if extracted_team not in SHARED_CATEGORY_CLUBS:
            continue
        
        display_name = SHARED_CATEGORY_CLUBS[extracted_team]["display_name"]
        
        all_jerseys.append({
            "team": display_name,
            **item
        })
    
    # Group by team and determine style/price
    teams = {}
    for j in all_jerseys:
        t = j["team"]
        if t not in teams:
            teams[t] = []
        
        name_lower = j['name'].lower()
        
        if 'player version' in name_lower or '球员' in name_lower:
            style = "Player"
            price = "$28.00"
        elif 'adult suit' in name_lower or 'high quality' in name_lower:
            style = "Suit"
            price = "$31.00"
        else:
            style = "Fan"
            price = "$25.00"
        
        # Determine variant_type
        if 'home' in name_lower:
            variant = "Home"
        elif 'away' in name_lower:
            variant = "Away"
        elif 'third' in name_lower:
            variant = "Third"
        elif 'fourth' in name_lower:
            variant = "Fourth"
        else:
            variant = "Home"
        
        teams[t].append({
            "name": j["name"],
            "image": j["image"],
            "price": price,
            "variant_type": variant,
            "style": style
        })
    
    print(f"\nTotal relevant Bundesliga jerseys: {len(all_jerseys)}")
    print(f"Teams found: {len(teams)}")
    
    for team, jerseys in sorted(teams.items()):
        styles = {}
        variants = {}
        for j in jerseys:
            s = j['style']
            v = j['variant_type']
            styles[s] = styles.get(s, 0) + 1
            variants[v] = variants.get(v, 0) + 1
        print(f"  {team}: {len(jerseys)} jerseys ({styles}, {variants})")
    
    return all_jerseys

if __name__ == "__main__":
    jerseys = scrape_all()
    
    with open("C:/Users/lizmo/Desktop/jersey-order/bundesliga_raw.json", "w") as f:
        json.dump(jerseys, f, indent=2)
    
    print(f"\nSaved {len(jerseys)} jerseys to bundesliga_raw.json")
