import requests
from bs4 import BeautifulSoup
import json
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# MLS teams with their jeogk9 short-code URLs
teams = [
    ("Inter Miami", "/Inter-Miami-c69384.html"),
    ("LA Galaxy", "/LA-Galaxy-c69303.html"),
    ("Portland Timbers", "/Portland-Timbers-c69422.html"),
    ("New York City", "/New-York-City-c69460.html"),
    ("Atlanta United", "/Atlanta-United-c69424.html"),
    ("New York Red Bulls", "/New-York-Red-Bulls-c69575.html"),
    ("Austin FC", "/AUstin-FC-c69416.html"),
    ("Nashville SC", "/Nashville-SC-c69413.html"),
    ("Charlotte", "/Charlotte-c69411.html"),
    ("Dallas FC", "/Dallas-FC-c69090.html"),
    ("Minnesota United", "/Minnesota-United-c69590.html"),
    ("Orlando City", "/Orlando-City-c69604.html"),
    ("Houston Dynamo", "/Houston-Dynamo-c69658.html"),
    ("Chicago Fire", "/Chicago-Fire-c69746.html"),
    ("Seattle Sounders FC", "/Seattle-Sounders-FC-c69750.html"),
]

all_jerseys = []

for team_name, path in teams:
    url = f'https://www.jeogk9.com{path}'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Check if page title matches team (not a redirect to shared category)
        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else ''
        if team_name.lower() not in page_title.lower():
            print(f"  {team_name}: SKIPPED - page title doesn't match (got '{page_title}')")
            continue
        
        # Find product grid
        products = soup.select('ul.common_pro_list1 > li')
        
        for item in products:
            img_tag = item.find('img')
            if not img_tag:
                continue
            
            alt_text = img_tag.get('alt', '')
            
            # Filter: exclude long sleeve, kids, women, shorts, socks
            alt_lower = alt_text.lower()
            
            # Skip long sleeve
            if 'long sleeve' in alt_lower or '长袖' in alt_text:
                continue
            
            # Skip women
            if 'women' in alt_lower or '(女)' in alt_text:
                continue
            
            # Skip kids/youth
            if 'kids' in alt_lower or 'youth' in alt_lower or '儿童' in alt_text:
                continue
            
            # Skip shorts/socks/tank top
            if any(skip in alt_lower for skip in ['shorts', 'pants', 'socks', 'tank top']):
                continue
            
            # Determine style from alt text
            style = "Fan"  # default
            if 'player' in alt_lower or '球员' in alt_text:
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
                "team": team_name,
                "name": alt_text.strip(),
                "image_url": image_url,
                "price": price,
                "variant_type": variant_type,
                "style": style
            })
        
        print(f"  {team_name}: {len(products)} total products")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {team_name}: ERROR - {e}")

# Save raw JSON
with open("C:/Users/lizmo/Desktop/jersey-order/mls_raw.json", "w") as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal MLS jerseys scraped: {len(all_jerseys)}")

# Count by team
from collections import Counter
team_counts = Counter(j["team"] for j in all_jerseys)
for team, count in sorted(team_counts.items()):
    print(f"  {team}: {count}")
