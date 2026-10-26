import os

BASE_DIR = os.path.dirname(__file__)
files = [
    "generate_postmatch_debrief.py",
    "generate_match_briefing.py",
    "generate_player_cards.py",
    "generate_executive_report.py"
]

for fname in files:
    fpath = os.path.join(BASE_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        c = f.read()
    
    if 'page.set_content(html, wait_until="networkidle")' in c:
        c = c.replace('page.set_content(html, wait_until="networkidle")', 'page.set_content(html, wait_until="domcontentloaded")\n        page.wait_for_timeout(1200)')
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(c)
        print(f"Optimisé : {fname}")
    elif 'page.set_content(html_content, wait_until="networkidle")' in c:
        c = c.replace('page.set_content(html_content, wait_until="networkidle")', 'page.set_content(html_content, wait_until="domcontentloaded")\n        page.wait_for_timeout(1200)')
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(c)
        print(f"Optimisé : {fname}")
    else:
        print(f"Déjà optimisé ou pattern différent : {fname}")
