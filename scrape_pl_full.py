import requests
from bs4 import BeautifulSoup
import json
import time
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

BASE = 'https://www.jeogk9.com'

teams = {
    "Arsenal": "https://www.jeogk9.com/Search-ars/list-r1.html",
    "Aston Villa": "https://www.jeogk9.com/Search-Aston-Villa/list-r1.html",
    "Bournemouth": "https://www.jeogk9.com/Search-bournemouth/list-r1.html",
    "Brentford": "https://www.jeogk9.com/Search-brentford/list-r1.html",
    "Brighton & Hove Albion": "https://www.jeogk9.com/Search-Brighton/list-r1.html",
    "Chelsea": "https://www.jeogk9.com/Search-CHE/list-r1.html",
    "Coventry City": "https://www.jeogk9.com/Search-coventry+city/list-r1.html",
    "Crystal Palace": "https://www.jeogk9.com/Search-Crystal-Palace/list-r1.html",
    "Everton": "https://www.jeogk9.com/Search-EVE/list-r1.html",
    "Fulham": "https://www.jeogk9.com/Search-Fulham/list-r1.html",
    "Hull City": "https://www.jeogk9.com/Search-hull+city/list-r1.html",
    "Ipswich Town": "https://www.jeogk9.com/Search-ipswich/list-r1.html",
    "Leeds United": "https://www.jeogk9.com/Search-Leeds-United/list-r1.html",
    "Liverpool": "https://www.jeogk9.com/Search-Liverpool/list-r1.html",
    "Manchester City": "https://www.jeogk9.com/Search-Man-City/list-r1.html",
    "Manchester United": "https://www.jeogk9.com/Search-man-utd/list-r1.html",
    "Newcastle United": "https://www.jeogk9.com/Search-Newcastle/list-r1.html",
    "Nottingham Forest": "https://www.jeogk9.com/Search-Nottingham/list-r1.html",
    "Sunderland": "https://www.jeogk9.com/Search-sunderland/list-r1.html",
    "Tottenham Hotspur": "https://www.jeogk9.com/Search-TOT/list-r1.html",
}

def is_relevant(name):
    n = name.strip()
    if '26-27' not in n:
        return False
    if 'Jersey' not in n and 'jersey' not in n:
        return False
    if any(excl in n for excl in ['Kids', 'Kid ', 'Women', 'Womens', 'Ladies']):
        return False
    if ('Long' in n or 'Longsleeve' in n or 'Long Sleeves' in n) and 'Sleeve' in n:
        return False
    if 'Retro' in n:
        return False
    if any(excl in n for excl in ['Windbreaker', 'Training shirts', 'GoalKeeper', 
                                    'Suit', 'Tracksuit', 'Socks', 'Shorts', 'Tank Top', 
                                    'Hoody', 'Casual Version', 'Jacket']):
        return False
    return True

def extract_variant_and_style(name):
    name_upper = name.upper()
    if 'FOURTH' in name_upper:
        variant = 'Fourth'
    elif 'THIRD' in name_upper:
        variant = 'Third'
    elif 'AWAY' in name_upper:
        variant = 'Away'
    else:
        variant = 'Home'
    
    if 'Player Version' in name or 'PLAYER VERSION' in name_upper:
        style = 'Player'
    elif 'Fans' in name or 'FANS' in name_upper:
        style = 'Fan'
    else:
        style = 'Unknown'
    
    return variant, style

def scrape_page(url):
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    products = []
    ul = soup.find('ul', class_='common_pro_list1')
    
    if not ul:
        return products
    
    items = ul.find_all('li')
    
    for item in items:
        a_tag = item.find('a', href=re.compile(r'/\d+-\d+.*-p\d+\.html'))
        if not a_tag:
            continue
        
        title = (a_tag.get('title', '') or '').strip()
        
        img = a_tag.find('img')
        img_url = ''
        if img:
            src = img.get('src') or img.get('data-src') or ''
            if src and not src.startswith('http'):
                src = BASE + src
            img_url = src
        
        price = '$14.50'
        all_text = item.get_text(separator='|')
        pm = re.search(r'\$([\d.]+)', all_text)
        if pm:
            price = f"${pm.group(1)}"
        
        products.append({
            'name': title,
            'image': img_url,
            'price': price,
            'url': a_tag.get('href', '')
        })
    
    return products

all_jerseys = {}

for team_name, base_url in teams.items():
    print(f"Scraping {team_name}...")
    try:
        jerseys = []
        seen_names = set()
        
        # Iterate through pages until we hit an empty page
        max_pages_to_try = 15  # safety limit
        consecutive_empty = 0
        
        for page in range(1, max_pages_to_try + 1):
            if page == 1:
                page_url = base_url
            else:
                page_url = base_url.replace('list-r1.html', f'list-r{page}.html')
            
            products = scrape_page(page_url)
            
            if not products:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
                continue
            
            consecutive_empty = 0
            
            for prod in products:
                name = prod['name']
                if not name or not is_relevant(name):
                    continue
                
                if name in seen_names:
                    continue
                seen_names.add(name)
                
                variant, style = extract_variant_and_style(name)
                
                jerseys.append({
                    'name': name,
                    'image': prod['image'],
                    'variant_type': variant,
                    'style': style,
                    'price': prod['price']
                })
            
            time.sleep(0.5)
        
        if jerseys:
            all_jerseys[team_name] = jerseys
            print(f"  -> {len(jerseys)} relevant jerseys found")
        else:
            print(f"  -> No relevant jerseys found")
        
    except Exception as e:
        import traceback
        print(f"  -> Error: {e}")
        traceback.print_exc()

# Save results
with open('pl_jerseys_all.json', 'w') as f:
    json.dump(all_jerseys, f, indent=2)

print(f"\nTotal teams with jerseys: {len(all_jerseys)}")
total = sum(len(v) for v in all_jerseys.values())
print(f"Total jerseys: {total}")

for team, jrs in sorted(all_jerseys.items()):
    fan_count = sum(1 for j in jrs if j['style'] == 'Fan')
    player_count = sum(1 for j in jrs if j['style'] == 'Player')
    home = sum(1 for j in jrs if j['variant_type'] == 'Home')
    away = sum(1 for j in jrs if j['variant_type'] == 'Away')
    third = sum(1 for j in jrs if j['variant_type'] == 'Third')
    fourth = sum(1 for j in jrs if j['variant_type'] == 'Fourth')
    print(f"  {team}: {len(jrs)} total (Fan:{fan_count} Player:{player_count} Home:{home} Away:{away} Third:{third} Fourth:{fourth})")
