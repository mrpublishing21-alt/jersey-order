import requests
from bs4 import BeautifulSoup
import json
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# MLS Other Clubs teams we care about
target_teams = [
    "Columbus Crew",
    "New England Revolution",
    "Real Salt Lake",
    "St. Louis City",
    "Philadelphia Union",
    "Seattle Sounders",
    "FC Dallas",
    "Montreal",
    "Toronto FC",
    "Colorado Rapids",
    "San Jose Earthquakes",
    "FC Cincinnati",
    "D.C. United",
    "Sporting Kansas City",
    "Vancouver Whitecaps",
    "San Diego FC",
]

all_jerseys = []
base_url = 'https://www.jeogk9.com/MLS-Other-Cluber-c69278.html'

# Handle pagination - check how many pages exist
page = 1
while True:
    url = f'{base_url}?page={page}' if page > 1 else base_url
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        products = soup.select('ul.common_pro_list1 > li')
        if not products:
            print(f"Page {page}: No more products. Stopping pagination.")
            break
        
        for item in products:
            img_tag = item.find('img')
            if not img_tag:
                continue
            
            alt_text = img_tag.get('alt', '')
            
            # Filter to target teams only
            team_match = None
            for t in target_teams:
                if t.lower() in alt_text.lower():
                    team_match = t
                    break
            if not team_match:
                continue
            
            # Skip retro/vintage
            if 'retro' in alt_text.lower() or 'vintage' in alt_text.lower():
                continue
            
            # Filter: exclude long sleeve, kids, women, shorts, socks, windbreaker, training
            alt_lower = alt_text.lower()
            if 'long sleeve' in alt_lower or '长袖' in alt_text:
                continue
            if 'women' in alt_lower or '(女)' in alt_text:
                continue
            if any(skip in alt_lower for skip in ['kids', 'youth', '儿童']):
                continue
            if any(skip in alt_lower for skip in ['shorts', 'pants', 'socks', 'tank top', 'windbreaker', 'training']):
                continue
            
            # Determine style from alt text
            style = "Fan"  # default
            if 'player' in alt_lower or '球员版' in alt_text:
                style = "Player"
            elif 'suit' in alt_lower or '训练服' in alt_text:
                style = "Adult Suit"
            
            # Determine variant type
            variant_type = "Home"  # default
            if 'away' in alt_lower:
                variant_type = "Away"
            elif 'third' in alt_lower:
                variant_type = "Third"
            elif 'alternate' in alt_lower or 'alt' in alt_lower:
                variant_type = "Alternate"
            
            # Extract price from alt text (pattern: $XX.XX)
            price_match = re.search(r'\$[\d.]+', alt_text)
            if price_match:
                price = price_match.group(0)
            else:
                price = "$25.00"  # default
            
            image_url = img_tag.get('src', '') or img_tag.get('data-src', '')
            
            all_jerseys.append({
                "team": team_match,
                "name": alt_text.strip(),
                "image_url": image_url,
                "price": price,
                "variant_type": variant_type,
                "style": style
            })
        
        print(f"Page {page}: {len(products)} products, total so far: {len(all_jerseys)}")
        page += 1
        time.sleep(0.5)
    except Exception as e:
        print(f"Page {page}: ERROR - {e}")
        break

# Save raw JSON
with open("C:/Users/lizmo/Desktop/jersey-order/mls_other_raw.json", "w") as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal MLS Other jerseys scraped: {len(all_jerseys)}")

# Count by team
from collections import Counter
team_counts = Counter(j["team"] for j in all_jerseys)
for team, count in sorted(team_counts.items()):
    print(f"  {team}: {count}")

style_counts = Counter(j["style"] for j in all_jerseys)
print(f"\nBy style: {dict(style_counts)}")
