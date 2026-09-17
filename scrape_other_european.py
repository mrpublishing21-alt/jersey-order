import requests
from bs4 import BeautifulSoup
import json
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# All Other European Clubs teams with their URLs
teams_urls = [
    # Search URL teams (Phase 1)
    ("Anderlecht", "https://www.jeogk9.com/Search-anderlecht/list-r1.html"),
    ("Luton Town", "https://www.jeogk9.com/Search-luton+town/list-r1.html"),
    ("Club Brugge", "https://www.jeogk9.com/Search-club+brugge/list-r1.html"),
    ("Bohemian FC", "https://www.jeogk9.com/Search-bohemian+fc/list-r1.html"),
    ("Aberdeen", "https://www.jeogk9.com/Search-aberdeen/list-r1.html"),
    ("Copenhagen FC", "https://www.jeogk9.com/Search-copenhagen+fc/list-r1.html"),
    ("Dinamo Zagreb", "https://www.jeogk9.com/Search-dinamo+zagreb/list-r1.html"),
    ("Salzburg", "https://www.jeogk9.com/Search-salzburg/list-r1.html"),
    ("Olympiacos", "https://www.jeogk9.com/Search-olympiacos/list-r1.html"),
    # Search URL teams with active 26-27 items (Phase 2)
    ("Celtic", "https://www.jeogk9.com/Search-celtic/list-r1.html"),
    ("Rangers", "https://www.jeogk9.com/Search-rangers/list-r1.html"),
    ("Galatasaray", "https://www.jeogk9.com/Search-galatasaray/list-r1.html"),
    ("Fenerbahce", "https://www.jeogk9.com/Search-fenerbahce/list-r1.html"),
    # Besiktas already scraped in Phase 1 of previous run
    ("Besiktas", "https://www.jeogk9.com/Search-besiktas/list-r1.html"),
]

all_jerseys = []

for team, url in teams_urls:
    page = 1
    while True:
        if page > 1:
            paginated_url = f'{url}?page={page}'
        else:
            paginated_url = url
        
        try:
            r = requests.get(paginated_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            products = soup.select('ul.common_pro_list1 > li')
            if not products:
                print(f"{team} page {page}: No more products. Stopping pagination.")
                break
            
            for item in products:
                img_tag = item.find('img')
                if not img_tag:
                    continue
                
                alt_text = img_tag.get('alt', '')
                
                # Skip retro/vintage
                if 'retro' in alt_text.lower() or 'vintage' in alt_text.lower():
                    continue
                
                # Filter: exclude long sleeve, kids, women, shorts, socks, windbreaker, training, goalkeeper
                alt_lower = alt_text.lower()
                if 'long sleeve' in alt_lower or '长袖' in alt_text:
                    continue
                if 'women' in alt_lower or '(女)' in alt_text:
                    continue
                if any(skip in alt_lower for skip in ['kids', 'youth', '儿童']):
                    continue
                if any(skip in alt_lower for skip in ['shorts', 'pants', 'socks', 'tank top', 'windbreaker', 'training']):
                    continue
                if 'goalkeeper' in alt_lower or 'gk' in alt_lower:
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
                    price = "$14.50"  # default
                
                image_url = img_tag.get('src', '') or img_tag.get('data-src', '')
                
                all_jerseys.append({
                    "team": team,
                    "name": alt_text.strip(),
                    "image_url": image_url,
                    "price": price,
                    "variant_type": variant_type,
                    "style": style
                })
            
            print(f"{team} page {page}: {len(products)} products, total so far: {len(all_jerseys)}")
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"{team} page {page}: ERROR - {e}")
            break
    
    if team != teams_urls[-1][0]:
        time.sleep(0.3)

# Save raw JSON
with open("C:/Users/lizmo/Desktop/jersey-order/other_european_raw.json", "w") as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal Other European Clubs jerseys scraped: {len(all_jerseys)}")

# Count by team
from collections import Counter
team_counts = Counter(j["team"] for j in all_jerseys)
for team, count in sorted(team_counts.items()):
    print(f"  {team}: {count}")

style_counts = Counter(j["style"] for j in all_jerseys)
print(f"\nBy style: {dict(style_counts)}")
