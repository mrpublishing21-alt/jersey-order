import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Premier League teams for 2026-27 season with their jeogk9 page IDs
pl_teams = {
    "Arsenal": "/ARS-c68990.html",
    "Aston Villa": "/Aston-Villa-c69256.html",
    "Bournemouth": None,  # need to find
    "Brentford": None,
    "Brighton & Hove Albion": "/Brighton-c69644.html",
    "Chelsea": "/CHE-c68989.html",
    "Coventry City": None,
    "Crystal Palace": "/Crystal-Palace-c69720.html",
    "Everton": "/EVE-c69453.html",
    "Fulham": "/Fulham-c69778.html",
    "Hull City": None,
    "Ipswich Town": None,
    "Leeds United": "/Leeds-United-c69245.html",
    "Liverpool": "/Liverpool-c68988.html",
    "Manchester City": "/Man-City-c68991.html",
    "Manchester United": "/Man-Utd-c68992.html",
    "Newcastle United": "/Newcastle-c69242.html",
    "Nottingham Forest": "/Nottingham-c69248.html",
    "Sunderland": None,
    "Tottenham Hotspur": "/TOT-c69000.html",
}

all_jerseys = {}

def filter_jersey(name):
    """Filter for 26-27 short sleeve fan/player versions only."""
    name_lower = name.lower()
    
    # Must be 26-27 season
    if '26-27' not in name:
        return False
    
    # Exclude long sleeve (长袖)
    if 'long-sleeve' in name_lower or 'long sleeves' in name_lower or '长袖' in name:
        return False
    
    # Exclude kids/children (童装)
    if 'kids' in name_lower:
        return False
    
    # Exclude women (女)
    if 'women' in name_lower or '(女)' in name:
        return False
    
    # Exclude baby, infant, cheerleading, socks, shorts/pants, pet
    exclude_terms = ['baby', 'infant', 'cheerleading', 'socks', 'shorts pants', 'pet']
    for term in exclude_terms:
        if term in name_lower:
            return False
    
    # Must be a jersey (not socks/shorts/pants)
    if 'jersey' not in name_lower:
        return False
    
    return True

def extract_jersey_info(name):
    """Extract variant and style from jersey name."""
    variant = "Home"  # default
    style = "Fans"    # default
    
    name_lower = name.lower()
    
    if 'home' in name_lower:
        variant = "Home"
    elif 'away' in name_lower:
        variant = "Away"
    elif 'third' in name_lower:
        variant = "Third"
    elif 'away' in name_lower:
        variant = "Away"
    
    if 'player version' in name_lower or '球员' in name:
        style = "Player"
    elif 'fans' in name_lower:
        style = "Fans"
    elif 'embroidered' in name_lower:
        style = "Embroidered"
    
    return variant, style

# First, find missing team page IDs by scraping the main Premier League category page
pl_category_url = "/Premier-League-c68987.html"
response = requests.get("https://www.jeogk9.com" + pl_category_url, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

print("=== Finding missing team page IDs ===")
for link in soup.find_all('a', href=True):
    text = link.get_text(strip=True).lower()
    href = link['href']
    
    # Check for teams we don't have yet
    if 'coventry' in text and '/c-' in href:
        pl_teams["Coventry City"] = href
        print(f"  Coventry City -> {href}")
    elif 'hull city' in text and '/c-' in href:
        pl_teams["Hull City"] = href
        print(f"  Hull City -> {href}")
    elif 'ipswich town' in text and '/c-' in href:
        pl_teams["Ipswich Town"] = href
        print(f"  Ipswich Town -> {href}")
    elif 'sunderland' in text and '/c-' in href:
        pl_teams["Sunderland"] = href
        print(f"  Sunderland -> {href}")
    elif 'bournemouth' in text and '/c-' in href:
        # Bournemouth might be under a different name
        if not pl_teams.get("Bournemouth"):
            pl_teams["AFC Bournemouth"] = href
            print(f"  AFC Bournemouth -> {href}")
    elif 'brentford' in text and '/c-' in href:
        pl_teams["Brentford"] = href
        print(f"  Brentford -> {href}")

print("\n=== All PL teams ===")
for team, page in pl_teams.items():
    print(f"  {team}: {page}")

# Now scrape each team's kit page
print("\n=== Scraping jerseys ===")
total_found = 0

for team, page_url in pl_teams.items():
    if not page_url:
        print(f"\n{team}: SKIPPED (no page URL)")
        continue
    
    print(f"\n{team}...")
    
    try:
        response = requests.get("https://www.jeogk9.com" + page_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        team_jerseys = []
        
        # Find all product links and images
        for img in soup.find_all('img'):
            alt = img.get('alt', '').strip()
            src = img.get('src', '') or img.get('data-src', '') or ''
            
            if not alt or '26-27' not in alt:
                continue
            
            # Filter for short sleeve fan/player versions only
            if not filter_jersey(alt):
                continue
            
            variant, style = extract_jersey_info(alt)
            
            # Clean up the image URL - remove resize params for better quality
            clean_url = src.split('?')[0] if '?' in src else src
            
            team_jerseys.append({
                'name': alt,
                'variant': variant,
                'style': style,
                'image_url': clean_url,
                'product_page': ''  # will fill below
            })
        
        # Also get product page URLs for each jersey
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if filter_jersey(text) and '-p' in link['href']:
                # Find matching entry by name
                for j in team_jerseys:
                    if j['name'] == text or (j['name'].replace(' 1:1 Thai Quality', '')).strip() == text.strip():
                        j['product_page'] = 'https://www.jeogk9.com' + link['href']
        
        # Deduplicate by name
        seen_names = set()
        unique_jerseys = []
        for j in team_jerseys:
            if j['name'] not in seen_names:
                seen_names.add(j['name'])
                unique_jerseys.append(j)
        
        all_jerseys[team] = unique_jerseys
        total_found += len(unique_jerseys)
        print(f"  Found {len(unique_jerseys)} matching jerseys")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(1.5)

# Save results
with open('premier_league_jerseys.json', 'w') as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\n=== Total: {total_found} jerseys across {len(all_jerseys)} teams ===")
