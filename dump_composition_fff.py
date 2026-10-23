import re
from playwright.sync_api import sync_playwright

args = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
with sync_playwright() as p:
    try:
        browser = p.chromium.launch(channel="chrome", headless=True, args=args)
    except:
        browser = p.chromium.launch(headless=True, args=args)
        
    page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    page.goto('https://epreuves.fff.fr/competition/match/56216904-ent-s-de-genech-et-c-anstaing-chereng', wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    try:
        page.locator('#didomi-notice-agree-button').click(timeout=1500)
    except: pass
    page.wait_for_timeout(1500)
    lines = [l.strip() for l in page.inner_text('body').split('\n') if l.strip()]
    
    comp_idx = -1
    for idx, l in enumerate(lines):
        if l == "COMPOSITION":
            comp_idx = idx
            break
            
    print(f"COMPOSITION trouvée à la ligne {comp_idx}")
    if comp_idx != -1:
        for idx, l in enumerate(lines[comp_idx:comp_idx+90]):
            print(f"[{idx}] {l}")
            
    browser.close()
