import requests
from bs4 import BeautifulSoup
import json
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

url = 'https://www.jeogk9.com/Other-Brazil-Clubs-c69479.html'

# Only these teams are in scope for 26-27
target_teams = [
    "Santa Cruz",
    "Paysandu", 
    "Remo",
    "Athletico Paranaense",
    "Nautico",
    # Botafogo-PB - not on this page, skip
    "Coritiba",
    "Figueirense",
    "Vitoria",
]

all_jerseys = []

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

products = soup.select('ul.common_pro_list1 > li')
print(f"Total products on page: {len(products)}")

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
    
    # Only include target teams
    team_name = None
    for t in target_teams:
        if t.lower() in alt_lower:
            team_name = t
            break
    
    if not team_name:
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
        price = "$14.50"  # default for this page
    
    image_url = img_tag.get('src', '') or img_tag.get('data-src', '')
    
    all_jerseys.append({
        "team": team_name,
        "name": alt_text.strip(),
        "image_url": image_url,
        "price": price,
        "variant_type": variant_type,
        "style": style
    })

# Save raw JSON
with open("C:/Users/lizmo/Desktop/jersey-order/other_brazil_raw.json", "w") as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal Other Brazil jerseys scraped: {len(all_jerseys)}")

# Count by team
from collections import Counter
team_counts = Counter(j["team"] for j in all_jerseys)
for team, count in sorted(team_counts.items()):
    print(f"  {team}: {count}")

style_counts = Counter(j["style"] for j in all_jerseys)
print(f"\nBy style: {dict(style_counts)}")
