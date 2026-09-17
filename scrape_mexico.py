import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Mexico Liga teams with their jeogk9 URLs
teams = [
    ("America", "/America%C2%A0-c69082.html"),
    ("Chivas", "/Chivas-c69081.html"),
    ("Tigres UANL", "/Tigres-UANL-c69079.html"),
    ("Pumas UNAM", "/Pumas-UNAM-c69105.html"),
    ("Cruz Azul", "/Cruz-Azul-c69493.html"),
    ("Monterrey", "/Monterrey-c69659.html"),
    ("Atlas FC", "/Atlas-FC-c69837.html"),
    ("Santos Laguna", "/Santos-Laguna-c69832.html"),
    ("Puebla FC", "/Puebla-FC-c69825.html"),
    ("Leon", "/Leon-c69815.html"),
    ("Toluca", "/Toluca%C2%A0-c69802.html"),
    ("Necaxa", "/Necaxa-c69789.html"),
    ("Pachuca", "/Pachuca%C2%A0-c69697.html"),
    ("Tijuana", "/Tijuana%C2%A0-c69665.html"),
    ("Mazatlan", "/Mazatlan-c88520.html"),
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
            
            # Skip shorts/socks/training suits that aren't full suits
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
            elif 'third' in alt_lower or 'third' in alt_lower:
                variant_type = "Third"
            elif 'alternate' in alt_lower or 'alt' in alt_lower:
                variant_type = "Alternate"
            
            # Extract price from alt text (pattern: $XX.XX)
            import re
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
with open("C:/Users/lizmo/Desktop/jersey-order/mexico_raw.json", "w") as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal Mexico Liga jerseys scraped: {len(all_jerseys)}")

# Count by team
from collections import Counter
team_counts = Counter(j["team"] for j in all_jerseys)
for team, count in sorted(team_counts.items()):
    print(f"  {team}: {count}")
