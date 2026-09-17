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
    if 'Kids' in n or 'Kid' in n:
        return False
    if 'Women' in n or 'Womens' in n or 'Ladies' in n:
        return False
    if 'Long' in n and ('Sleeve' in n or 'Sleeves' in n):
        return False
    if 'Retro' in n:
        return False
    if 'Training' in n or 'Suit' in n or 'Jacket' in n or 'Windbreaker' in n or 'Socks' in n or 'Tracksuit' in n:
        return False
    if 'Fans' not in n and 'Player' not in n:
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
    """Scrape a single page and return product entries."""
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    products = []
    # Find all product link containers - each has an img + title text
    items = soup.find_all('li', class_='item') or soup.find_all('div', class_=re.compile('product|product-item'))
    
    if not items:
        # Fallback: find all anchor tags with product URLs
        products_links = soup.find_all('a', href=re.compile(r'/\d+-\d+.*-p\d+\.html'))
        for link in products_links:
            title = link.get('title', '').strip() or (link.find('img').get('alt', '') if link.find('img') else '')
            img = link.find('img')
            img_url = ''
            if img:
                src = img.get('src') or img.get('data-src') or ''
                if src and not src.startswith('http'):
                    src = BASE + src
                img_url = src
            
            # Find price - look for next sibling with price text
            price = '$14.50'
            parent = link.parent
            if parent:
                for sib in parent.find_all(string=True):
                    s = sib.strip()
                    pm = re.search(r'\$?([\d.]+)', s)
                    if pm and float(pm.group(1)) <= 30:  # jersey prices are $14-25 range
                        price = f"${pm.group(1)}"
                        break
            
            products.append({
                'name': title,
                'image': img_url,
                'price': price,
                'url': link.get('href', '')
            })
    
    return products

def get_total_pages(url):
    """Get total number of pages from pagination."""
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Find last page link in pagination
    pagination = soup.find('div', class_=re.compile('pagination|page|pager')) or \
                 soup.find('div', id=re.compile('pagination|page|pager'))
    
    if not pagination:
        return 1
    
    links = pagination.find_all('a')
    max_page = 1
    for link in links:
        href = link.get('href', '')
        page_match = re.search(r'list-r(\d+)\.html', href) or re.search(r'/(\d+)\.html$', href)
        if page_match:
            p = int(page_match.group(1))
            max_page = max(max_page, p)
    
    return max_page

all_jerseys = {}

for team_name, base_url in teams.items():
    print(f"Scraping {team_name}...")
    try:
        total_pages = get_total_pages(base_url)
        print(f"  -> {total_pages} pages to scrape")
        
        jerseys = []
        seen_names = set()
        
        for page in range(1, total_pages + 1):
            page_url = base_url.replace('list-r1.html', f'list-r{page}.html') if page > 1 else base_url
            
            products = scrape_page(page_url)
            
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
            
            time.sleep(0.5)  # politeness
        
        if jerseys:
            all_jerseys[team_name] = jerseys
            print(f"  -> {len(jerseys)} relevant jerseys found")
        else:
            print(f"  -> No relevant jerseys found")
        
    except Exception as e:
        print(f"  -> Error: {e}")

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
