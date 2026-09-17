#!/usr/bin/env python3
"""Scrape La Liga 26-27 short sleeve fan/player jerseys from jeogk9.com."""

import requests
from bs4 import BeautifulSoup
import json, re, time

BASE = "https://www.jeogk9.com"
CDN = "us03-imgcdn.ymcart.com"

# La Liga teams (Spanish clubs only)
LA_LIGA_TEAMS = [
    ("BAR", "/BAR-c69223.html"),
    ("RMA", "/RMA-c69216.html"),
    ("ATM", "/ATM-c69244.html"),
    ("Real Betis", "/Real-Betis-c69237.html"),
    ("Valencia", "/Valencia-c69263.html"),
    ("Bilbao", "/Bilbao-c69611.html"),
    ("Zaragoza", "/Zaragoza-c69449.html"),
    ("Villarreal", "/Villarreal-c69421.html"),
    ("Osasuna", "/Osasuna-c69793.html"),
    ("Cadiz", "/Cadiz-c69696.html"),
    ("Valladolid", "/Valladolid-c69812.html"),
    ("Real Sociedad", "/Real-Sociedad-c69716.html"),
    ("Celta & Espanyol", "/Celta-Espanyol-c69305.html"),
    ("Sevilla & Almeria", "/Sevilla-Almeria-c69703.html"),
    ("Girona & Elche", "/Girona-Elche-c69777.html"),
    ("Leganes & Granada", "/Leganes-Granada-c69847.html"),
]

def is_short_sleeve(name):
    """Check if jersey is short sleeve (NOT long sleeve)."""
    name_lower = name.lower()
    # Exclude long sleeve variants
    if "long" in name_lower or "长袖" in name:
        return False
    return True

def is_not_kids(name):
    """Exclude kids/youth/baby/pet versions."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["kids", "童装", "baby", "infant", "pet", "youth", "junior"]):
        return False
    return True

def is_not_women(name):
    """Exclude women's/ladies versions."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["women", "女", "ladies"]):
        # But keep cheerleading as it's not a jersey variant we want
        if "cheerleading" in name_lower:
            return False
        return False
    return True

def is_fan_or_player(name):
    """Only include fan version or player version."""
    name_lower = name.lower()
    # Include fan and player versions
    if any(kw in name_lower for kw in ["fans", "fan", "player", "球员"]):
        return True
    # Also include "embroidered" variants that are fan/player (not kids/women)
    if "embroidered" in name_lower:
        return True
    return False

def has_season_26_27(name):
    """Check for 2026-27 season."""
    return "26-27" in name or "2026-27" in name or "26/27" in name or "2026/27" in name

all_jerseys = []

for team_name, team_url in LA_LIGA_TEAMS:
    url = f"{BASE}{team_url}"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        soup = BeautifulSoup(r.text, "html.parser")
        
        imgs = soup.find_all("img", src=lambda s: s and CDN in s)
        
        team_jerseys = []
        for img in imgs:
            alt = img.get("alt", "").strip()
            if not alt:
                continue
            
            # Apply filters
            if not is_short_sleeve(alt):
                continue
            if not is_not_kids(alt):
                continue
            if not is_not_women(alt):
                continue
            if not has_season_26_27(alt):
                continue
            
            # Get image URL (strip query params for CDN base)
            src = img.get("src", "")
            
            team_jerseys.append({
                "team": team_name,
                "name": alt,
                "image": src
            })
        
        if team_jerseys:
            all_jerseys.extend(team_jerseys)
            print(f"  {team_name}: {len(team_jerseys)} jerseys")
        else:
            print(f"  {team_name}: No matching jerseys found")
        
        time.sleep(0.3)  # Rate limit
    
    except Exception as e:
        print(f"  {team_name}: Error - {e}")

# Save results
output_file = "la_liga_jerseys.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_jerseys, f, indent=2, ensure_ascii=False)

print(f"\nTotal La Liga jerseys found: {len(all_jerseys)}")
print(f"Saved to {output_file}")

# Show sample per team
for team in sorted(set(j["team"] for j in all_jerseys)):
    team_items = [j for j in all_jerseys if j["team"] == team]
    print(f"\n  {team} ({len(team_items)} jerseys):")
    for j in team_items[:5]:
        print(f"    - {j['name'][:80]}")
